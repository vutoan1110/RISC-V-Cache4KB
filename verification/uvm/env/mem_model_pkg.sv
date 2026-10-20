`timescale 1ns/1ps

// The memory image is shared by the core environment and the AXI environment,
// and it references no virtual interface. Keeping it in its own package means
// a testbench can use it without pulling in the interfaces of the other
// environment, which Questa would then fail to resolve.
package mem_model_pkg;

    import uvm_pkg::*;
`include "uvm_macros.svh"

`include "native_mem_model.sv"

endpackage
