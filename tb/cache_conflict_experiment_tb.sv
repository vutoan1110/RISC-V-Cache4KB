`timescale 1ns/1ps
// Deterministic mechanism experiment. This is intentionally an I-cache-level test:
// it isolates cache organisation while keeping the backend and line size fixed.
module tb_cache_conflict_experiment #(
    parameter integer CACHE_CONFIG = 0
);
logic clk=0, reset_n=0;
always #5 clk=~clk;
logic req_valid; logic [31:0] req_addr;
wire req_ready, rsp_valid; wire [31:0] rsp_data; wire rsp_error;
wire refill_req_valid; wire [31:0] refill_req_addr; wire refill_req_ready;
wire refill_rsp_valid; wire [31:0] refill_rsp_data; wire refill_rsp_last, refill_rsp_error;
wire [31:0] access_count, hit_count, miss_count;
wire [31:0] main_hit_count, victim_hit_count, true_miss_count;
integer ar_delay=0, r_gap=0, read_txns, write_txns;
integer cycles, start_cycles, pattern, repetitions, i;

icache #(.LINE_COUNT(64), .CACHE_CONFIG(CACHE_CONFIG), .VICTIM_ENTRIES(4)) dut (
 .clk(clk), .reset_n(reset_n), .req_valid(req_valid), .req_addr(req_addr),
 .req_ready(req_ready), .rsp_valid(rsp_valid), .rsp_data(rsp_data), .rsp_error(rsp_error),
 .refill_req_valid(refill_req_valid), .refill_req_addr(refill_req_addr),
 .refill_req_ready(refill_req_ready), .refill_rsp_valid(refill_rsp_valid),
 .refill_rsp_data(refill_rsp_data), .refill_rsp_last(refill_rsp_last),
 .refill_rsp_error(refill_rsp_error), .access_count(access_count),
 .hit_count(hit_count), .miss_count(miss_count), .main_hit_count(main_hit_count),
 .victim_hit_count(victim_hit_count), .true_miss_count(true_miss_count),
 .access_event(), .hit_event(), .miss_event(), .main_hit_event(),
 .victim_hit_event(), .true_miss_event());

cache_backend_model backend (
 .clk(clk), .reset_n(reset_n), .refill_req_valid(refill_req_valid),
 .refill_req_addr(refill_req_addr), .refill_req_ready(refill_req_ready),
 .refill_rsp_valid(refill_rsp_valid), .refill_rsp_data(refill_rsp_data),
 .refill_rsp_last(refill_rsp_last), .refill_rsp_error(refill_rsp_error),
 .mem_wr_valid(1'b0), .mem_wr_addr(32'b0), .mem_wr_data(32'b0),
 .mem_wr_strb(4'b0), .mem_wr_ready(), .mem_wr_rsp_valid(), .mem_wr_rsp_error(),
 .ar_delay_cfg(ar_delay), .r_gap_cfg(r_gap), .read_txn_count(read_txns),
 .write_txn_count(write_txns));

always @(posedge clk) if (reset_n) cycles <= cycles + 1;

task automatic fetch(input [31:0] address);
 integer guard; reg [31:0] expected;
 begin
  expected=backend.mem[address[15:2]]; guard=0;
  while(!req_ready) begin @(posedge clk); if(guard++>500) $fatal(1,"request timeout"); end
  req_addr=address; req_valid=1; @(posedge clk); #1; req_valid=0; guard=0;
  while(!rsp_valid) begin @(posedge clk); #1; if(guard++>800) $fatal(1,"response timeout"); end
  if(rsp_error || rsp_data!==expected) $fatal(1,"data mismatch at %08h",address);
  @(posedge clk); #1;
 end
endtask

task automatic check_expected(input integer n_accesses);
 integer expected_miss, expected_main, expected_victim;
 begin
  expected_miss=0; expected_main=0; expected_victim=0;
  if(pattern==2) begin
   case(CACHE_CONFIG)
    0: expected_miss=n_accesses;
    1: begin expected_miss=2; expected_main=n_accesses-2; end
    2: begin expected_miss=2; expected_victim=n_accesses-2; end
   endcase
  end else begin
   case(CACHE_CONFIG)
    0: expected_miss=n_accesses;
    1: expected_miss=n_accesses;
    2: begin expected_miss=3; expected_victim=n_accesses-3; end
   endcase
  end
  if(access_count!=n_accesses || main_hit_count!=expected_main ||
     victim_hit_count!=expected_victim || true_miss_count!=expected_miss ||
     read_txns!=expected_miss || write_txns!=0)
    $fatal(1,"expected-count failure cfg=%0d pattern=%0d a=%0d main=%0d victim=%0d miss=%0d axi=%0d",
      CACHE_CONFIG,pattern,access_count,main_hit_count,victim_hit_count,true_miss_count,read_txns);
  if(access_count!==(main_hit_count+victim_hit_count+true_miss_count) ||
     access_count!==(hit_count+miss_count))
    $fatal(1,"exclusive accounting invariant failed");
 end
endtask

initial begin
 req_valid=0; req_addr=0; cycles=0;
 if(!$value$plusargs("pattern=%d",pattern)) pattern=2;
 if(!$value$plusargs("repetitions=%d",repetitions)) repetitions=16;
 if((pattern!=2 && pattern!=3) || repetitions<1) $fatal(1,"bad plusargs");
 repeat(3) @(posedge clk); reset_n=1; repeat(2) @(posedge clk); #1;
 start_cycles=cycles;
 for(i=0;i<repetitions;i=i+1) begin
  fetch(32'h0000_0000); fetch(32'h0000_0400);
  if(pattern==3) fetch(32'h0000_0800);
 end
 check_expected(pattern*repetitions);
 $display("CACHE_CONFLICT config=%0d pattern=AB%0s repetitions=%0d accesses=%0d main_hits=%0d victim_hits=%0d true_misses=%0d axi_reads=%0d cycles=%0d invariant_pass=1 result_pass=1",
   CACHE_CONFIG,(pattern==3)?"C":"",repetitions,access_count,main_hit_count,
   victim_hit_count,true_miss_count,read_txns,cycles-start_cycles);
 $display("[PASS] Deterministic cache-conflict experiment");
 $finish;
end
endmodule
