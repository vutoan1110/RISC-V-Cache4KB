`timescale 1ns/1ps

module tb_icache;

reg clk;
reg reset_n;
reg req_valid;
reg [31:0] req_addr;
wire req_ready;
wire rsp_valid;
wire [31:0] rsp_data;
wire rsp_error;

wire refill_req_valid;
wire [31:0] refill_req_addr;
wire refill_req_ready;
wire refill_rsp_valid;
wire [31:0] refill_rsp_data;
wire refill_rsp_last;
wire refill_rsp_error;

wire [31:0] access_count;
wire [31:0] hit_count;
wire [31:0] miss_count;

integer errors;
integer cpu_accept_count;
integer cpu_response_count;
integer refill_request_count;
integer refill_beats_total;
integer ready_delay_cfg;
integer response_delay_cfg;
integer response_gap_cfg;
integer delay_count;
integer gap_count;
integer watchdog;

localparam [2:0] B_IDLE       = 3'd0;
localparam [2:0] B_WAIT_READY = 3'd1;
localparam [2:0] B_ACCEPT     = 3'd2;
localparam [2:0] B_WAIT_RSP   = 3'd3;
localparam [2:0] B_SEND       = 3'd4;

reg [2:0] backend_state;
reg [31:0] waiting_req_addr;
reg [31:0] active_line_base;
reg [31:0] last_refill_addr;
reg [1:0] backend_beat;

function automatic [31:0] backing_word;
    input [31:0] address;
    begin
        backing_word = 32'h1000_0000 + address[31:2];
    end
endfunction

assign refill_req_ready = (backend_state == B_ACCEPT);
assign refill_rsp_valid = (backend_state == B_SEND) && (gap_count == 0);
assign refill_rsp_data  = backing_word(active_line_base +
                                         {28'h0000000, backend_beat, 2'b00});
assign refill_rsp_last  = refill_rsp_valid && (backend_beat == 2'd3);
assign refill_rsp_error = 1'b0;

icache #(
    .LINE_COUNT (64)
) dut (
    .clk              (clk),
    .reset_n          (reset_n),
    .req_valid        (req_valid),
    .req_addr         (req_addr),
    .req_ready        (req_ready),
    .rsp_valid        (rsp_valid),
    .rsp_data         (rsp_data),
    .rsp_error        (rsp_error),
    .refill_req_valid (refill_req_valid),
    .refill_req_addr  (refill_req_addr),
    .refill_req_ready (refill_req_ready),
    .refill_rsp_valid (refill_rsp_valid),
    .refill_rsp_data  (refill_rsp_data),
    .refill_rsp_last  (refill_rsp_last),
    .refill_rsp_error (refill_rsp_error),
    .access_count     (access_count),
    .hit_count        (hit_count),
    .miss_count       (miss_count),
    .access_event(), .hit_event(), .miss_event(),
    .main_hit_count(), .victim_hit_count(), .true_miss_count(),
    .main_hit_event(), .victim_hit_event(), .true_miss_event()
);

always #5 clk = ~clk;

// Backpressure-capable four-beat refill model. It observes one line request,
// may delay ready, may delay/gap responses, and then sends addresses +0/+4/+8/+C.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        backend_state       <= B_IDLE;
        waiting_req_addr    <= 32'h0000_0000;
        active_line_base    <= 32'h0000_0000;
        last_refill_addr    <= 32'h0000_0000;
        backend_beat        <= 2'd0;
        delay_count         <= 0;
        gap_count           <= 0;
        refill_request_count <= 0;
        refill_beats_total   <= 0;
    end
    else begin
        case(backend_state)
            B_IDLE: begin
                if(refill_req_valid) begin
                    waiting_req_addr <= refill_req_addr;
                    delay_count      <= ready_delay_cfg;
                    if(ready_delay_cfg == 0)
                        backend_state <= B_ACCEPT;
                    else
                        backend_state <= B_WAIT_READY;
                end
            end

            B_WAIT_READY: begin
                if(!refill_req_valid) begin
                    $display("[ERROR] refill_req_valid dropped before ready");
                    errors = errors + 1;
                end
                if(refill_req_addr !== waiting_req_addr) begin
                    $display("[ERROR] refill_req_addr changed under backpressure old=%08h new=%08h",
                             waiting_req_addr, refill_req_addr);
                    errors = errors + 1;
                end
                if(delay_count <= 1)
                    backend_state <= B_ACCEPT;
                else
                    delay_count <= delay_count - 1;
            end

            B_ACCEPT: begin
                if(!refill_req_valid) begin
                    $display("[ERROR] refill request missing on ready cycle");
                    errors = errors + 1;
                end
                else begin
                    if(refill_req_addr[3:0] != 4'b0000) begin
                        $display("[ERROR] refill request is not line aligned: %08h",
                                 refill_req_addr);
                        errors = errors + 1;
                    end
                    active_line_base     <= refill_req_addr;
                    last_refill_addr     <= refill_req_addr;
                    refill_request_count <= refill_request_count + 1;
                    backend_beat         <= 2'd0;
                    gap_count            <= 0;
                    delay_count          <= response_delay_cfg;
                    if(response_delay_cfg == 0)
                        backend_state <= B_SEND;
                    else
                        backend_state <= B_WAIT_RSP;
                end
            end

            B_WAIT_RSP: begin
                if(delay_count <= 1)
                    backend_state <= B_SEND;
                else
                    delay_count <= delay_count - 1;
            end

            B_SEND: begin
                if(gap_count != 0) begin
                    gap_count <= gap_count - 1;
                end
                else begin
                    refill_beats_total <= refill_beats_total + 1;
                    if(backend_beat == 2'd3) begin
                        backend_beat  <= 2'd0;
                        backend_state <= B_IDLE;
                    end
                    else begin
                        backend_beat <= backend_beat + 1'b1;
                        gap_count    <= response_gap_cfg;
                    end
                end
            end

            default: backend_state <= B_IDLE;
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
        // A resident fast hit may accept its request and return the
        // response in this same edge. Old counts are compared here because
        // the counters update nonblocking, so include the simultaneous fire.
        if(rsp_valid && (cpu_response_count >= cpu_accept_count) &&
           !(req_valid && req_ready)) begin
            $display("[ERROR] response without an unmatched accepted request");
            errors = errors + 1;
        end
    end
end

// Check the requested accounting invariant after all nonblocking updates.
always @(negedge clk) begin
    if(reset_n && (access_count !== (hit_count + miss_count))) begin
        $display("[ERROR] counter invariant access=%0d hit=%0d miss=%0d",
                 access_count, hit_count, miss_count);
        errors = errors + 1;
    end
end

task automatic reset_test;
    begin
        @(negedge clk);
        reset_n           = 1'b0;
        req_valid         = 1'b0;
        req_addr          = 32'h0000_0000;
        ready_delay_cfg   = 0;
        response_delay_cfg = 0;
        response_gap_cfg  = 0;
        repeat(3) @(posedge clk);
        @(negedge clk);
        reset_n = 1'b1;
    end
endtask

task automatic cpu_read;
    input [31:0] address;
    input        expect_refill;
    input        hold_valid_until_response;
    integer before_refills;
    integer before_beats;
    integer local_watchdog;
    reg [31:0] expected_data;
    begin
        expected_data  = backing_word(address);
        before_refills = refill_request_count;
        before_beats   = refill_beats_total;

        @(negedge clk);
        req_addr  = address;
        req_valid = 1'b1;
        local_watchdog = 0;
        while(!req_ready) begin
            @(negedge clk);
            local_watchdog = local_watchdog + 1;
            if(local_watchdog > 200)
                $fatal(1, "CPU request timeout addr=%08h", address);
        end

        // The request is accepted at this edge.
        @(posedge clk);
        #1;
        if(!hold_valid_until_response) begin
            @(negedge clk);
            req_valid = 1'b0;
            req_addr  = 32'hdead_beef;
        end

        local_watchdog = 0;
        while(!rsp_valid) begin
            @(posedge clk);
            #1;
            local_watchdog = local_watchdog + 1;
            if(local_watchdog > 300)
                $fatal(1, "CPU response timeout addr=%08h", address);
        end

        if(rsp_error || (rsp_data !== expected_data)) begin
            $display("[ERROR] response addr=%08h expected=%08h got=%08h error=%b",
                     address, expected_data, rsp_data, rsp_error);
            errors = errors + 1;
        end

        if(expect_refill) begin
            if((refill_request_count - before_refills) != 1) begin
                $display("[ERROR] addr=%08h expected one refill, observed %0d",
                         address, refill_request_count - before_refills);
                errors = errors + 1;
            end
            if((refill_beats_total - before_beats) != 4) begin
                $display("[ERROR] addr=%08h expected four refill beats, observed %0d",
                         address, refill_beats_total - before_beats);
                errors = errors + 1;
            end
        end
        else begin
            if((refill_request_count != before_refills) ||
               (refill_beats_total != before_beats)) begin
                $display("[ERROR] hit addr=%08h unexpectedly caused refill traffic", address);
                errors = errors + 1;
            end
        end

        if(hold_valid_until_response) begin
            // Drop before the next rising edge, after observing the response.
            @(negedge clk);
            req_valid = 1'b0;
            req_addr  = 32'hdead_beef;
        end
    end
endtask

task automatic check_counts;
    input integer expected_access;
    input integer expected_hit;
    input integer expected_miss;
    input integer expected_refills;
    input integer expected_beats;
    input [8*48-1:0] test_name;
    begin
        repeat(2) @(posedge clk);
        #1;
        if((access_count != expected_access) ||
           (hit_count != expected_hit) ||
           (miss_count != expected_miss)) begin
            $display("[ERROR] %0s counters access/hit/miss=%0d/%0d/%0d expected=%0d/%0d/%0d",
                     test_name, access_count, hit_count, miss_count,
                     expected_access, expected_hit, expected_miss);
            errors = errors + 1;
        end
        if((refill_request_count != expected_refills) ||
           (refill_beats_total != expected_beats)) begin
            $display("[ERROR] %0s refill req/beats=%0d/%0d expected=%0d/%0d",
                     test_name, refill_request_count, refill_beats_total,
                     expected_refills, expected_beats);
            errors = errors + 1;
        end
        if((cpu_accept_count != expected_access) ||
           (cpu_response_count != expected_access)) begin
            $display("[ERROR] %0s CPU accepted/responses=%0d/%0d expected=%0d/%0d",
                     test_name, cpu_accept_count, cpu_response_count,
                     expected_access, expected_access);
            errors = errors + 1;
        end
    end
endtask

initial begin
    clk                  = 1'b0;
    reset_n              = 1'b0;
    req_valid            = 1'b0;
    req_addr             = 32'h0000_0000;
    errors               = 0;
    ready_delay_cfg      = 0;
    response_delay_cfg   = 0;
    response_gap_cfg     = 0;

    $dumpfile("icache_tb.vcd");
    $dumpvars(0, tb_icache);

    // TEST 1: cold miss and a complete four-word line refill.
    reset_test();
    cpu_read(32'h0000_0000, 1'b1, 1'b0);
    check_counts(1, 0, 1, 1, 4, "TEST 1 cold miss");
    $display("[PASS] I-cache test 1 - cold miss");

    // TEST 2: the same word is a hit and produces no refill traffic.
    cpu_read(32'h0000_0000, 1'b0, 1'b0);
    check_counts(2, 1, 1, 1, 4, "TEST 2 same-address hit");
    $display("[PASS] I-cache test 2 - same-address hit");

    // TEST 3: all remaining words in the 16-byte line are spatial hits.
    cpu_read(32'h0000_0004, 1'b0, 1'b0);
    cpu_read(32'h0000_0008, 1'b0, 1'b0);
    cpu_read(32'h0000_000c, 1'b0, 1'b0);
    check_counts(5, 4, 1, 1, 4, "TEST 3 spatial locality");
    $display("[PASS] I-cache test 3 - spatial locality/word offset");

    // TEST 4: 0x000 and 0x400 share index zero for 64 x 16-byte lines.
    reset_test();
    cpu_read(32'h0000_0000, 1'b1, 1'b0);
    cpu_read(32'h0000_0000, 1'b0, 1'b0);
    cpu_read(32'h0000_0400, 1'b1, 1'b0);
    cpu_read(32'h0000_0000, 1'b1, 1'b0);
    check_counts(4, 1, 3, 3, 12, "TEST 4 conflict replacement");
    $display("[PASS] I-cache test 4 - conflict replacement");

    // TEST 5: hold the CPU request and stall both refill request and data.
    reset_test();
    ready_delay_cfg    = 4;
    response_delay_cfg = 5;
    response_gap_cfg   = 2;
    cpu_read(32'h0000_002c, 1'b1, 1'b1);
    check_counts(1, 0, 1, 1, 4, "TEST 5 stalled refill");
    if(last_refill_addr !== 32'h0000_0020) begin
        $display("[ERROR] TEST 5 line base expected=00000020 got=%08h",
                 last_refill_addr);
        errors = errors + 1;
    end
    $display("[PASS] I-cache test 5 - request/refill backpressure");

    // TEST 6: a deterministic mix with exact final accounting.
    reset_test();
    cpu_read(32'h0000_0000, 1'b1, 1'b0); // miss
    cpu_read(32'h0000_0004, 1'b0, 1'b0); // hit
    cpu_read(32'h0000_0010, 1'b1, 1'b0); // miss
    cpu_read(32'h0000_0014, 1'b0, 1'b0); // hit
    cpu_read(32'h0000_0400, 1'b1, 1'b0); // conflict miss
    cpu_read(32'h0000_0004, 1'b1, 1'b0); // replaced line miss
    cpu_read(32'h0000_0020, 1'b1, 1'b0); // miss
    cpu_read(32'h0000_0020, 1'b0, 1'b0); // hit
    check_counts(8, 3, 5, 5, 20, "TEST 6 exact accounting");
    $display("[PASS] I-cache test 6 - exact counter accounting");

    // TEST 7: issue each next request immediately after the prior response.
    reset_test();
    cpu_read(32'h0000_0000, 1'b1, 1'b0);
    cpu_read(32'h0000_0004, 1'b0, 1'b0);
    cpu_read(32'h0000_0008, 1'b0, 1'b0);
    check_counts(3, 2, 1, 1, 4, "TEST 7 back-to-back requests");
    $display("[PASS] I-cache test 7 - back-to-back requests");

    $display("----- I-CACHE SUMMARY -----");
    $display("Final access/hit/miss = %0d/%0d/%0d",
             access_count, hit_count, miss_count);
    $display("Final refill req/beats = %0d/%0d",
             refill_request_count, refill_beats_total);

    if(errors != 0)
        $fatal(1, "I-cache test failed with %0d error(s)", errors);

    $display("[PASS] Direct-mapped 4-word-line I-cache: all 7 tests passed");
    $finish;
end

endmodule
