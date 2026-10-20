// Instruction-set reference model for the claimed subset: RV32I computational
// + Zmmul + the reduced machine CSR subset the core implements.
//
// It is a SystemVerilog port of verification/diff/rv32_reference.py, extended
// with the CSR subset so it can also run verification/directed/directed_isa.hex
// (the Python model rejects opcode 0x73). It is not Spike and is not an ISA
// compliance oracle; anything outside the claimed subset is reported as
// unsupported rather than guessed.
//
// The model owns its own memory image, loaded from the same hex as the DUT
// memory. Divergence therefore shows up both per instruction and, at end of
// test, as a memory image mismatch.

typedef struct {
    bit [31:0] pc;
    bit [31:0] instr;
    bit [31:0] next_pc;
    bit [4:0]  rd_addr;
    bit        rd_we;
    bit [31:0] rd_wdata;
    bit        rd_wdata_known;   // 0 for reads of mcycle/minstret
    bit        mem_valid;
    bit        mem_write;
    bit [31:0] mem_addr;
    bit [31:0] mem_wdata;
    bit [3:0]  mem_wstrb;
    bit        halted;
    bit        unsupported;
    string     reason;
} rv32_step_s;

class rv32_iss extends uvm_object;

    bit [31:0]       regs[32];
    bit [31:0]       pc;
    longint unsigned order;
    native_mem_model mem;
    bit [31:0]       halt_instr = 32'h0000_006f;

    // Reduced machine CSR subset, docs/reference/01 section 1.1. mcycle and
    // minstret are timing dependent, so the model does not track their value.
    bit [31:0] csr_mstatus;
    bit [31:0] csr_mie;
    bit [31:0] csr_mtvec;
    bit [31:0] csr_mepc;
    bit [31:0] csr_mcause;

    `uvm_object_utils(rv32_iss)

    function new(string name = "rv32_iss");
        super.new(name);
    endfunction

    function void reset();
        foreach (regs[i]) regs[i] = 32'h0;
        pc          = 32'h0;
        order       = 0;
        csr_mstatus = 32'h0;
        csr_mie     = 32'h0;
        csr_mtvec   = 32'h0000_0080;   // reset value in hdl/datapath.v
        csr_mepc    = 32'h0;
        csr_mcause  = 32'h0;
    endfunction

    // -----------------------------------------------------------------
    // Immediate decoding
    // -----------------------------------------------------------------
    protected function bit [31:0] imm_i(bit [31:0] instr);
        return {{20{instr[31]}}, instr[31:20]};
    endfunction

    protected function bit [31:0] imm_s(bit [31:0] instr);
        return {{20{instr[31]}}, instr[31:25], instr[11:7]};
    endfunction

    protected function bit [31:0] imm_b(bit [31:0] instr);
        return {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    endfunction

    protected function bit [31:0] imm_j(bit [31:0] instr);
        return {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};
    endfunction

    // -----------------------------------------------------------------
    // Memory helpers
    // -----------------------------------------------------------------
    protected function bit [31:0] load32(bit [31:0] addr);
        return {mem.read_byte(addr + 3), mem.read_byte(addr + 2),
                mem.read_byte(addr + 1), mem.read_byte(addr)};
    endfunction

    protected function bit [15:0] load16(bit [31:0] addr);
        return {mem.read_byte(addr + 1), mem.read_byte(addr)};
    endfunction

    // -----------------------------------------------------------------
    // CSR subset
    // -----------------------------------------------------------------
    protected function bit [31:0] csr_read(bit [11:0] addr);
        case (addr)
            12'h300: return csr_mstatus;
            12'h304: return csr_mie;
            12'h305: return csr_mtvec;
            12'h341: return csr_mepc;
            12'h342: return csr_mcause;
            default: return 32'h0;
        endcase
    endfunction

    protected function void csr_write(bit [11:0] addr, bit [31:0] value);
        case (addr)
            12'h300: csr_mstatus = value;
            12'h304: csr_mie     = value;
            12'h305: csr_mtvec   = value;
            12'h341: csr_mepc    = value;
            12'h342: csr_mcause  = value;
            default: ;   // mcycle/minstret are not modelled, see above
        endcase
    endfunction

    protected function bit csr_is_counter(bit [11:0] addr);
        return (addr == 12'hB00) || (addr == 12'hB02);
    endfunction

    protected function void clear_step(ref rv32_step_s s);
        s.pc             = 32'h0;
        s.instr          = 32'h0;
        s.next_pc        = 32'h0;
        s.rd_addr        = 5'd0;
        s.rd_we          = 1'b0;
        s.rd_wdata       = 32'h0;
        s.rd_wdata_known = 1'b1;
        s.mem_valid      = 1'b0;
        s.mem_write      = 1'b0;
        s.mem_addr       = 32'h0;
        s.mem_wdata      = 32'h0;
        s.mem_wstrb      = 4'h0;
        s.halted         = 1'b0;
        s.unsupported    = 1'b0;
        s.reason         = "";
    endfunction

    // -----------------------------------------------------------------
    // One retirement
    // -----------------------------------------------------------------
    function rv32_step_s step();
        rv32_step_s s;
        bit [31:0]  instr;
        bit [6:0]   opcode;
        bit [2:0]   funct3;
        bit [6:0]   funct7;
        bit [4:0]   rs1;
        bit [4:0]   rs2;
        bit [31:0]  a;
        bit [31:0]  b;
        bit [4:0]   shamt;
        bit [31:0]  target;
        bit         taken;
        bit [11:0]  csr_addr;
        bit [31:0]  csr_old;
        bit [31:0]  csr_new;
        int signed       sa;
        bit [7:0]        byte_val;
        bit [15:0]       half_val;
        longint signed   sprod;
        longint unsigned uprod;

        clear_step(s);
        s.pc = pc;

        if (!mem.is_backed(pc)) begin
            s.unsupported = 1'b1;
            s.reason = $sformatf("pc 0x%08h escaped the program image", pc);
            return s;
        end

        instr    = mem.read_word(pc);
        s.instr  = instr;
        s.next_pc = pc + 32'd4;

        if (instr == halt_instr) begin
            s.halted = 1'b1;
            return s;
        end

        opcode = instr[6:0];
        funct3 = instr[14:12];
        funct7 = instr[31:25];
        rs1    = instr[19:15];
        rs2    = instr[24:20];
        a      = regs[rs1];
        b      = regs[rs2];
        s.rd_addr = instr[11:7];

        case (opcode)
            // ---------------------------------------------------- R type
            7'b0110011: begin
                s.rd_we = 1'b1;
                shamt   = b[4:0];
                if (funct7 == 7'b0000001) begin
                    case (funct3)
                        3'b000: begin
                            sprod = longint'(signed'(a)) * longint'(signed'(b));
                            s.rd_wdata = sprod[31:0];
                        end
                        3'b001: begin
                            sprod = longint'(signed'(a)) * longint'(signed'(b));
                            s.rd_wdata = sprod[63:32];
                        end
                        3'b010: begin   // MULHSU
                            sprod = longint'(signed'(a)) * longint'({32'd0, b});
                            s.rd_wdata = sprod[63:32];
                        end
                        3'b011: begin   // MULHU
                            uprod = longint'({32'd0, a}) * longint'({32'd0, b});
                            s.rd_wdata = uprod[63:32];
                        end
                        default: begin
                            s.unsupported = 1'b1;
                            s.reason = $sformatf("M extension funct3 %0d is outside Zmmul", funct3);
                        end
                    endcase
                end
                else begin
                    case (funct3)
                        3'b000: s.rd_wdata = (funct7 == 7'b0100000) ? (a - b) : (a + b);
                        3'b001: s.rd_wdata = a << shamt;
                        3'b010: s.rd_wdata = {31'd0, signed'(a) < signed'(b)};
                        3'b011: s.rd_wdata = {31'd0, a < b};
                        3'b100: s.rd_wdata = a ^ b;
                        // Kept out of a ternary on purpose: mixing a signed
                        // and an unsigned arm makes the whole expression
                        // unsigned and turns >>> into a logical shift.
                        3'b101: begin
                            if (funct7 == 7'b0100000) begin
                                sa = signed'(a);
                                s.rd_wdata = sa >>> shamt;
                            end
                            else
                                s.rd_wdata = a >> shamt;
                        end
                        3'b110: s.rd_wdata = a | b;
                        default: s.rd_wdata = a & b;
                    endcase
                end
            end

            // ---------------------------------------------------- I type
            7'b0010011: begin
                s.rd_we = 1'b1;
                shamt   = instr[24:20];
                case (funct3)
                    3'b000: s.rd_wdata = a + imm_i(instr);
                    3'b001: s.rd_wdata = a << shamt;
                    3'b010: s.rd_wdata = {31'd0, signed'(a) < signed'(imm_i(instr))};
                    3'b011: s.rd_wdata = {31'd0, a < imm_i(instr)};
                    3'b100: s.rd_wdata = a ^ imm_i(instr);
                    3'b101: begin
                        if (funct7 == 7'b0100000) begin
                            sa = signed'(a);
                            s.rd_wdata = sa >>> shamt;
                        end
                        else
                            s.rd_wdata = a >> shamt;
                    end
                    3'b110: s.rd_wdata = a | imm_i(instr);
                    default: s.rd_wdata = a & imm_i(instr);
                endcase
            end

            // ---------------------------------------------------- loads
            7'b0000011: begin
                s.rd_we     = 1'b1;
                s.mem_valid = 1'b1;
                s.mem_addr  = a + imm_i(instr);
                byte_val = mem.read_byte(s.mem_addr);
                half_val = load16(s.mem_addr);
                case (funct3)
                    3'b000: s.rd_wdata = {{24{byte_val[7]}}, byte_val};
                    3'b100: s.rd_wdata = {24'd0, byte_val};
                    3'b001, 3'b101: begin
                        if (s.mem_addr[0] != 1'b0) begin
                            s.unsupported = 1'b1;
                            s.reason = $sformatf("misaligned halfword load at 0x%08h", s.mem_addr);
                        end
                        else if (funct3 == 3'b001)
                            s.rd_wdata = {{16{half_val[15]}}, half_val};
                        else
                            s.rd_wdata = {16'd0, half_val};
                    end
                    3'b010: begin
                        if (s.mem_addr[1:0] != 2'b00) begin
                            s.unsupported = 1'b1;
                            s.reason = $sformatf("misaligned word load at 0x%08h", s.mem_addr);
                        end
                        else
                            s.rd_wdata = load32(s.mem_addr);
                    end
                    default: begin
                        s.unsupported = 1'b1;
                        s.reason = $sformatf("load funct3 %0d is not in RV32I", funct3);
                    end
                endcase
            end

            // --------------------------------------------------- stores
            7'b0100011: begin
                s.mem_valid = 1'b1;
                s.mem_write = 1'b1;
                s.mem_addr  = a + imm_s(instr);
                // Lane placement matches riscv_core_native, which shifts the
                // payload and the strobe by mem_addr[1:0].
                case (funct3)
                    3'b000: begin
                        s.mem_wstrb = 4'b0001 << s.mem_addr[1:0];
                        s.mem_wdata = {24'd0, b[7:0]} << (8 * s.mem_addr[1:0]);
                    end
                    3'b001: begin
                        if (s.mem_addr[0] != 1'b0) begin
                            s.unsupported = 1'b1;
                            s.reason = $sformatf("misaligned halfword store at 0x%08h", s.mem_addr);
                        end
                        else begin
                            s.mem_wstrb = 4'b0011 << s.mem_addr[1:0];
                            s.mem_wdata = {16'd0, b[15:0]} << (8 * s.mem_addr[1:0]);
                        end
                    end
                    3'b010: begin
                        if (s.mem_addr[1:0] != 2'b00) begin
                            s.unsupported = 1'b1;
                            s.reason = $sformatf("misaligned word store at 0x%08h", s.mem_addr);
                        end
                        else begin
                            s.mem_wstrb = 4'b1111;
                            s.mem_wdata = b;
                        end
                    end
                    default: begin
                        s.unsupported = 1'b1;
                        s.reason = $sformatf("store funct3 %0d is not in RV32I", funct3);
                    end
                endcase
            end

            // ------------------------------------------------- branches
            7'b1100011: begin
                case (funct3)
                    3'b000: taken = (a == b);
                    3'b001: taken = (a != b);
                    3'b100: taken = (signed'(a) <  signed'(b));
                    3'b101: taken = (signed'(a) >= signed'(b));
                    3'b110: taken = (a <  b);
                    3'b111: taken = (a >= b);
                    default: begin
                        taken = 1'b0;
                        s.unsupported = 1'b1;
                        s.reason = $sformatf("branch funct3 %0d is not in RV32I", funct3);
                    end
                endcase
                if (taken)
                    s.next_pc = pc + imm_b(instr);
            end

            // ------------------------------------------------------ JAL
            7'b1101111: begin
                s.rd_we    = 1'b1;
                s.rd_wdata = pc + 32'd4;
                s.next_pc  = pc + imm_j(instr);
            end

            // ----------------------------------------------------- JALR
            7'b1100111: begin
                s.rd_we    = 1'b1;
                s.rd_wdata = pc + 32'd4;
                s.next_pc  = (a + imm_i(instr)) & ~32'd1;
            end

            // ------------------------------------------------------ LUI
            7'b0110111: begin
                s.rd_we    = 1'b1;
                s.rd_wdata = {instr[31:12], 12'd0};
            end

            // ---------------------------------------------------- AUIPC
            7'b0010111: begin
                s.rd_we    = 1'b1;
                s.rd_wdata = pc + {instr[31:12], 12'd0};
            end

            // ---------------------------------------------------- FENCE
            7'b0001111: ;   // no-op in this single-hart harness

            // ------------------------------------------------------ CSR
            7'b1110011: begin
                csr_addr = instr[31:20];
                if (instr == 32'h3020_0073) begin
                    s.unsupported = 1'b1;
                    s.reason = "MRET is outside the verified subset";
                end
                else if (funct3 inside {3'b001, 3'b010, 3'b011}) begin
                    csr_old    = csr_read(csr_addr);
                    s.rd_we    = 1'b1;
                    s.rd_wdata = csr_old;
                    // mcycle and minstret are free running, so their read value
                    // cannot be predicted; the write side is not modelled.
                    if (csr_is_counter(csr_addr))
                        s.rd_wdata_known = 1'b0;
                    else begin
                        case (funct3)
                            3'b001:  csr_new = a;
                            3'b010:  csr_new = csr_old | a;
                            default: csr_new = csr_old & ~a;
                        endcase
                        // The RTL commits the write for every register form,
                        // including rs1 == x0. See docs/reference/02 section 9.1.
                        csr_write(csr_addr, csr_new);
                    end
                end
                else begin
                    s.unsupported = 1'b1;
                    s.reason = $sformatf("CSR funct3 %0d (immediate form, ECALL/EBREAK) is outside the verified subset",
                                         funct3);
                end
            end

            default: begin
                s.unsupported = 1'b1;
                s.reason = $sformatf("opcode 0x%02h is outside the verified subset", opcode);
            end
        endcase

        if (s.unsupported)
            return s;

        // Commit. rd == x0 discards the write, exactly like retire_rd_we.
        if (s.rd_we && (s.rd_addr != 5'd0))
            regs[s.rd_addr] = s.rd_wdata;
        else begin
            s.rd_we    = 1'b0;
            s.rd_wdata = 32'h0;
        end
        regs[0] = 32'h0;

        if (s.mem_write) begin
            for (int lane = 0; lane < 4; lane++)
                if (s.mem_wstrb[lane])
                    mem.write_byte({s.mem_addr[31:2], 2'b00} + lane,
                                   s.mem_wdata[8*lane +: 8]);
        end

        pc = s.next_pc;
        order++;
        return s;
    endfunction

    // mcycle and minstret are free running, so the model has to take the value
    // the DUT produced; otherwise every later instruction that consumes the
    // result diverges for a reason that is not a bug.
    function void adopt_rd(bit [4:0] rd_addr, bit [31:0] value);
        if (rd_addr != 5'd0)
            regs[rd_addr] = value;
    endfunction

    function string convert2string();
        return $sformatf("iss pc=0x%08h order=%0d", pc, order);
    endfunction

endclass
