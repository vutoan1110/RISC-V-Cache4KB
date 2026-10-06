`timescale 1ns/1ps
module tb_cache_configuration #(
    parameter integer CACHE_CONFIG=0,
    parameter integer LINE_COUNT=64,
    parameter integer LINE_WORDS=4,
    // R16 (review M1): 1 = the DSE / N-way core answers a main-array hit in ST_LOOKUP. Every check below is
    // latency-independent (fetch waits for rsp_valid), so it must hold unchanged.
    parameter integer FAST_HIT=0
);
// Two addresses collide in the main array when they differ by one way's worth
// of storage. Deriving that from the geometry keeps the test valid at any line
// size instead of pinning it to the 1-KiB default.
localparam integer LINE_BYTES     = LINE_WORDS * 4;
localparam integer WAY_COUNT      = (CACHE_CONFIG == 1) ? 2 : 1;
localparam integer CAPACITY_BYTES = LINE_COUNT * LINE_BYTES;
localparam [31:0]  CONFLICT_STRIDE = 32'(CAPACITY_BYTES);
logic clk=0,reset_n=0;always #5 clk=~clk;
logic req_valid;logic[31:0]req_addr;wire req_ready,rsp_valid;wire[31:0]rsp_data;wire rsp_error;
wire rr_valid;wire[31:0]rr_addr;wire rr_ready,rd_valid;wire[31:0]rd_data;wire rd_last,rd_error;
wire[31:0]access_count,hit_count,miss_count,main_hit_count,victim_hit_count,true_miss_count;
integer ar_delay=0,r_gap=0,read_txns,write_txns;
integer last_lat;   // cycles fetch() waited after the accepting edge for rsp_valid (R16 latency check)
logic[31:0]decode_addr;wire sel_cacheable,sel_mmio,sel_uart,sel_display,sel_timer,sel_sysmon,sel_unmapped;

icache #(.LINE_COUNT(LINE_COUNT),.CACHE_CONFIG(CACHE_CONFIG),
        .VICTIM_ENTRIES(4),.LINE_WORDS(LINE_WORDS),.FAST_HIT(FAST_HIT)) dut(
 .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_addr(req_addr),.req_ready(req_ready),
 .rsp_valid(rsp_valid),.rsp_data(rsp_data),.rsp_error(rsp_error),
 .refill_req_valid(rr_valid),.refill_req_addr(rr_addr),.refill_req_ready(rr_ready),
 .refill_rsp_valid(rd_valid),.refill_rsp_data(rd_data),.refill_rsp_last(rd_last),
 .refill_rsp_error(rd_error),.access_count(access_count),.hit_count(hit_count),.miss_count(miss_count),
 .main_hit_count(main_hit_count),.victim_hit_count(victim_hit_count),.true_miss_count(true_miss_count),
 .access_event(),.hit_event(),.miss_event(),.main_hit_event(),.victim_hit_event(),
 .true_miss_event());
cache_backend_model #(.LINE_WORDS(LINE_WORDS)) be(
 .clk(clk),.reset_n(reset_n),.refill_req_valid(rr_valid),.refill_req_addr(rr_addr),
 .refill_req_ready(rr_ready),.refill_rsp_valid(rd_valid),.refill_rsp_data(rd_data),
 .refill_rsp_last(rd_last),.refill_rsp_error(rd_error),.mem_wr_valid(1'b0),.mem_wr_addr(0),
 .mem_wr_data(0),.mem_wr_strb(4'b0),.mem_wr_ready(),.mem_wr_rsp_valid(),.mem_wr_rsp_error(),
 .ar_delay_cfg(ar_delay),.r_gap_cfg(r_gap),.read_txn_count(read_txns),.write_txn_count(write_txns));
soc_address_decoder dec(.addr(decode_addr),.sel_cacheable(sel_cacheable),.sel_mmio(sel_mmio),
 .sel_uart(sel_uart),.sel_display(sel_display),.sel_timer(sel_timer),.sel_sysmon(sel_sysmon),
 .sel_unmapped(sel_unmapped));

task automatic fetch(input[31:0]a);
 integer g;reg[31:0]e;
 begin e=be.mem[a[15:2]];g=0;while(!req_ready)begin@(posedge clk);if(g++>500)$fatal(1,"ready timeout");end
  req_addr=a;req_valid=1;@(posedge clk);#1;req_valid=0;g=0;
  while(!rsp_valid)begin@(posedge clk);#1;if(g++>800)$fatal(1,"response timeout");end
  last_lat=g;
  if(rsp_error||rsp_data!==e)$fatal(1,"architecture mismatch cfg=%0d addr=%h got=%h exp=%h",CACHE_CONFIG,a,rsp_data,e);
  @(posedge clk);#1;end
endtask

task automatic fetch_fast(input[31:0]a);
 integer g;reg[31:0]e;
 begin e=be.mem[a[15:2]];g=0;while(!req_ready)begin@(posedge clk);if(g++>500)$fatal(1,"ready timeout");end
  req_addr=a;req_valid=1;#1;
  if(!req_ready||!rsp_valid)$fatal(1,"CACHE_CONFIG=%0d main hit did not respond in request cycle",CACHE_CONFIG);
  if(rsp_error||rsp_data!==e)$fatal(1,"fast-hit mismatch cfg=%0d addr=%h got=%h exp=%h",CACHE_CONFIG,a,rsp_data,e);
  @(posedge clk);#1;req_valid=0;
  @(posedge clk);#1;
 end
endtask

integer before_access,before_main,before_reads;
initial begin
 req_valid=0;req_addr=0;decode_addr=0;repeat(3)@(posedge clk);reset_n=1;repeat(2)@(posedge clk);#1;
 // Every organization must hold the same number of bytes: the whole point
 // of the comparison is that only the mapping differs.
 if((LINE_COUNT/WAY_COUNT)*WAY_COUNT*LINE_BYTES != CAPACITY_BYTES)
   $fatal(1,"capacity fairness failed cfg=%0d",CACHE_CONFIG);
 fetch(0);fetch(CONFLICT_STRIDE);fetch(0);fetch(CONFLICT_STRIDE);
 case(CACHE_CONFIG)
  0: if(read_txns!=4||main_hit_count!=0||victim_hit_count!=0||true_miss_count!=4)
      $fatal(1,"DM must thrash A/B");
  1: if(read_txns!=2||main_hit_count!=2||victim_hit_count!=0||true_miss_count!=2)
      $fatal(1,"SA2 must retain A/B");
  2: if(read_txns!=2||main_hit_count!=0||victim_hit_count!=2||true_miss_count!=2)
      $fatal(1,"VC4 must rescue A/B");
  // CACHE_CONFIG 3 is the ablation point: direct-mapped on the ten-state DSE
  // core, with no readable victim buffer. It must therefore thrash exactly as
  // CACHE_CONFIG 0 does. A stray second way would show up here as main hits,
  // and a victim buffer that is still live would show up as victim hits.
  3: if(read_txns!=4||main_hit_count!=0||victim_hit_count!=0||true_miss_count!=4)
      $fatal(1,"DM-DSE must thrash A/B exactly as DM does");
  default:$fatal(1,"invalid CACHE_CONFIG");
 endcase
 // R16: for SA2 the last fetch above is a main-array hit that misses the L0 (A and B share an L0 slot, since
 // LINE_COUNT is a multiple of the 8 L0 entries). The original DSE core answers it one cycle after the accepting
 // edge (ST_HIT_RESP); FAST_HIT answers in ST_LOOKUP, i.e. one cycle earlier.
 if(CACHE_CONFIG==1 && last_lat!==(FAST_HIT ? 0 : 1))
   $fatal(1,"SA2 main-hit latency %0d, expected %0d (FAST_HIT=%0d)",last_lat,FAST_HIT ? 0 : 1,FAST_HIT);
 before_access=access_count;before_main=main_hit_count;before_reads=read_txns;
 fetch_fast(CONFLICT_STRIDE);
 if(access_count!=before_access+1||main_hit_count!=before_main+1||
    read_txns!=before_reads)
   $fatal(1,"fast main hit accounting/refill failure cfg=%0d",CACHE_CONFIG);
 $display("[PASS] CACHE_CONFIG=%0d FAST_HIT=%0d request-cycle main-cache hit",CACHE_CONFIG,FAST_HIT);
 if(access_count!==(main_hit_count+victim_hit_count+true_miss_count)||
    access_count!==(hit_count+miss_count))$fatal(1,"exclusive cache accounting failed");
 before_access=access_count;decode_addr=32'h4000_0034;#1;
 if(!sel_mmio||sel_cacheable)$fatal(1,"MMIO decode/bypass classification wrong");
 repeat(4)@(posedge clk);
 if(access_count!=before_access)$fatal(1,"MMIO changed cache counters");
 $display("[PASS] CACHE_CONFIG=%0d conflict behavior, architecture, accounting, MMIO bypass",CACHE_CONFIG);
 $finish;
end
endmodule
