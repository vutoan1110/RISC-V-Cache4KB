`timescale 1ns/1ps
module tb_set_associative_cache;
logic clk=0,reset_n=0;
always #5 clk=~clk;
logic req_valid; logic [31:0] req_addr; wire req_ready,rsp_valid; wire [31:0] rsp_data; wire rsp_error;
wire rr_valid; wire [31:0] rr_addr; wire rr_ready,rd_valid; wire [31:0] rd_data; wire rd_last,rd_error;
wire [31:0] access_count,hit_count,miss_count,main_hit_count,victim_hit_count,true_miss_count;
integer ar_delay_cfg=0,r_gap_cfg=0,read_txns,write_txns;

icache #(.LINE_COUNT(64),.CACHE_CONFIG(1),.VICTIM_ENTRIES(4)) dut(
 .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_addr(req_addr),.req_ready(req_ready),
 .rsp_valid(rsp_valid),.rsp_data(rsp_data),.rsp_error(rsp_error),
 .refill_req_valid(rr_valid),.refill_req_addr(rr_addr),.refill_req_ready(rr_ready),
 .refill_rsp_valid(rd_valid),.refill_rsp_data(rd_data),.refill_rsp_last(rd_last),
 .refill_rsp_error(rd_error),.access_count(access_count),.hit_count(hit_count),.miss_count(miss_count),
 .main_hit_count(main_hit_count),.victim_hit_count(victim_hit_count),.true_miss_count(true_miss_count),
 .access_event(),.hit_event(),.miss_event(),.main_hit_event(),.victim_hit_event(),
 .true_miss_event());
cache_backend_model be(
 .clk(clk),.reset_n(reset_n),.refill_req_valid(rr_valid),.refill_req_addr(rr_addr),
 .refill_req_ready(rr_ready),.refill_rsp_valid(rd_valid),.refill_rsp_data(rd_data),
 .refill_rsp_last(rd_last),.refill_rsp_error(rd_error),.mem_wr_valid(1'b0),.mem_wr_addr(0),
 .mem_wr_data(0),.mem_wr_strb(4'b0),.mem_wr_ready(),.mem_wr_rsp_valid(),.mem_wr_rsp_error(),
 .ar_delay_cfg(ar_delay_cfg),.r_gap_cfg(r_gap_cfg),.read_txn_count(read_txns),.write_txn_count(write_txns));

task automatic read_addr(input [31:0] a);
 integer guard; reg [31:0] exp;
 begin
  exp=be.mem[a[15:2]]; guard=0; while(!req_ready) begin @(posedge clk); if(guard++>200)$fatal(1,"ready timeout"); end
  req_addr=a;req_valid=1;@(posedge clk);#1;req_valid=0;
  guard=0;while(!rsp_valid)begin @(posedge clk);#1;if(guard++>300)$fatal(1,"response timeout %h",a);end
  if(rsp_error||rsp_data!==exp)$fatal(1,"read %h got %h expected %h",a,rsp_data,exp);
  @(posedge clk);#1;
 end
endtask

task automatic do_reset;
 begin req_valid=0;req_addr=0;reset_n=0;repeat(3)@(posedge clk);reset_n=1;repeat(2)@(posedge clk);#1;end
endtask

initial begin
 do_reset();
 if((64*1*16)!=1024 || (32*2*16)!=1024)$fatal(1,"capacity fairness arithmetic failed");
 read_addr(32'h0); read_addr(32'h400); read_addr(32'h0); read_addr(32'h400);
 if(read_txns!=2||access_count!=4||main_hit_count!=2||victim_hit_count!=0||true_miss_count!=2)
  $fatal(1,"SA2 A/B counters rd=%0d access=%0d main=%0d vc=%0d miss=%0d",read_txns,access_count,main_hit_count,victim_hit_count,true_miss_count);
 if(!(dut.g_dse.u_core.valid_way0[0]&&dut.g_dse.u_core.valid_way1[0]))
  $fatal(1,"SA2 invalid-way priority did not populate both ways");
 $display("[PASS] SA2 A/B coexistence and invalid-way priority");

 do_reset();
 read_addr(32'h0); read_addr(32'h400); read_addr(32'h800);
 if(dut.g_dse.u_core.tag_way0[0]!==23'h4 || dut.g_dse.u_core.tag_way1[0]!==23'h2)
  $fatal(1,"SA2 third conflict replacement state wrong w0=%h w1=%h",dut.g_dse.u_core.tag_way0[0],dut.g_dse.u_core.tag_way1[0]);
 read_addr(32'h400);
 if(read_txns!=3)$fatal(1,"resident B should hit after C replacement");
 read_addr(32'h0);
 if(read_txns!=4)$fatal(1,"evicted A should miss after C replacement");
 $display("[PASS] SA2 one-bit replacement and third conflict");

 do_reset(); ar_delay_cfg=3; r_gap_cfg=2;
 read_addr(32'h100); read_addr(32'h100);
 if(read_txns!=1||true_miss_count!=1||main_hit_count!=1||access_count!=2)
  $fatal(1,"SA2 backpressure caused lost request/double accounting");
 $display("[PASS] SA2 AXI-style backpressure and no double accounting");
 $display("[PASS] SA2 cache regression");
 $finish;
end
endmodule
