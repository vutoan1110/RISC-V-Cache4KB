// UVM sources. Interfaces first, then the package, then the bind and the top.
+incdir+verification/uvm/env
+incdir+verification/uvm/env/axi
+incdir+verification/uvm/env/soc
+incdir+verification/uvm/seq
+incdir+verification/uvm/test

// Memory image, shared by both environments.
verification/uvm/env/mem_model_pkg.sv

// Core environment (phase 1-3), DUT riscv_core_native.
verification/uvm/intf/native_if.sv
verification/uvm/intf/rvfi_if.sv
verification/uvm/env/core_uvm_pkg.sv
verification/uvm/tb/core_bind.sv
verification/uvm/tb/tb_core_top.sv

// AXI environment (phase 4), DUT cache_axi_master.
verification/uvm/intf/refill_if.sv
verification/uvm/intf/wthru_if.sv
verification/uvm/intf/axi4_if.sv
verification/uvm/env/axi/axi_uvm_pkg.sv
verification/uvm/tb/tb_axi_top.sv

// SoC environment (phase 5), DUT soc_top.
verification/uvm/intf/soc_obs_if.sv
verification/uvm/intf/apb_if.sv
verification/uvm/intf/uart_if.sv
verification/uvm/env/soc/soc_uvm_pkg.sv
verification/uvm/tb/tb_soc_top.sv
