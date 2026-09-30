`timescale 1ns/1ps

module tb_dcache;

reg clk;
reg reset_n;

reg         req_valid;
reg         req_write;
reg  [31:0] req_addr;
reg  [31:0] req_wdata;
reg  [3:0]  req_wstrb;
wire        req_ready;
wire        rsp_valid;
wire [31:0] rsp_rdata;
wire        rsp_error;

wire        refill_req_valid;
wire [31:0] refill_req_addr;
wire        refill_req_ready;
wire        refill_rsp_valid;
wire [31:0] refill_rsp_data;
wire        refill_rsp_last;
wire        refill_rsp_error;

wire        mem_wr_valid;
wire [31:0] mem_wr_addr;
wire [31:0] mem_wr_data;
wire [3:0]  mem_wr_strb;
wire        mem_wr_ready;
wire        mem_wr_rsp_valid;
wire        mem_wr_rsp_error;

wire [31:0] access_count;
wire [31:0] read_count;
wire [31:0] write_count;
wire [31:0] hit_count;
wire [31:0] miss_count;
wire [31:0] read_hit_count;
wire [31:0] read_miss_count;
wire [31:0] write_hit_count;
wire [31:0] write_miss_count;

integer errors;
reg test_pass;
integer cpu_accept_count;
integer cpu_response_count;
integer refill_request_count;
integer refill_beat_count_total;
integer write_request_count;
integer i;

integer refill_ready_delay_cfg;
integer refill_first_delay_cfg;
integer refill_gap_cfg;
integer write_ready_delay_cfg;
integer write_response_delay_cfg;

reg [31:0] backing_mem [0:1023];
reg [31:0] last_refill_addr;
reg [31:0] last_write_addr;
reg [31:0] last_write_data;
reg [3:0]  last_write_strb;

localparam [2:0] RB_IDLE       = 3'd0;
localparam [2:0] RB_WAIT_READY = 3'd1;
localparam [2:0] RB_ACCEPT     = 3'd2;
localparam [2:0] RB_WAIT_DATA  = 3'd3;
localparam [2:0] RB_SEND       = 3'd4;

reg [2:0]  refill_backend_state;
reg [31:0] refill_waiting_addr;
reg [31:0] refill_active_base;
reg [1:0]  refill_backend_beat;
integer refill_delay_count;
integer refill_gap_count;

localparam [2:0] WB_IDLE       = 3'd0;
localparam [2:0] WB_WAIT_READY = 3'd1;
localparam [2:0] WB_ACCEPT     = 3'd2;
localparam [2:0] WB_WAIT_RESP  = 3'd3;
localparam [2:0] WB_RESP       = 3'd4;

reg [2:0]  write_backend_state;
reg [31:0] write_waiting_addr;
reg [31:0] write_waiting_data;
reg [3:0]  write_waiting_strb;
integer write_delay_count;

function automatic [31:0] pattern_word;
    input [31:0] address;
    begin
        pattern_word = 32'h1000_0000 + address[31:2];
    end
endfunction

function automatic [31:0] merge_wstrb;
    input [31:0] old_word;
    input [31:0] new_word;
    input [3:0]  strobe;
    begin
        merge_wstrb = old_word;
        if(strobe[0]) merge_wstrb[7:0]   = new_word[7:0];
        if(strobe[1]) merge_wstrb[15:8]  = new_word[15:8];
        if(strobe[2]) merge_wstrb[23:16] = new_word[23:16];
        if(strobe[3]) merge_wstrb[31:24] = new_word[31:24];
    end
endfunction

assign refill_req_ready = (refill_backend_state == RB_ACCEPT);
assign refill_rsp_valid = (refill_backend_state == RB_SEND) &&
                          (refill_gap_count == 0);
assign refill_rsp_data = backing_mem[(refill_active_base >> 2) +
                                     refill_backend_beat];
assign refill_rsp_last = refill_rsp_valid && (refill_backend_beat == 2'd3);
assign refill_rsp_error = 1'b0;

assign mem_wr_ready = (write_backend_state == WB_ACCEPT);
assign mem_wr_rsp_valid = (write_backend_state == WB_RESP);
assign mem_wr_rsp_error = 1'b0;

dcache #(
    .LINE_COUNT (64)
) dut (
    .clk                  (clk),
    .reset_n              (reset_n),
    .req_valid            (req_valid),
    .req_write            (req_write),
    .req_addr             (req_addr),
    .req_wdata            (req_wdata),
    .req_wstrb            (req_wstrb),
    .req_ready            (req_ready),
    .rsp_valid            (rsp_valid),
    .rsp_rdata            (rsp_rdata),
    .rsp_error            (rsp_error),
    .refill_req_valid     (refill_req_valid),
    .refill_req_addr      (refill_req_addr),
    .refill_req_ready     (refill_req_ready),
    .refill_rsp_valid     (refill_rsp_valid),
    .refill_rsp_data      (refill_rsp_data),
    .refill_rsp_last      (refill_rsp_last),
    .refill_rsp_error     (refill_rsp_error),
    .mem_wr_valid         (mem_wr_valid),
    .mem_wr_addr          (mem_wr_addr),
    .mem_wr_data          (mem_wr_data),
    .mem_wr_strb          (mem_wr_strb),
    .mem_wr_ready         (mem_wr_ready),
    .mem_wr_rsp_valid     (mem_wr_rsp_valid),
    .mem_wr_rsp_error     (mem_wr_rsp_error),
    .access_count         (access_count),
    .read_count           (read_count),
    .write_count          (write_count),
    .hit_count            (hit_count),
    .miss_count           (miss_count),
    .read_hit_count       (read_hit_count),
    .read_miss_count      (read_miss_count),
    .write_hit_count      (write_hit_count),
    .write_miss_count     (write_miss_count),
    .read_access_event(), .read_hit_event(), .read_miss_event(),
    .write_access_event(), .write_hit_event(), .write_miss_event(),
    .main_hit_count(), .victim_hit_count(), .true_miss_count(),
    .main_hit_event(), .victim_hit_event(), .true_miss_event()
);

always #5 clk = ~clk;

// Backpressure-capable four-beat read-refill backend.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        refill_backend_state  <= RB_IDLE;
        refill_waiting_addr   <= 32'h0000_0000;
        refill_active_base    <= 32'h0000_0000;
        refill_backend_beat   <= 2'd0;
        refill_delay_count    <= 0;
        refill_gap_count      <= 0;
        refill_request_count  <= 0;
        refill_beat_count_total <= 0;
        last_refill_addr      <= 32'h0000_0000;
    end
    else begin
        case(refill_backend_state)
            RB_IDLE: begin
                if(refill_req_valid) begin
                    refill_waiting_addr <= refill_req_addr;
                    refill_delay_count  <= refill_ready_delay_cfg;
                    if(refill_ready_delay_cfg == 0)
                        refill_backend_state <= RB_ACCEPT;
                    else
                        refill_backend_state <= RB_WAIT_READY;
                end
            end

            RB_WAIT_READY: begin
                if(!refill_req_valid)
                    $fatal(1, "refill_req_valid dropped before ready");
                if(refill_req_addr !== refill_waiting_addr)
                    $fatal(1, "refill_req_addr changed under backpressure");
                if(refill_delay_count <= 1)
                    refill_backend_state <= RB_ACCEPT;
                else
                    refill_delay_count <= refill_delay_count - 1;
            end

            RB_ACCEPT: begin
                if(!refill_req_valid)
                    $fatal(1, "refill request missing on ready cycle");
                if(refill_req_addr !== refill_waiting_addr)
                    $fatal(1, "refill address changed on ready cycle");
                if(refill_req_addr[3:0] !== 4'b0000)
                    $fatal(1, "refill address is not line aligned: %08h",
                           refill_req_addr);

                refill_active_base      <= refill_req_addr;
                last_refill_addr        <= refill_req_addr;
                refill_request_count    <= refill_request_count + 1;
                refill_backend_beat     <= 2'd0;
                refill_gap_count        <= 0;
                refill_delay_count      <= refill_first_delay_cfg;
                if(refill_first_delay_cfg == 0)
                    refill_backend_state <= RB_SEND;
                else
                    refill_backend_state <= RB_WAIT_DATA;
            end

            RB_WAIT_DATA: begin
                if(refill_delay_count <= 1)
                    refill_backend_state <= RB_SEND;
                else
                    refill_delay_count <= refill_delay_count - 1;
            end

            RB_SEND: begin
                if(refill_gap_count != 0) begin
                    refill_gap_count <= refill_gap_count - 1;
                end
                else begin
                    refill_beat_count_total <= refill_beat_count_total + 1;
                    if(refill_backend_beat == 2'd3) begin
                        refill_backend_beat  <= 2'd0;
                        refill_backend_state <= RB_IDLE;
                    end
                    else begin
                        refill_backend_beat <= refill_backend_beat + 1'b1;
                        refill_gap_count    <= refill_gap_cfg;
                    end
                end
            end

            default: refill_backend_state <= RB_IDLE;
        endcase
    end
end

// Independent write backend. It merges exactly the selected byte lanes once
// at the request handshake, then returns one completion response.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        write_backend_state <= WB_IDLE;
        write_waiting_addr  <= 32'h0000_0000;
        write_waiting_data  <= 32'h0000_0000;
        write_waiting_strb  <= 4'b0000;
        write_delay_count   <= 0;
        write_request_count <= 0;
        last_write_addr     <= 32'h0000_0000;
        last_write_data     <= 32'h0000_0000;
        last_write_strb     <= 4'b0000;
    end
    else begin
        case(write_backend_state)
            WB_IDLE: begin
                if(mem_wr_valid) begin
                    write_waiting_addr <= mem_wr_addr;
                    write_waiting_data <= mem_wr_data;
                    write_waiting_strb <= mem_wr_strb;
                    write_delay_count  <= write_ready_delay_cfg;
                    if(write_ready_delay_cfg == 0)
                        write_backend_state <= WB_ACCEPT;
                    else
                        write_backend_state <= WB_WAIT_READY;
                end
            end

            WB_WAIT_READY: begin
                if(!mem_wr_valid)
                    $fatal(1, "mem_wr_valid dropped before ready");
                if((mem_wr_addr !== write_waiting_addr) ||
                   (mem_wr_data !== write_waiting_data) ||
                   (mem_wr_strb !== write_waiting_strb))
                    $fatal(1, "write request fields changed under backpressure");
                if(write_delay_count <= 1)
                    write_backend_state <= WB_ACCEPT;
                else
                    write_delay_count <= write_delay_count - 1;
            end

            WB_ACCEPT: begin
                if(!mem_wr_valid)
                    $fatal(1, "write request missing on ready cycle");
                if((mem_wr_addr !== write_waiting_addr) ||
                   (mem_wr_data !== write_waiting_data) ||
                   (mem_wr_strb !== write_waiting_strb))
                    $fatal(1, "write request fields changed on ready cycle");

                backing_mem[mem_wr_addr >> 2] <=
                    merge_wstrb(backing_mem[mem_wr_addr >> 2],
                                mem_wr_data, mem_wr_strb);
                last_write_addr     <= mem_wr_addr;
                last_write_data     <= mem_wr_data;
                last_write_strb     <= mem_wr_strb;
                write_request_count <= write_request_count + 1;
                write_delay_count   <= write_response_delay_cfg;
                if(write_response_delay_cfg == 0)
                    write_backend_state <= WB_RESP;
                else
                    write_backend_state <= WB_WAIT_RESP;
            end

            WB_WAIT_RESP: begin
                if(write_delay_count <= 1)
                    write_backend_state <= WB_RESP;
                else
                    write_delay_count <= write_delay_count - 1;
            end

            WB_RESP: write_backend_state <= WB_IDLE;

            default: write_backend_state <= WB_IDLE;
        endcase
    end
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        cpu_accept_count   <= 0;
        cpu_response_count <= 0;
    end
    else begin
        if(req_valid && req_ready)
            cpu_accept_count <= cpu_accept_count + 1;
        if(rsp_valid)
            cpu_response_count <= cpu_response_count + 1;
        if(cpu_response_count > cpu_accept_count)
            $fatal(1, "response without an accepted CPU request");
    end
end

// Counter invariants must hold after every accounted request, not only at the
// end of a selected sequence.
always @(negedge clk) begin
    if(reset_n) begin
        if(access_count !== (hit_count + miss_count))
            $fatal(1, "access/hit/miss invariant failed: %0d/%0d/%0d",
                   access_count, hit_count, miss_count);
        if(access_count !== (read_count + write_count))
            $fatal(1, "access/read/write invariant failed: %0d/%0d/%0d",
                   access_count, read_count, write_count);
        if(hit_count !== (read_hit_count + write_hit_count))
            $fatal(1, "hit detail invariant failed");
        if(miss_count !== (read_miss_count + write_miss_count))
            $fatal(1, "miss detail invariant failed");
    end
end

task automatic expect_value;
    input [31:0] actual;
    input [31:0] expected;
    input [8*80-1:0] label_text;
    begin
        if(actual !== expected) begin
            $error("%0s expected=%08h actual=%08h", label_text, expected, actual);
            errors = errors + 1;
        end
    end
endtask

task automatic reset_case;
    begin
        @(negedge clk);
        reset_n = 1'b0;
        req_valid = 1'b0;
        req_write = 1'b0;
        req_addr  = 32'h0000_0000;
        req_wdata = 32'h0000_0000;
        req_wstrb = 4'b0000;
        refill_ready_delay_cfg   = 0;
        refill_first_delay_cfg   = 0;
        refill_gap_cfg           = 0;
        write_ready_delay_cfg    = 0;
        write_response_delay_cfg = 0;
        for(i = 0; i < 1024; i = i + 1)
            backing_mem[i] = pattern_word(i * 4);
        repeat(3) @(posedge clk);
        @(negedge clk);
        reset_n = 1'b1;
    end
endtask

task automatic cpu_access;
    input        write_access;
    input [31:0] address;
    input [31:0] write_data;
    input [3:0]  write_strobe;
    input [31:0] expected_read_data;
    input        hold_valid_until_response;
    output [31:0] returned_data;
    integer watchdog;
    begin
        @(negedge clk);
        req_valid = 1'b1;
        req_write = write_access;
        req_addr  = address;
        req_wdata = write_data;
        req_wstrb = write_strobe;
        watchdog = 0;
        while(!req_ready) begin
            @(negedge clk);
            watchdog = watchdog + 1;
            if(watchdog > 300)
                $fatal(1, "CPU request timeout addr=%08h", address);
        end

        @(posedge clk);
        #1;
        if(!hold_valid_until_response) begin
            @(negedge clk);
            req_valid = 1'b0;
            req_addr  = 32'hdead_beef;
        end

        watchdog = 0;
        while(!rsp_valid) begin
            @(posedge clk);
            #1;
            watchdog = watchdog + 1;
            if(watchdog > 600)
                $fatal(1, "CPU response timeout addr=%08h", address);
        end

        returned_data = rsp_rdata;
        if(rsp_error)
            $fatal(1, "unexpected CPU response error addr=%08h", address);
        if(!write_access && (rsp_rdata !== expected_read_data)) begin
            $error("read addr=%08h expected=%08h got=%08h",
                   address, expected_read_data, rsp_rdata);
            errors = errors + 1;
        end

        @(negedge clk);
        if(hold_valid_until_response)
            req_valid = 1'b0;
        req_write = 1'b0;
        req_addr  = 32'h0000_0000;
        req_wdata = 32'h0000_0000;
        req_wstrb = 4'b0000;
    end
endtask

task automatic cpu_fast_load;
    input [31:0] address;
    input [31:0] expected_read_data;
    output [31:0] returned_data;
    begin
        @(negedge clk);
        req_valid = 1'b1;
        req_write = 1'b0;
        req_addr  = address;
        req_wdata = 32'h0000_0000;
        req_wstrb = 4'b0000;
        #1;
        if(!req_ready)
            $fatal(1, "fast-load cache was not ready addr=%08h", address);
        if(!rsp_valid)
            $fatal(1, "resident DM load did not respond in request cycle addr=%08h", address);
        returned_data = rsp_rdata;
        if(rsp_error || (rsp_rdata !== expected_read_data))
            $fatal(1, "fast-load mismatch addr=%08h expected=%08h got=%08h",
                   address, expected_read_data, rsp_rdata);
        @(posedge clk);
        #1;
        @(negedge clk);
        req_valid = 1'b0;
        req_addr  = 32'h0000_0000;
    end
endtask

task automatic back_to_back_reads;
    input [31:0] address_a;
    input [31:0] expected_a;
    input [31:0] address_b;
    input [31:0] expected_b;
    integer watchdog;
    begin
        @(negedge clk);
        req_valid = 1'b1;
        req_write = 1'b0;
        req_addr  = address_a;
        req_wdata = 32'h0;
        req_wstrb = 4'h0;
        while(!req_ready) @(negedge clk);
        @(posedge clk);
        @(negedge clk);
        req_valid = 1'b0;

        watchdog = 0;
        while(!rsp_valid) begin
            @(posedge clk);
            #1;
            watchdog = watchdog + 1;
            if(watchdog > 600) $fatal(1, "back-to-back response A timeout");
        end
        if(rsp_error || (rsp_rdata !== expected_a))
            $fatal(1, "back-to-back response A incorrect");

        // Assert B at the first falling edge after A's response. It remains
        // stable until the cache returns to IDLE and accepts it.
        @(negedge clk);
        req_valid = 1'b1;
        req_addr  = address_b;
        while(!req_ready) @(negedge clk);
        @(posedge clk);
        @(negedge clk);
        req_valid = 1'b0;

        watchdog = 0;
        while(!rsp_valid) begin
            @(posedge clk);
            #1;
            watchdog = watchdog + 1;
            if(watchdog > 600) $fatal(1, "back-to-back response B timeout");
        end
        if(rsp_error || (rsp_rdata !== expected_b))
            $fatal(1, "back-to-back response B incorrect");
        @(negedge clk);
        req_addr = 32'h0000_0000;
        @(posedge clk);
        #1;
    end
endtask

reg [31:0] result;
integer before_refills;
integer before_writes;

initial begin
    clk = 1'b0;
    reset_n = 1'b0;
    req_valid = 1'b0;
    req_write = 1'b0;
    req_addr  = 32'h0;
    req_wdata = 32'h0;
    req_wstrb = 4'h0;
    errors = 0;
    test_pass = 1'b0;
    refill_ready_delay_cfg = 0;
    refill_first_delay_cfg = 0;
    refill_gap_cfg = 0;
    write_ready_delay_cfg = 0;
    write_response_delay_cfg = 0;

    $display("===== D-CACHE SELF-CHECKING TEST =====");

    // TEST 1: cold load miss.
    reset_case();
    $display("[TEST 1] Load cold miss");
    cpu_access(1'b0, 32'h0000_0000, 32'h0, 4'h0,
               pattern_word(32'h0), 1'b0, result);
    expect_value(access_count, 32'd1, "T1 access_count");
    expect_value(read_count, 32'd1, "T1 read_count");
    expect_value(hit_count, 32'd0, "T1 hit_count");
    expect_value(miss_count, 32'd1, "T1 miss_count");
    expect_value(refill_request_count, 32'd1, "T1 refill requests");
    expect_value(refill_beat_count_total, 32'd4, "T1 refill beats");

    // TEST 2: same address is now a hit and does not refill.
    $display("[TEST 2] Load hit");
    before_refills = refill_request_count;
    cpu_fast_load(32'h0000_0000, pattern_word(32'h0), result);
    expect_value(hit_count, 32'd1, "T2 hit_count");
    expect_value(refill_request_count, before_refills, "T2 no refill");

    // TEST 3: the other three words from the resident line must hit.
    $display("[TEST 3] Word offset / spatial locality");
    cpu_access(1'b0, 32'h0000_0004, 32'h0, 4'h0,
               pattern_word(32'h4), 1'b0, result);
    cpu_access(1'b0, 32'h0000_0008, 32'h0, 4'h0,
               pattern_word(32'h8), 1'b0, result);
    cpu_access(1'b0, 32'h0000_000c, 32'h0, 4'h0,
               pattern_word(32'hc), 1'b0, result);
    expect_value(access_count, 32'd5, "T3 access_count");
    expect_value(hit_count, 32'd4, "T3 hit_count");
    expect_value(miss_count, 32'd1, "T3 miss_count");
    expect_value(refill_request_count, 32'd1, "T3 no new refill");

    // TEST 4: 0x000 and 0x400 share index zero but have different tags.
    reset_case();
    $display("[TEST 4] Load conflict replacement");
    cpu_access(1'b0, 32'h0000_0000, 0, 0, pattern_word(0), 0, result);
    cpu_access(1'b0, 32'h0000_0000, 0, 0, pattern_word(0), 0, result);
    cpu_access(1'b0, 32'h0000_0400, 0, 0, pattern_word(32'h400), 0, result);
    cpu_access(1'b0, 32'h0000_0400, 0, 0, pattern_word(32'h400), 0, result);
    cpu_access(1'b0, 32'h0000_0000, 0, 0, pattern_word(0), 0, result);
    // The fifth access used to miss: 0x000's main line had been replaced by
    // 0x400, and the L0 hot buffer was not allowed to answer unless the main
    // tag agreed. With a synchronous tag array that agreement cannot be had in
    // the request cycle, so the hot buffer is authoritative on its own -- it
    // compares the whole block address and is updated on every store commit.
    // Both 0x000 and 0x400 fit in its two entries, so the conflict is absorbed
    // and the fifth access is a hit served from cache storage without going to
    // memory. One fewer miss, one fewer refill.
    expect_value(access_count, 32'd5, "T4 access_count");
    expect_value(hit_count, 32'd3, "T4 hit_count");
    expect_value(miss_count, 32'd2, "T4 miss_count");
    expect_value(refill_request_count, 32'd2, "T4 refill requests");

    // TEST 4b: the hot buffer is now answering loads without a main-tag check,
    // so it must never hold data that a store has moved past. Store to a block
    // that is still in the hot buffer but has been evicted from the main array,
    // then read it back. A stale hot copy returns the pre-store value here.
    reset_case();
    $display("[TEST 4b] Hot-buffer coherence after eviction");
    backing_mem['h000 >> 2] = 32'h1111_1111;
    backing_mem['h400 >> 2] = 32'h2222_2222;
    cpu_access(0, 32'h0000_0000, 0, 0, 32'h1111_1111, 0, result);
    cpu_access(0, 32'h0000_0400, 0, 0, 32'h2222_2222, 0, result);
    // 0x000 is evicted from index zero at this point, but still in the L0.
    cpu_access(1, 32'h0000_0000, 32'hfeed_face, 4'hf, 0, 0, result);
    expect_value(last_write_addr, 32'h0, "T4b write-through address");
    expect_value(last_write_data, 32'hfeed_face, "T4b write-through data");
    cpu_access(0, 32'h0000_0000, 0, 0, 32'hfeed_face, 0, result);

    // TEST 5: store hit updates cache and writes through before CPU completion.
    reset_case();
    $display("[TEST 5] Store hit / write-through");
    backing_mem[0] = 32'h0102_0304;
    cpu_access(0, 32'h0, 0, 0, 32'h0102_0304, 0, result);
    before_refills = refill_request_count;
    cpu_access(1, 32'h0, 32'hdead_beef, 4'hf, 0, 0, result);
    expect_value(last_write_addr, 32'h0, "T5 backend address");
    expect_value(last_write_data, 32'hdead_beef, "T5 backend data");
    expect_value({28'h0,last_write_strb}, 32'hf, "T5 backend WSTRB");
    expect_value(refill_request_count, before_refills, "T5 store no refill");
    cpu_access(0, 32'h0, 0, 0, 32'hdead_beef, 0, result);
    expect_value(access_count, 32'd3, "T5 access_count");
    expect_value(hit_count, 32'd2, "T5 hit_count");
    expect_value(miss_count, 32'd1, "T5 miss_count");
    expect_value(write_request_count, 32'd1, "T5 backend writes");

    // TEST 6: byte strobe merges only byte lane 1.
    reset_case();
    $display("[TEST 6] Store byte merge");
    backing_mem[0] = 32'haabb_ccdd;
    cpu_access(0, 32'h0, 0, 0, 32'haabb_ccdd, 0, result);
    cpu_access(1, 32'h1, 32'h0000_5500, 4'b0010, 0, 0, result);
    expect_value(backing_mem[0], 32'haabb_55dd, "T6 backend merged word");
    expect_value({28'h0,last_write_strb}, 32'h2, "T6 WSTRB");
    cpu_access(0, 32'h0, 0, 0, 32'haabb_55dd, 0, result);

    // TEST 7: lower and upper halfword strobes.
    reset_case();
    $display("[TEST 7] Store halfword merge");
    backing_mem[0] = 32'h1122_3344;
    cpu_access(0, 32'h0, 0, 0, 32'h1122_3344, 0, result);
    cpu_access(1, 32'h0, 32'h0000_aabb, 4'b0011, 0, 0, result);
    expect_value(backing_mem[0], 32'h1122_aabb, "T7 lower half merge");
    expect_value({28'h0,last_write_strb}, 32'h3, "T7 lower WSTRB");
    cpu_access(1, 32'h2, 32'hccdd_0000, 4'b1100, 0, 0, result);
    expect_value(backing_mem[0], 32'hccdd_aabb, "T7 upper half merge");
    expect_value({28'h0,last_write_strb}, 32'hc, "T7 upper WSTRB");
    cpu_access(0, 32'h0, 0, 0, 32'hccdd_aabb, 0, result);

    // TEST 8: store miss writes memory but must not replace resident A.
    reset_case();
    $display("[TEST 8] Store miss / no-write-allocate");
    backing_mem[0]       = 32'h1111_1111;
    backing_mem[32'h100] = 32'h2222_2222;
    cpu_access(0, 32'h0000_0000, 0, 0, 32'h1111_1111, 0, result);
    before_refills = refill_request_count;
    cpu_access(1, 32'h0000_0400, 32'hcafe_babe, 4'hf, 0, 0, result);
    expect_value(refill_request_count, before_refills, "T8 store miss no refill");
    cpu_access(0, 32'h0000_0000, 0, 0, 32'h1111_1111, 0, result);
    expect_value(refill_request_count, before_refills, "T8 A remains resident");
    cpu_access(0, 32'h0000_0400, 0, 0, 32'hcafe_babe, 0, result);
    expect_value(access_count, 32'd4, "T8 access_count");
    expect_value(hit_count, 32'd1, "T8 hit_count");
    expect_value(miss_count, 32'd3, "T8 miss_count");
    expect_value(refill_request_count, 32'd2, "T8 load refills only");

    // TEST 9: write valid and all payload fields remain stable under pressure.
    reset_case();
    $display("[TEST 9] Backend write backpressure");
    cpu_access(0, 32'h0, 0, 0, pattern_word(0), 0, result);
    write_ready_delay_cfg    = 5;
    write_response_delay_cfg = 4;
    cpu_access(1, 32'h0, 32'h1234_5678, 4'hf, 0, 1, result);
    expect_value(write_request_count, 32'd1, "T9 exactly one backend write");
    expect_value(access_count, 32'd2, "T9 exactly two CPU accesses");
    expect_value(hit_count, 32'd1, "T9 store hit once");

    // TEST 10: line request and beats survive refill ready/valid delays.
    reset_case();
    $display("[TEST 10] Refill backpressure");
    refill_ready_delay_cfg = 5;
    refill_first_delay_cfg = 4;
    refill_gap_cfg         = 2;
    cpu_access(0, 32'h0000_002c, 0, 0,
               pattern_word(32'h2c), 1, result);
    expect_value(last_refill_addr, 32'h0000_0020, "T10 aligned line base");
    expect_value(refill_request_count, 32'd1, "T10 one refill request");
    expect_value(refill_beat_count_total, 32'd4, "T10 four refill beats");
    expect_value(access_count, 32'd1, "T10 one access");
    expect_value(hit_count, 32'd0, "T10 no synthetic hit");
    expect_value(miss_count, 32'd1, "T10 one miss");

    // TEST 11: exact accounting for a known read/write, hit/miss sequence.
    reset_case();
    $display("[TEST 11] Exact counter accounting");
    cpu_access(0, 32'h0, 0, 0, pattern_word(0), 0, result);        // read miss
    cpu_access(0, 32'h0, 0, 0, pattern_word(0), 0, result);        // read hit
    cpu_access(1, 32'h0, 32'h5555_aaaa, 4'hf, 0, 0, result);       // write hit
    cpu_access(1, 32'h400, 32'h7777_9999, 4'hf, 0, 0, result);     // write miss
    cpu_access(0, 32'h400, 0, 0, 32'h7777_9999, 0, result);        // read miss
    expect_value(access_count, 32'd5, "T11 access_count");
    expect_value(read_count, 32'd3, "T11 read_count");
    expect_value(write_count, 32'd2, "T11 write_count");
    expect_value(hit_count, 32'd2, "T11 hit_count");
    expect_value(miss_count, 32'd3, "T11 miss_count");
    expect_value(read_hit_count, 32'd1, "T11 read_hit_count");
    expect_value(read_miss_count, 32'd2, "T11 read_miss_count");
    expect_value(write_hit_count, 32'd1, "T11 write_hit_count");
    expect_value(write_miss_count, 32'd1, "T11 write_miss_count");

    // TEST 12: B is asserted at the first opportunity after response A.
    reset_case();
    $display("[TEST 12] Back-to-back requests");
    back_to_back_reads(32'h0, pattern_word(0),
                       32'h4, pattern_word(4));
    expect_value(cpu_accept_count, 32'd2, "T12 accepted requests");
    expect_value(cpu_response_count, 32'd2, "T12 responses");
    expect_value(access_count, 32'd2, "T12 accounted requests");
    expect_value(hit_count, 32'd1, "T12 second word hit");
    expect_value(miss_count, 32'd1, "T12 first word miss");

    if(errors != 0)
        $fatal(1, "D-cache failed with %0d error(s)", errors);

    test_pass = 1'b1;
    $display("[PASS] D-cache tests 1-12");
    $display("[PASS] Counter invariants and backend handshake stability");
    $finish;
end

endmodule
