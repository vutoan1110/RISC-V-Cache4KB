// One retirement record sampled from the RVFI-style port.
class rvfi_item extends uvm_sequence_item;

    bit [63:0] order;
    bit [31:0] pc;
    bit [31:0] pc_next;
    bit [31:0] instr;
    bit [4:0]  rs1_addr;
    bit [31:0] rs1_rdata;
    bit [4:0]  rs2_addr;
    bit [31:0] rs2_rdata;
    bit [4:0]  rd_addr;
    bit [31:0] rd_wdata;
    bit        rd_we;
    bit        mem_valid;
    bit        mem_write;
    bit [31:0] mem_addr;
    bit [31:0] mem_wdata;
    bit [3:0]  mem_wstrb;
    bit        trap;
    bit        interrupt;

    `uvm_object_utils_begin(rvfi_item)
        `uvm_field_int(order,    UVM_ALL_ON | UVM_DEC)
        `uvm_field_int(pc,       UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(pc_next,  UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(instr,    UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(rd_addr,  UVM_ALL_ON | UVM_DEC)
        `uvm_field_int(rd_wdata, UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(rd_we,    UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "rvfi_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("order=%0d pc=%08h instr=%08h rd=x%0d we=%0b data=%08h mem=%0b/%0b addr=%08h",
                         order, pc, instr, rd_addr, rd_we, rd_wdata,
                         mem_valid, mem_write, mem_addr);
    endfunction

endclass
