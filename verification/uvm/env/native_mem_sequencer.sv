// Present so reactive stimulus (error injection, backpressure profiles) can be
// driven from sequences in phase 3. The milestone-1 responder serves requests
// straight from the memory model and does not pull items.
class native_mem_sequencer extends uvm_sequencer #(native_mem_item);
    `uvm_component_utils(native_mem_sequencer)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass
