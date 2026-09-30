// Constrained-random program generator for the claimed subset.
//
// Termination is structural, not statistical: every branch, JAL and JALR the
// generator emits targets a fixed short forward distance, so the PC only ever
// moves forward and the program always reaches the trailing HALT. Data
// accesses are all relative to x30, which is initialised to the data base, so
// they cannot escape into the code or outside RAM.
//
// This mirrors verification/random/gen_rv32.py, the generator the retained
// 50/50-seed random differential record was produced with, so a UVM run and a
// Python run explore the same shape of program.
class rv32_program_gen extends uvm_object;

    localparam bit [31:0] HALT = 32'h0000_006f;   // JAL x0,0
    localparam bit [31:0] NOP  = 32'h0000_0013;

    // x30 holds the data base, x27/x28 are JAL/JALR scaffolding.
    localparam bit [4:0] REG_DATA_BASE = 5'd30;
    localparam bit [4:0] REG_LINK      = 5'd27;
    localparam bit [4:0] REG_SCRATCH   = 5'd28;

    int unsigned length     = 160;    // instruction words before HALT
    int unsigned data_base  = 32'h400;
    int unsigned data_bytes = 256;

    bit [31:0] words[$];

    `uvm_object_utils(rv32_program_gen)

    function new(string name = "rv32_program_gen");
        super.new(name);
    endfunction

    // ------------------------------------------------------------------
    // Encoders
    // ------------------------------------------------------------------
    static function bit [31:0] enc_r(bit [6:0] f7, bit [4:0] rs2, bit [4:0] rs1,
                                     bit [2:0] f3, bit [4:0] rd);
        return {f7, rs2, rs1, f3, rd, 7'b0110011};
    endfunction

    static function bit [31:0] enc_i(bit [11:0] imm, bit [4:0] rs1, bit [2:0] f3,
                                     bit [4:0] rd, bit [6:0] opcode = 7'b0010011);
        return {imm, rs1, f3, rd, opcode};
    endfunction

    static function bit [31:0] enc_s(bit [11:0] imm, bit [4:0] rs2, bit [4:0] rs1,
                                     bit [2:0] f3);
        return {imm[11:5], rs2, rs1, f3, imm[4:0], 7'b0100011};
    endfunction

    static function bit [31:0] enc_b(bit [12:0] off, bit [4:0] rs2, bit [4:0] rs1,
                                     bit [2:0] f3);
        return {off[12], off[10:5], rs2, rs1, f3, off[4:1], off[11], 7'b1100011};
    endfunction

    static function bit [31:0] enc_u(bit [19:0] imm20, bit [4:0] rd, bit [6:0] opcode);
        return {imm20, rd, opcode};
    endfunction

    static function bit [31:0] enc_j(bit [20:0] off, bit [4:0] rd);
        return {off[20], off[10:1], off[11], off[19:12], rd, 7'b1101111};
    endfunction

    // ------------------------------------------------------------------
    // Program body
    // ------------------------------------------------------------------
    function void generate_program();
        rv32_instr_item item;
        int unsigned    remaining;

        words.delete();

        // x30 = data base, then seed x1..x10 with small values so the first
        // comparisons and shifts are not all zero.
        words.push_back(enc_i(data_base[11:0], 5'd0, 3'b000, REG_DATA_BASE));
        for (int r = 1; r <= 10; r++)
            words.push_back(enc_i($urandom_range(2047, 0), 5'd0, 3'b000, r[4:0]));

        item = rv32_instr_item::type_id::create("item");

        while (words.size() < length) begin
            remaining = length - words.size();

            item.data_bytes   = data_bytes;
            item.allow_branch = (remaining >= 2);
            item.allow_jal    = (remaining >= 2);
            item.allow_jalr   = (remaining >= 4);

            if (!item.randomize())
                `uvm_fatal("GENRAND", "rv32_instr_item randomization failed")

            emit(item);
        end

        // Trim any tail the multi-word forms pushed past the target length,
        // then stop the program.
        while (words.size() > length)
            void'(words.pop_back());
        words.push_back(HALT);
    endfunction

    protected function void emit(rv32_instr_item item);
        bit [6:0]  f7;
        bit [11:0] imm;

        case (item.kind)
            rv32_instr_item::KIND_R: begin
                f7 = item.alt ? 7'b0100000 : 7'b0000000;
                words.push_back(enc_r(f7, item.rs2, item.rs1, item.funct3, item.rd));
            end

            rv32_instr_item::KIND_MUL:
                words.push_back(enc_r(7'b0000001, item.rs2, item.rs1,
                                      item.funct3, item.rd));

            rv32_instr_item::KIND_I: begin
                // Shift-immediate encodings carry the shift amount and, for
                // SRAI, funct7 in the immediate field.
                if (item.funct3 == 3'b001)
                    imm = {7'b0000000, item.shamt};
                else if (item.funct3 == 3'b101)
                    imm = {item.alt ? 7'b0100000 : 7'b0000000, item.shamt};
                else
                    imm = item.imm;
                words.push_back(enc_i(imm, item.rs1, item.funct3, item.rd));
            end

            rv32_instr_item::KIND_LOAD:
                words.push_back(enc_i({3'b000, item.data_off}, REG_DATA_BASE,
                                      item.funct3, item.rd, 7'b0000011));

            rv32_instr_item::KIND_STORE:
                words.push_back(enc_s({3'b000, item.data_off}, item.rs2,
                                      REG_DATA_BASE, item.funct3));

            // Forward branch over one instruction; both outcomes are legal and
            // the PC advances either way.
            rv32_instr_item::KIND_BRANCH: begin
                words.push_back(enc_b(13'd8, item.rs2, item.rs1, item.funct3));
                words.push_back(enc_i(item.imm, item.rd, 3'b000, item.rd));
            end

            rv32_instr_item::KIND_JAL: begin
                words.push_back(enc_j(21'd8, REG_LINK));
                words.push_back(enc_i(item.imm, item.rd, 3'b000, item.rd));
            end

            // AUIPC/ADDI build a target four instructions ahead, so the JALR
            // lands on the instruction right after this block.
            rv32_instr_item::KIND_JALR: begin
                words.push_back(enc_u(20'd0, REG_SCRATCH, 7'b0010111));
                words.push_back(enc_i(12'd16, REG_SCRATCH, 3'b000, REG_SCRATCH));
                words.push_back(enc_i(12'd0, REG_SCRATCH, 3'b000, REG_LINK, 7'b1100111));
                words.push_back(enc_i(item.imm, item.rd, 3'b000, item.rd));
            end

            rv32_instr_item::KIND_UPPER:
                words.push_back(enc_u(item.uimm, item.rd,
                                      item.upper_is_auipc ? 7'b0010111 : 7'b0110111));

            default: words.push_back(NOP);
        endcase
    endfunction

    // ------------------------------------------------------------------
    // Output
    // ------------------------------------------------------------------
    function void write_to(native_mem_model mem);
        foreach (words[i])
            mem.write_word(i << 2, words[i], 4'b1111);
    endfunction

    // A copy of the image on disk makes a failing seed reproducible with the
    // existing Python tools.
    function void dump_hex(string path);
        int fd = $fopen(path, "w");
        if (fd == 0) begin
            `uvm_warning("GENDUMP", $sformatf("cannot write program image to %s", path))
            return;
        end
        foreach (words[i])
            $fdisplay(fd, "%08h", words[i]);
        $fclose(fd);
        `uvm_info("GENDUMP", $sformatf("wrote %0d words to %s", words.size(), path),
                  UVM_LOW)
    endfunction

    // The data window has to start past the last instruction, otherwise a
    // store would rewrite code the core has not fetched yet.
    function bit code_and_data_disjoint();
        return (words.size() * 4) <= data_base;
    endfunction

endclass
