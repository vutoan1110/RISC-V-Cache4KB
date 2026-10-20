// One observed event on a native port. The monitor publishes an ACCEPT item
// when req_valid && req_ready and a RESPONSE item when rsp_valid pulses.
typedef enum bit [1:0] {
    NATIVE_ACCEPT,
    NATIVE_RESPONSE
} native_evt_e;

class native_mem_item extends uvm_sequence_item;

    rand native_evt_e evt;
    rand bit          is_write;
    rand bit [31:0]   addr;
    rand bit [31:0]   wdata;
    rand bit [3:0]    wstrb;
    bit [31:0]        rdata;
    bit               error;
    longint unsigned  cycle;

    `uvm_object_utils_begin(native_mem_item)
        `uvm_field_enum(native_evt_e, evt, UVM_ALL_ON)
        `uvm_field_int(is_write, UVM_ALL_ON)
        `uvm_field_int(addr,     UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(wdata,    UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(wstrb,    UVM_ALL_ON | UVM_BIN)
        `uvm_field_int(rdata,    UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(error,    UVM_ALL_ON)
        `uvm_field_int(cycle,    UVM_ALL_ON | UVM_DEC)
    `uvm_object_utils_end

    function new(string name = "native_mem_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("%s %s addr=%08h wdata=%08h wstrb=%4b rdata=%08h err=%0b @cyc %0d",
                         evt.name(), is_write ? "WR" : "RD",
                         addr, wdata, wstrb, rdata, error, cycle);
    endfunction

endclass
