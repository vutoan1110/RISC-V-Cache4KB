// Responder for one native port. It behaves like the registered memory model
// in tb/native_interface_tb.sv: a request accepted on edge N is answered with
// a one-cycle rsp_valid pulse on edge N+latency, and req_ready drops while a
// request is in flight so only one transaction is ever outstanding.
class native_mem_driver extends uvm_driver #(native_mem_item);

    virtual native_if vif;
    core_cfg          cfg;
    bit               allow_write = 1;   // instruction port forces reads
    string            port_name   = "d";

    `uvm_component_utils(native_mem_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for native_mem_driver")
    endfunction

    protected function int unsigned pick_latency();
        int unsigned lo = (cfg.rsp_latency_min < 1) ? 1 : cfg.rsp_latency_min;
        int unsigned hi = (cfg.rsp_latency_max < lo) ? lo : cfg.rsp_latency_max;
        return (hi == lo) ? lo : ($urandom_range(hi, lo));
    endfunction

    // Serve one accepted request out of the shared memory image.
    protected function void access(bit is_write, bit [31:0] addr,
                                   bit [31:0] wdata, bit [3:0] wstrb,
                                   output bit [31:0] rdata, output bit error);
        native_region_e region = native_mem_model::decode(addr);
        rdata = 32'h0;
        error = 1'b0;
        case (region)
            REGION_RAM: begin
                if (!cfg.mem.is_backed(addr)) begin
                    // Cacheable window is 64 KiB but physical RAM is smaller.
                    error = 1'b1;
                    `uvm_error("MEMRANGE",
                        $sformatf("%s port access to 0x%08h is past the %0d-byte RAM model",
                                  port_name, addr, cfg.mem.size_bytes))
                end
                else if (is_write)
                    cfg.mem.write_word(addr, wdata, wstrb);
                else
                    rdata = cfg.mem.read_word(addr);
            end
            REGION_MMIO: begin
                // Strongly ordered APB page: reads return 0, writes are sunk.
                `uvm_info("MMIO",
                    $sformatf("%s port %s to APB page 0x%08h", port_name,
                              is_write ? "write" : "read", addr), UVM_HIGH)
            end
            default: begin
                error = 1'b1;
                `uvm_info("UNMAPPED",
                    $sformatf("%s port access to unmapped 0x%08h answered with rsp_error",
                              port_name, addr), UVM_MEDIUM)
            end
        endcase
    endfunction

    protected task drive_idle(ref bit cur_ready);
        cur_ready = 1'b1;
        vif.rsp_cb.req_ready <= 1'b1;
        vif.rsp_cb.rsp_valid <= 1'b0;
        vif.rsp_cb.rsp_rdata <= 32'h0;
        vif.rsp_cb.rsp_error <= 1'b0;
    endtask

    task run_phase(uvm_phase phase);
        bit          pend;
        bit          p_write;
        bit [31:0]   p_addr;
        bit [31:0]   p_wdata;
        bit [3:0]    p_wstrb;
        int unsigned cnt;
        bit          cur_ready;
        bit          nxt_valid;
        bit [31:0]   nxt_rdata;
        bit          nxt_error;

        pend      = 1'b0;
        cnt       = 0;
        cur_ready = 1'b0;
        vif.rsp_cb.req_ready <= 1'b0;
        vif.rsp_cb.rsp_valid <= 1'b0;
        vif.rsp_cb.rsp_rdata <= 32'h0;
        vif.rsp_cb.rsp_error <= 1'b0;

        forever begin
            @(vif.rsp_cb);

            if (!vif.reset_n) begin
                pend = 1'b0;
                cnt  = 0;
                drive_idle(cur_ready);
                continue;
            end

            nxt_valid = 1'b0;
            nxt_rdata = 32'h0;
            nxt_error = 1'b0;

            if (vif.rsp_cb.req_valid && cur_ready) begin
                pend    = 1'b1;
                p_write = allow_write ? vif.rsp_cb.req_write : 1'b0;
                p_addr  = vif.rsp_cb.req_addr;
                p_wdata = vif.rsp_cb.req_wdata;
                p_wstrb = vif.rsp_cb.req_wstrb;
                cnt     = pick_latency();
            end

            if (pend) begin
                if (cnt <= 1) begin
                    access(p_write, p_addr, p_wdata, p_wstrb, nxt_rdata, nxt_error);
                    nxt_valid = 1'b1;
                    pend      = 1'b0;
                end
                else begin
                    cnt = cnt - 1;
                end
            end

            // req_ready driven now is what the core samples on the next edge.
            cur_ready = !pend;
            vif.rsp_cb.req_ready <= cur_ready;
            vif.rsp_cb.rsp_valid <= nxt_valid;
            vif.rsp_cb.rsp_rdata <= nxt_rdata;
            vif.rsp_cb.rsp_error <= nxt_error;
        end
    endtask

endclass
