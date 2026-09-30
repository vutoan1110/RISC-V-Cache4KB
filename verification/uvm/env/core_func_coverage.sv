// Functional coverage for the core environment.
//
// verification/coverage/core_coverage.sv stays in place and keeps reporting its
// procedural bins; this adds real covergroups on top, so Questa can merge a
// UCDB across tests and seeds and report a coverage percentage.

class core_retire_coverage extends uvm_subscriber #(rvfi_item);

    `uvm_component_utils(core_retire_coverage)

    protected bit [6:0]  cp_opcode;
    protected bit [2:0]  cp_funct3;
    protected bit [6:0]  cp_funct7;
    protected bit        cp_rd_we;
    protected bit [4:0]  cp_rd;
    protected bit        cp_mem_valid;
    protected bit        cp_mem_write;
    protected bit [1:0]  cp_mem_align;
    protected bit [3:0]  cp_wstrb;

    covergroup cg_retire;
        option.per_instance = 1;
        option.name         = "core_retire";

        opcode: coverpoint cp_opcode {
            bins alu_r  = {7'b0110011};
            bins alu_i  = {7'b0010011};
            bins load   = {7'b0000011};
            bins store  = {7'b0100011};
            bins branch = {7'b1100011};
            bins jal    = {7'b1101111};
            bins jalr   = {7'b1100111};
            bins lui    = {7'b0110111};
            bins auipc  = {7'b0010111};
            bins csr    = {7'b1110011};
            bins fence  = {7'b0001111};
        }

        funct3: coverpoint cp_funct3;

        // funct7 = 0000001 is Zmmul, 0100000 is SUB/SRA.
        alu_variant: coverpoint cp_funct7 {
            bins base = {7'b0000000};
            bins alt  = {7'b0100000};
            bins mul  = {7'b0000001};
        }

        writes_rd: coverpoint cp_rd_we;

        rd_reg: coverpoint cp_rd {
            bins x0        = {0};
            bins low[8]    = {[1:15]};
            bins high[8]   = {[16:31]};
        }

        mem_kind: coverpoint {cp_mem_valid, cp_mem_write} {
            bins none  = {2'b00};
            bins load  = {2'b10};
            bins store = {2'b11};
            ignore_bins impossible = {2'b01};
        }

        mem_align: coverpoint cp_mem_align iff (cp_mem_valid);

        store_strobe: coverpoint cp_wstrb iff (cp_mem_write) {
            bins byte_lane[4] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
            bins half_lane[2] = {4'b0011, 4'b1100};
            bins word         = {4'b1111};
        }

        // Which widths actually land on which alignment.
        kind_x_align: cross mem_kind, mem_align;
        // Which ALU variants appear for which funct3.
        alu_x_funct3: cross alu_variant, funct3 {
            ignore_bins non_alu = binsof(alu_variant.mul) && binsof(funct3) intersect {[4:7]};
        }
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_retire = new();
    endfunction

    function void write(rvfi_item t);
        cp_opcode    = t.instr[6:0];
        cp_funct3    = t.instr[14:12];
        cp_funct7    = t.instr[31:25];
        cp_rd_we     = t.rd_we;
        cp_rd        = t.rd_addr;
        cp_mem_valid = t.mem_valid;
        cp_mem_write = t.mem_write;
        cp_mem_align = t.mem_addr[1:0];
        cp_wstrb     = t.mem_wstrb;
        cg_retire.sample();
    endfunction

endclass

// Coverage of the data port itself: which regions the core reaches and how the
// handshake behaves.
class core_dmem_coverage extends uvm_subscriber #(native_mem_item);

    `uvm_component_utils(core_dmem_coverage)

    protected bit             cp_write;
    protected native_region_e cp_region;
    protected bit [3:0]       cp_wstrb;

    covergroup cg_dport;
        option.per_instance = 1;
        option.name         = "core_data_port";

        direction: coverpoint cp_write {
            bins read  = {0};
            bins write = {1};
        }

        region: coverpoint cp_region {
            bins ram      = {REGION_RAM};
            bins mmio     = {REGION_MMIO};
            bins unmapped = {REGION_UNMAPPED};
        }

        strobe: coverpoint cp_wstrb iff (cp_write) {
            bins byte_lane[4] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
            bins half_lane[2] = {4'b0011, 4'b1100};
            bins word         = {4'b1111};
        }

        dir_x_region: cross direction, region;
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_dport = new();
    endfunction

    function void write(native_mem_item t);
        if (t.evt != NATIVE_ACCEPT)
            return;
        cp_write  = t.is_write;
        cp_region = native_mem_model::decode(t.addr);
        cp_wstrb  = t.wstrb;
        cg_dport.sample();
    endfunction

endclass
