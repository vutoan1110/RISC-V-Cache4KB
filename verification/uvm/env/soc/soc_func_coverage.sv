// Functional coverage for the SoC environment: which peripheral pages and
// registers software actually touched, and in which direction.
class soc_apb_coverage extends uvm_subscriber #(apb_item);

    `uvm_component_utils(soc_apb_coverage)

    protected bit        cp_write;
    protected bit [7:0]  cp_page;
    protected bit [7:0]  cp_offset;
    protected bit [3:0]  cp_strb;

    covergroup cg_apb;
        option.per_instance = 1;
        option.name         = "soc_apb";

        direction: coverpoint cp_write {
            bins read  = {0};
            bins write = {1};
        }

        // hdl/bus/soc_address_decoder.v gives each peripheral a 256-byte page.
        page: coverpoint cp_page {
            bins uart    = {8'h00};
            bins display = {8'h01};
            bins timer   = {8'h02};
            bins sysmon  = {8'h03};
        }

        offset: coverpoint cp_offset {
            bins reg0 = {8'h00};
            bins reg4 = {8'h04};
            bins reg8 = {8'h08};
            bins regc = {8'h0C};
            bins reg10 = {8'h10};
            bins other = default;
        }

        page_x_dir: cross page, direction;
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_apb = new();
    endfunction

    function void write(apb_item t);
        cp_write  = t.write;
        cp_page   = t.addr[15:8];
        cp_offset = t.addr[7:0];
        cp_strb   = t.strb;
        cg_apb.sample();
    endfunction

endclass

// Interrupt and retirement context at SoC level.
class soc_retire_coverage extends uvm_subscriber #(soc_retire_item);

    `uvm_component_utils(soc_retire_coverage)

    protected bit [6:0] cp_opcode;
    protected bit       cp_interrupt;
    protected bit       cp_after_irq;
    protected bit       cp_mem_valid;

    covergroup cg_soc_retire;
        option.per_instance = 1;
        option.name         = "soc_retire";

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

        irq_flag: coverpoint cp_interrupt;
        redirect: coverpoint cp_after_irq;

        // Which instruction was retiring when an interrupt was accepted.
        opcode_x_irq: cross opcode, irq_flag {
            ignore_bins quiet = binsof(irq_flag) intersect {0};
        }
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_soc_retire = new();
    endfunction

    function void write(soc_retire_item t);
        cp_opcode    = t.instr[6:0];
        cp_interrupt = t.interrupt;
        cp_after_irq = (t.irq_pulses != 0);
        cp_mem_valid = t.mem_valid;
        cg_soc_retire.sample();
    endfunction

endclass
