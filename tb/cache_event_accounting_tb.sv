`timescale 1ns/1ps

module tb_cache_event_accounting;
reg clk;
reg reset_n;

reg i_req_valid;
reg [31:0] i_req_addr;
wire i_req_ready;
wire i_rsp_valid;
wire [31:0] i_rsp_data;
wire i_rsp_error;
wire i_refill_req_valid;
wire [31:0] i_refill_req_addr;
reg i_refill_req_ready;
reg i_refill_rsp_valid;
reg [31:0] i_refill_rsp_data;
reg i_refill_rsp_last;
reg i_refill_rsp_error;
wire [31:0] i_access_count, i_hit_count, i_miss_count;
wire i_access_event, i_hit_event, i_miss_event;

reg d_req_valid;
reg d_req_write;
reg [31:0] d_req_addr;
reg [31:0] d_req_wdata;
reg [3:0] d_req_wstrb;
wire d_req_ready;
wire d_rsp_valid;
wire [31:0] d_rsp_rdata;
wire d_rsp_error;
wire d_refill_req_valid;
wire [31:0] d_refill_req_addr;
reg d_refill_req_ready;
reg d_refill_rsp_valid;
reg [31:0] d_refill_rsp_data;
reg d_refill_rsp_last;
reg d_refill_rsp_error;
wire d_mem_wr_valid;
wire [31:0] d_mem_wr_addr;
wire [31:0] d_mem_wr_data;
wire [3:0] d_mem_wr_strb;
reg d_mem_wr_ready;
reg d_mem_wr_rsp_valid;
reg d_mem_wr_rsp_error;
wire [31:0] d_access_count, d_read_count, d_write_count;
wire [31:0] d_hit_count, d_miss_count;
wire [31:0] d_read_hit_count, d_read_miss_count;
wire [31:0] d_write_hit_count, d_write_miss_count;
wire d_read_access_event, d_read_hit_event, d_read_miss_event;
wire d_write_access_event, d_write_hit_event, d_write_miss_event;

integer i_access_pulses, i_hit_pulses, i_miss_pulses;
integer d_read_access_pulses, d_read_hit_pulses, d_read_miss_pulses;
integer d_write_access_pulses, d_write_hit_pulses, d_write_miss_pulses;
integer beat;

icache #(.LINE_COUNT(8)) u_icache (
    .clk(clk), .reset_n(reset_n),
    .req_valid(i_req_valid), .req_addr(i_req_addr), .req_ready(i_req_ready),
    .rsp_valid(i_rsp_valid), .rsp_data(i_rsp_data), .rsp_error(i_rsp_error),
    .refill_req_valid(i_refill_req_valid), .refill_req_addr(i_refill_req_addr),
    .refill_req_ready(i_refill_req_ready), .refill_rsp_valid(i_refill_rsp_valid),
    .refill_rsp_data(i_refill_rsp_data), .refill_rsp_last(i_refill_rsp_last),
    .refill_rsp_error(i_refill_rsp_error),
    .access_count(i_access_count), .hit_count(i_hit_count), .miss_count(i_miss_count),
    .main_hit_count(), .victim_hit_count(), .true_miss_count(),
    .access_event(i_access_event), .hit_event(i_hit_event), .miss_event(i_miss_event),
    .main_hit_event(), .victim_hit_event(), .true_miss_event()
);

dcache #(.LINE_COUNT(8)) u_dcache (
    .clk(clk), .reset_n(reset_n),
    .req_valid(d_req_valid), .req_write(d_req_write), .req_addr(d_req_addr),
    .req_wdata(d_req_wdata), .req_wstrb(d_req_wstrb), .req_ready(d_req_ready),
    .rsp_valid(d_rsp_valid), .rsp_rdata(d_rsp_rdata), .rsp_error(d_rsp_error),
    .refill_req_valid(d_refill_req_valid), .refill_req_addr(d_refill_req_addr),
    .refill_req_ready(d_refill_req_ready), .refill_rsp_valid(d_refill_rsp_valid),
    .refill_rsp_data(d_refill_rsp_data), .refill_rsp_last(d_refill_rsp_last),
    .refill_rsp_error(d_refill_rsp_error),
    .mem_wr_valid(d_mem_wr_valid), .mem_wr_addr(d_mem_wr_addr),
    .mem_wr_data(d_mem_wr_data), .mem_wr_strb(d_mem_wr_strb),
    .mem_wr_ready(d_mem_wr_ready), .mem_wr_rsp_valid(d_mem_wr_rsp_valid),
    .mem_wr_rsp_error(d_mem_wr_rsp_error),
    .access_count(d_access_count), .read_count(d_read_count),
    .write_count(d_write_count), .hit_count(d_hit_count), .miss_count(d_miss_count),
    .read_hit_count(d_read_hit_count), .read_miss_count(d_read_miss_count),
    .write_hit_count(d_write_hit_count), .write_miss_count(d_write_miss_count),
    .main_hit_count(), .victim_hit_count(), .true_miss_count(),
    .read_access_event(d_read_access_event), .read_hit_event(d_read_hit_event),
    .read_miss_event(d_read_miss_event), .write_access_event(d_write_access_event),
    .write_hit_event(d_write_hit_event), .write_miss_event(d_write_miss_event),
    .main_hit_event(), .victim_hit_event(), .true_miss_event()
);

always #5 clk = ~clk;

always @(posedge clk) begin
    if(!reset_n) begin
        i_access_pulses = 0; i_hit_pulses = 0; i_miss_pulses = 0;
        d_read_access_pulses = 0; d_read_hit_pulses = 0; d_read_miss_pulses = 0;
        d_write_access_pulses = 0; d_write_hit_pulses = 0; d_write_miss_pulses = 0;
    end
    else begin
        if(i_access_event) i_access_pulses = i_access_pulses + 1;
        if(i_hit_event) i_hit_pulses = i_hit_pulses + 1;
        if(i_miss_event) i_miss_pulses = i_miss_pulses + 1;
        if(d_read_access_event) d_read_access_pulses = d_read_access_pulses + 1;
        if(d_read_hit_event) d_read_hit_pulses = d_read_hit_pulses + 1;
        if(d_read_miss_event) d_read_miss_pulses = d_read_miss_pulses + 1;
        if(d_write_access_event) d_write_access_pulses = d_write_access_pulses + 1;
        if(d_write_hit_event) d_write_hit_pulses = d_write_hit_pulses + 1;
        if(d_write_miss_event) d_write_miss_pulses = d_write_miss_pulses + 1;

        if(i_refill_rsp_valid && (i_access_event || i_hit_event || i_miss_event))
            $fatal(1, "I-cache refill beat generated a CPU cache event");
        if(d_refill_rsp_valid &&
           (d_read_access_event || d_read_hit_event || d_read_miss_event ||
            d_write_access_event || d_write_hit_event || d_write_miss_event))
            $fatal(1, "D-cache refill beat generated a CPU cache event");
    end
end

task automatic issue_i(input [31:0] addr);
begin
    @(negedge clk); i_req_addr = addr; i_req_valid = 1;
    while(!i_req_ready) @(negedge clk);
    @(posedge clk);
    @(negedge clk); i_req_valid = 0;
end
endtask

task automatic fill_i(input [31:0] base_data);
begin
    wait(i_refill_req_valid);
    @(posedge clk);
    for(beat = 0; beat < 4; beat = beat + 1) begin
        @(negedge clk);
        i_refill_rsp_valid = 1;
        i_refill_rsp_data = base_data + beat;
        i_refill_rsp_last = (beat == 3);
        @(posedge clk);
    end
    @(negedge clk);
    i_refill_rsp_valid = 0; i_refill_rsp_last = 0;
    wait(i_rsp_valid); @(posedge clk);
end
endtask

task automatic issue_d(input wr, input [31:0] addr,
                       input [31:0] data, input [3:0] strb);
begin
    @(negedge clk);
    d_req_write = wr; d_req_addr = addr; d_req_wdata = data;
    d_req_wstrb = strb; d_req_valid = 1;
    while(!d_req_ready) @(negedge clk);
    @(posedge clk);
    @(negedge clk); d_req_valid = 0;
end
endtask

task automatic fill_d(input [31:0] base_data);
begin
    wait(d_refill_req_valid);
    @(posedge clk);
    for(beat = 0; beat < 4; beat = beat + 1) begin
        @(negedge clk);
        d_refill_rsp_valid = 1;
        d_refill_rsp_data = base_data + beat;
        d_refill_rsp_last = (beat == 3);
        @(posedge clk);
    end
    @(negedge clk);
    d_refill_rsp_valid = 0; d_refill_rsp_last = 0;
    wait(d_rsp_valid); @(posedge clk);
end
endtask

task automatic complete_store;
begin
    wait(d_mem_wr_valid);
    @(negedge clk); d_mem_wr_rsp_valid = 1;
    @(posedge clk);
    @(negedge clk); d_mem_wr_rsp_valid = 0;
    wait(d_rsp_valid); @(posedge clk);
end
endtask

task automatic check_eq(input integer got, input integer expected,
                        input string label_text);
begin
    if(got != expected)
        $fatal(1, "%s expected %0d got %0d", label_text, expected, got);
end
endtask

initial begin
    clk = 0; reset_n = 0;
    i_req_valid = 0; i_req_addr = 0; i_refill_req_ready = 1;
    i_refill_rsp_valid = 0; i_refill_rsp_data = 0; i_refill_rsp_last = 0;
    i_refill_rsp_error = 0;
    d_req_valid = 0; d_req_write = 0; d_req_addr = 0; d_req_wdata = 0;
    d_req_wstrb = 0; d_refill_req_ready = 1; d_refill_rsp_valid = 0;
    d_refill_rsp_data = 0; d_refill_rsp_last = 0; d_refill_rsp_error = 0;
    d_mem_wr_ready = 1; d_mem_wr_rsp_valid = 0; d_mem_wr_rsp_error = 0;

    repeat(3) @(posedge clk);
    @(negedge clk); reset_n = 1;

    $display("[TEST 5] I-cache CPU events exclude four refill beats");
    issue_i(32'h0000_002C);
    fill_i(32'h1000_0000);
    issue_i(32'h0000_002C);
    wait(i_rsp_valid); @(posedge clk);
    check_eq(i_access_pulses, 2, "I access pulses");
    check_eq(i_hit_pulses, 1, "I hit pulses");
    check_eq(i_miss_pulses, 1, "I miss pulses");
    if(i_access_count !== (i_hit_count + i_miss_count))
        $fatal(1, "I-cache legacy event invariant failed");

    $display("[TEST 6] D-cache CPU read/write events exclude refill/write traffic");
    issue_d(0, 32'h0000_0108, 0, 0);
    fill_d(32'h2000_0000);
    issue_d(0, 32'h0000_0108, 0, 0);
    wait(d_rsp_valid); @(posedge clk);
    issue_d(1, 32'h0000_0108, 32'hCAFE_BABE, 4'hF);
    complete_store();

    check_eq(d_read_access_pulses, 2, "D read access pulses");
    check_eq(d_read_hit_pulses, 1, "D read hit pulses");
    check_eq(d_read_miss_pulses, 1, "D read miss pulses");
    check_eq(d_write_access_pulses, 1, "D write access pulses");
    check_eq(d_write_hit_pulses, 1, "D write hit pulses");
    check_eq(d_write_miss_pulses, 0, "D write miss pulses");
    if(d_read_count !== (d_read_hit_count + d_read_miss_count))
        $fatal(1, "D-cache read invariant failed");
    if(d_write_count !== (d_write_hit_count + d_write_miss_count))
        $fatal(1, "D-cache write invariant failed");

    $display("[PASS] Cache event source/refill exclusion tests");
    $finish;
end

initial begin
    #10000;
    $fatal(1, "Cache event test timeout");
end

endmodule
