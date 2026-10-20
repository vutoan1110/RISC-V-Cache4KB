// Checks for the cache_axi_master environment.
//
//   - burst shape: reads are one 4-beat 32-bit INCR burst, writes a single beat;
//   - one AXI transaction outstanding at a time (checked in axi_monitor);
//   - refill data equals the memory content at the refill address;
//   - every write-through request reaches AXI once, in order, unchanged;
//   - the posted-write buffer answers before the AXI B response.
class axi_scoreboard extends uvm_scoreboard;

    uvm_analysis_imp_refill #(refill_item, axi_scoreboard) refill_export;
    uvm_analysis_imp_wthru  #(wthru_item,  axi_scoreboard) wthru_export;
    uvm_analysis_imp_axi    #(axi_item,    axi_scoreboard) axi_export;

    axi_cfg cfg;

    // Write-through requests that have been answered but whose AXI write has
    // not been seen yet. The buffer drains in order.
    protected wthru_item wr_drain_q[$];

    `uvm_component_utils(axi_scoreboard)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        refill_export = new("refill_export", this);
        wthru_export  = new("wthru_export", this);
        axi_export    = new("axi_export", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for axi_scoreboard")
    endfunction

    function void write_refill(refill_item item);
        bit [31:0] expected;
        logic [31:0] line_base;

        if (item.is_icache) cfg.stats.i_refill_done++;
        else                cfg.stats.d_refill_done++;

        if (item.beat.size() != cfg.refill_beats) begin
            `uvm_error("REFILLBEATS",
                $sformatf("%s refill of 0x%08h returned %0d beats, the line is %0d words",
                          item.is_icache ? "I" : "D", item.addr, item.beat.size(),
                          cfg.refill_beats))
            return;
        end
        if (item.error) begin
            `uvm_error("REFILLERR",
                $sformatf("%s refill of 0x%08h reported rsp_error",
                          item.is_icache ? "I" : "D", item.addr))
            return;
        end

        // A refill returns the whole line containing the requested address, so
        // the reference data starts at the line base, not at the request.
        line_base = item.addr & ~32'((cfg.refill_beats * 4) - 1);
        foreach (item.beat[i]) begin
            expected = cfg.mem.read_word(line_base + 32'(4 * i));
            if (item.beat[i] !== expected)
                `uvm_error("REFILLDATA",
                    $sformatf("%s refill 0x%08h beat %0d: expected 0x%08h, got 0x%08h",
                              item.is_icache ? "I" : "D", item.addr, i,
                              expected, item.beat[i]))
        end
    endfunction

    function void write_wthru(wthru_item item);
        // The response came back; the AXI write may still be draining.
        wr_drain_q.push_back(item);
    endfunction

    function void write_axi(axi_item item);
        wthru_item req;

        case (item.kind)
            AXI_READ_BURST: begin
                if (item.len !== 8'(cfg.refill_beats - 1))
                    `uvm_error("ARLEN",
                        $sformatf("read burst at 0x%08h has arlen=%0d, expected %0d",
                                  item.addr, item.len, cfg.refill_beats - 1))
                if (item.size !== 3'd2)
                    `uvm_error("ARSIZE",
                        $sformatf("read burst at 0x%08h has arsize=%0d, expected 2 (4 bytes)",
                                  item.addr, item.size))
                if (item.burst !== 2'b01)
                    `uvm_error("ARBURST",
                        $sformatf("read burst at 0x%08h has arburst=%0d, expected INCR",
                                  item.addr, item.burst))
                // A refill is aligned to its own line, not to a fixed 16 bytes.
                if ((item.addr & ((cfg.refill_beats * 4) - 1)) != 0)
                    `uvm_error("ARALIGN",
                        $sformatf("read burst address 0x%08h is not %0d-byte aligned",
                                  item.addr, cfg.refill_beats * 4))
                if (item.data.size() != cfg.refill_beats)
                    `uvm_error("RBEATS",
                        $sformatf("read burst at 0x%08h returned %0d beats, expected %0d",
                                  item.addr, item.data.size(), cfg.refill_beats))
                if (item.resp !== 2'b00)
                    `uvm_error("RRESP",
                        $sformatf("read burst at 0x%08h answered rresp=%0d", item.addr, item.resp))
            end

            AXI_WRITE: begin
                if (item.len !== 8'd0)
                    `uvm_error("AWLEN",
                        $sformatf("write at 0x%08h has awlen=%0d, expected 0",
                                  item.addr, item.len))
                if (item.size !== 3'd2)
                    `uvm_error("AWSIZE",
                        $sformatf("write at 0x%08h has awsize=%0d, expected 2", item.addr, item.size))
                if (item.data.size() != 1)
                    `uvm_error("WBEATS",
                        $sformatf("write at 0x%08h carried %0d beats", item.addr, item.data.size()))
                if (item.resp !== 2'b00)
                    `uvm_error("BRESP",
                        $sformatf("write at 0x%08h answered bresp=%0d", item.addr, item.resp))

                // Match it against the write-through request that produced it.
                if (wr_drain_q.size() == 0)
                    `uvm_error("AXIWEXTRA",
                        $sformatf("AXI write to 0x%08h with no pending write-through request",
                                  item.addr))
                else begin
                    req = wr_drain_q.pop_front();
                    if (req.addr !== item.addr)
                        `uvm_error("AXIWADDR",
                            $sformatf("write-through 0x%08h reached AXI as 0x%08h",
                                      req.addr, item.addr))
                    else if ((req.data !== item.data[0]) || (req.strb !== item.strb))
                        `uvm_error("AXIWDATA",
                            $sformatf("write-through 0x%08h data 0x%08h/%4b reached AXI as 0x%08h/%4b",
                                      req.addr, req.data, req.strb, item.data[0], item.strb))
                    else if (req.rsp_cycle < item.end_cycle)
                        // Not an error: the evidence that the buffer posts, i.e.
                        // the store was answered before the AXI B came back.
                        cfg.stats.posted_rsp_before_b++;
                end
            end
        endcase
    endfunction

    function void check_phase(uvm_phase phase);
        axi_stats s;
        super.check_phase(phase);
        s = cfg.stats;

        if (wr_drain_q.size() != 0)
            `uvm_error("WRLEFTOVER",
                $sformatf("%0d write-through requests never reached AXI (first 0x%08h)",
                          wr_drain_q.size(), wr_drain_q[0].addr))

        if (s.wthru_req != s.wthru_rsp)
            `uvm_error("WTHRUCOUNT",
                $sformatf("%0d write-through requests but %0d responses",
                          s.wthru_req, s.wthru_rsp))
        if (s.wthru_rsp != s.axi_write)
            `uvm_error("WRITECOUNT",
                $sformatf("%0d write-through responses but %0d AXI writes",
                          s.wthru_rsp, s.axi_write))

        if ((s.i_refill_done + s.d_refill_done) != s.axi_read_burst)
            `uvm_error("READCOUNT",
                $sformatf("%0d refills completed but %0d AXI read bursts",
                          s.i_refill_done + s.d_refill_done, s.axi_read_burst))
        if (s.axi_read_beats != (cfg.refill_beats * s.axi_read_burst))
            `uvm_error("BEATCOUNT",
                $sformatf("%0d read beats for %0d bursts, expected %0d per burst",
                          s.axi_read_beats, s.axi_read_burst, cfg.refill_beats))
        if (s.max_outstanding_reads > 1)
            `uvm_error("OUTSTANDING",
                $sformatf("peak of %0d outstanding read bursts, the design allows one",
                          s.max_outstanding_reads))

        // The point of posting: at least some stores were answered before their
        // AXI B response came back. If none were, the buffer is not posting.
        if ((s.axi_write > 0) && (s.posted_rsp_before_b == 0))
            `uvm_error("NOTPOSTED",
                "no write-through response arrived before its AXI B response; the posted-write buffer did not post")
    endfunction

    function void report_phase(uvm_phase phase);
        axi_stats s;
        super.report_phase(phase);
        s = cfg.stats;
        `uvm_info("SUMMARY", $sformatf(
            {"\n  I refills   : %0d requested / %0d completed",
             "\n  D refills   : %0d requested / %0d completed",
             "\n  writes      : %0d requested / %0d answered",
             "\n  AXI reads   : %0d bursts, %0d beats",
             "\n  AXI writes  : %0d",
             "\n  peak outstanding reads : %0d",
             "\n  posted answers ahead of B : %0d"},
            s.i_refill_req, s.i_refill_done,
            s.d_refill_req, s.d_refill_done,
            s.wthru_req, s.wthru_rsp,
            s.axi_read_burst, s.axi_read_beats,
            s.axi_write, s.max_outstanding_reads,
            s.posted_rsp_before_b), UVM_LOW)
    endfunction

endclass
