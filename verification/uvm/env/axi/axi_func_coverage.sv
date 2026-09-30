// Functional coverage for the cache_axi_master environment: burst shape, which
// initiator won the arbiter, and how the write path overlapped the read path.
class axi_bus_coverage extends uvm_subscriber #(axi_item);

    `uvm_component_utils(axi_bus_coverage)

    protected axi_kind_e cp_kind;
    protected bit [7:0]  cp_len;
    protected bit [2:0]  cp_size;
    protected bit [1:0]  cp_burst;
    protected bit [3:0]  cp_strb;
    protected bit [1:0]  cp_resp;
    protected bit [3:0]  cp_addr_lo;

    covergroup cg_axi;
        option.per_instance = 1;
        option.name         = "axi_bus";

        kind: coverpoint cp_kind {
            bins read  = {AXI_READ_BURST};
            bins write = {AXI_WRITE};
        }

        len: coverpoint cp_len {
            // A write is a single beat; a refill is LINE_WORDS beats, which the
            // design supports from two to sixteen. Binning only arlen=3 made
            // every other legal line size an illegal bin.
            bins single   = {8'd0};
            // One bin per supported refill length, grouped under a single name
            // so the cross below can refer to all of them at once.
            bins refill[] = {8'd1, 8'd3, 8'd7, 8'd15};
            illegal_bins other = default;
        }

        size: coverpoint cp_size {
            bins word = {3'd2};
            illegal_bins other = default;
        }

        burst: coverpoint cp_burst {
            bins fixed = {2'b00};
            bins incr  = {2'b01};
            illegal_bins other = default;
        }

        resp: coverpoint cp_resp {
            bins okay = {2'b00};
            bins error[] = {2'b10, 2'b11};
        }

        // Reads are line aligned, writes are word aligned anywhere in the line.
        addr_lo: coverpoint cp_addr_lo {
            bins aligned16 = {4'h0};
            bins word4     = {4'h4};
            bins word8     = {4'h8};
            bins wordc     = {4'hC};
        }

        strobe: coverpoint cp_strb iff (cp_kind == AXI_WRITE) {
            bins byte_lane[4] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
            bins half_lane[2] = {4'b0011, 4'b1100};
            bins word         = {4'b1111};
        }

        kind_x_len: cross kind, len {
            ignore_bins read_single  = binsof(kind.read)  && binsof(len.single);
            ignore_bins write_refill = binsof(kind.write) && binsof(len.refill);
        }
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_axi = new();
    endfunction

    function void write(axi_item t);
        cp_kind    = t.kind;
        cp_len     = t.len;
        cp_size    = t.size;
        cp_burst   = t.burst;
        cp_strb    = t.strb;
        cp_resp    = t.resp;
        cp_addr_lo = t.addr[3:0];
        cg_axi.sample();
    endfunction

endclass

// Which native initiator produced traffic, and how long the refill took.
class axi_refill_coverage extends uvm_subscriber #(refill_item);

    `uvm_component_utils(axi_refill_coverage)

    protected bit          cp_icache;
    protected int unsigned cp_latency;

    covergroup cg_refill;
        option.per_instance = 1;
        option.name         = "axi_refill";

        source: coverpoint cp_icache {
            bins dcache = {0};
            bins icache = {1};
        }

        // A refill is at least four beats; the tail bins show backpressure.
        latency: coverpoint cp_latency {
            bins fast   = {[0:9]};
            bins mid    = {[10:29]};
            bins slow   = {[30:99]};
            bins stalled = {[100:$]};
        }

        source_x_latency: cross source, latency;
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_refill = new();
    endfunction

    function void write(refill_item t);
        cp_icache  = t.is_icache;
        cp_latency = int'(t.done_cycle - t.accept_cycle);
        cg_refill.sample();
    endfunction

endclass
