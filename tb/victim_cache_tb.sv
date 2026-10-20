`timescale 1ns/1ps
module tb_victim_cache;
logic clk=0,reset_n=0; always #5 clk=~clk;
logic i_valid;logic[31:0]i_addr;wire i_ready,i_rsp_valid;wire[31:0]i_rsp_data;wire i_rsp_error;
wire irr_valid;wire[31:0]irr_addr;wire irr_ready,ird_valid;wire[31:0]ird_data;wire ird_last,ird_error;
wire[31:0]ia,ih,im,imh,ivh,itm;integer iar=0,igap=0,irt,iwt;

logic d_valid,d_write;logic[31:0]d_addr,d_wdata;logic[3:0]d_wstrb;wire d_ready,d_rsp_valid;
wire[31:0]d_rsp_data;wire d_rsp_error,drr_valid;wire[31:0]drr_addr;wire drr_ready,drd_valid;
wire[31:0]drd_data;wire drd_last,drd_error,dw_valid;wire[31:0]dw_addr,dw_data;wire[3:0]dw_strb;
wire dw_ready,dw_rsp_valid,dw_rsp_error;wire[31:0]da,dr,dw,dh,dm,drh,drm,dwh,dwm,dmh,dvh,dtm;
integer dar=0,dgap=0,drt,dwt;

icache #(.LINE_COUNT(64),.CACHE_CONFIG(2),.VICTIM_ENTRIES(4)) idut(
 .clk(clk),.reset_n(reset_n),.req_valid(i_valid),.req_addr(i_addr),.req_ready(i_ready),
 .rsp_valid(i_rsp_valid),.rsp_data(i_rsp_data),.rsp_error(i_rsp_error),
 .refill_req_valid(irr_valid),.refill_req_addr(irr_addr),.refill_req_ready(irr_ready),
 .refill_rsp_valid(ird_valid),.refill_rsp_data(ird_data),.refill_rsp_last(ird_last),
 .refill_rsp_error(ird_error),.access_count(ia),.hit_count(ih),.miss_count(im),
 .main_hit_count(imh),.victim_hit_count(ivh),.true_miss_count(itm),
 .access_event(),.hit_event(),.miss_event(),.main_hit_event(),.victim_hit_event(),
 .true_miss_event());
cache_backend_model ibe(
 .clk(clk),.reset_n(reset_n),.refill_req_valid(irr_valid),.refill_req_addr(irr_addr),
 .refill_req_ready(irr_ready),.refill_rsp_valid(ird_valid),.refill_rsp_data(ird_data),
 .refill_rsp_last(ird_last),.refill_rsp_error(ird_error),.mem_wr_valid(1'b0),.mem_wr_addr(0),
 .mem_wr_data(0),.mem_wr_strb(4'b0),.mem_wr_ready(),.mem_wr_rsp_valid(),.mem_wr_rsp_error(),
 .ar_delay_cfg(iar),.r_gap_cfg(igap),.read_txn_count(irt),.write_txn_count(iwt));

dcache #(.LINE_COUNT(64),.CACHE_CONFIG(2),.VICTIM_ENTRIES(4)) ddut(
 .clk(clk),.reset_n(reset_n),.req_valid(d_valid),.req_write(d_write),.req_addr(d_addr),
 .req_wdata(d_wdata),.req_wstrb(d_wstrb),.req_ready(d_ready),.rsp_valid(d_rsp_valid),
 .rsp_rdata(d_rsp_data),.rsp_error(d_rsp_error),.refill_req_valid(drr_valid),
 .refill_req_addr(drr_addr),.refill_req_ready(drr_ready),.refill_rsp_valid(drd_valid),
 .refill_rsp_data(drd_data),.refill_rsp_last(drd_last),.refill_rsp_error(drd_error),
 .mem_wr_valid(dw_valid),.mem_wr_addr(dw_addr),.mem_wr_data(dw_data),.mem_wr_strb(dw_strb),
 .mem_wr_ready(dw_ready),.mem_wr_rsp_valid(dw_rsp_valid),.mem_wr_rsp_error(dw_rsp_error),
 .access_count(da),.read_count(dr),.write_count(dw),.hit_count(dh),.miss_count(dm),
 .read_hit_count(drh),.read_miss_count(drm),.write_hit_count(dwh),.write_miss_count(dwm),
 .main_hit_count(dmh),.victim_hit_count(dvh),.true_miss_count(dtm),
 .read_access_event(),.read_hit_event(),.read_miss_event(),.write_access_event(),
 .write_hit_event(),.write_miss_event(),.main_hit_event(),.victim_hit_event(),
 .true_miss_event());
cache_backend_model dbe(
 .clk(clk),.reset_n(reset_n),.refill_req_valid(drr_valid),.refill_req_addr(drr_addr),
 .refill_req_ready(drr_ready),.refill_rsp_valid(drd_valid),.refill_rsp_data(drd_data),
 .refill_rsp_last(drd_last),.refill_rsp_error(drd_error),.mem_wr_valid(dw_valid),
 .mem_wr_addr(dw_addr),.mem_wr_data(dw_data),.mem_wr_strb(dw_strb),.mem_wr_ready(dw_ready),
 .mem_wr_rsp_valid(dw_rsp_valid),.mem_wr_rsp_error(dw_rsp_error),.ar_delay_cfg(dar),
 .r_gap_cfg(dgap),.read_txn_count(drt),.write_txn_count(dwt));

task automatic do_reset;
 begin i_valid=0;i_addr=0;d_valid=0;d_write=0;d_addr=0;d_wdata=0;d_wstrb=0;
  reset_n=0;repeat(3)@(posedge clk);reset_n=1;repeat(2)@(posedge clk);#1;end
endtask
task automatic iread(input[31:0]a);
 integer g;reg[31:0]e;
 begin e=ibe.mem[a[15:2]];g=0;while(!i_ready)begin@(posedge clk);if(g++>500)$fatal(1,"I ready timeout");end
  i_addr=a;i_valid=1;@(posedge clk);#1;i_valid=0;g=0;
  while(!i_rsp_valid)begin@(posedge clk);#1;if(g++>800)$fatal(1,"I response timeout %h",a);end
  if(i_rsp_error||i_rsp_data!==e)$fatal(1,"I read %h got %h expected %h",a,i_rsp_data,e);
  @(posedge clk);#1;end
endtask
task automatic dread(input[31:0]a,input[31:0]e);
 integer g;
 begin g=0;while(!d_ready)begin@(posedge clk);if(g++>500)$fatal(1,"D ready timeout");end
  d_addr=a;d_write=0;d_wdata=0;d_wstrb=0;d_valid=1;@(posedge clk);#1;d_valid=0;g=0;
  while(!d_rsp_valid)begin@(posedge clk);#1;if(g++>800)$fatal(1,"D response timeout %h",a);end
  if(d_rsp_error||d_rsp_data!==e)$fatal(1,"D read %h got %h expected %h",a,d_rsp_data,e);
  @(posedge clk);#1;end
endtask
task automatic dstore(input[31:0]a,input[31:0]v,input[3:0]s);
 integer g;
 begin g=0;while(!d_ready)begin@(posedge clk);if(g++>500)$fatal(1,"D ready timeout");end
  d_addr=a;d_write=1;d_wdata=v;d_wstrb=s;d_valid=1;@(posedge clk);#1;d_valid=0;g=0;
  while(!d_rsp_valid)begin@(posedge clk);#1;if(g++>800)$fatal(1,"D store timeout %h",a);end
  if(d_rsp_error)$fatal(1,"D store error %h",a);@(posedge clk);#1;end
endtask

integer before_reads;reg[21:0]saved_tag;reg saved_valid;reg[3:0]saved_vvalid;reg[27:0]saved_vtag0;
initial begin
 do_reset();
 if((64*16)!=1024||(4*16)!=64)$fatal(1,"VC capacity arithmetic failed");
 iread(32'h0);iread(32'h400);iread(32'h0);iread(32'h400);
 if(irt!=2||ia!=4||imh!=0||ivh!=2||itm!=2||ih!=2||im!=2)
  $fatal(1,"VC A/B counters rd=%0d access=%0d main=%0d vc=%0d true=%0d",irt,ia,imh,ivh,itm);
 if(idut.g_dse.u_core.tag_way0[0]!==22'h1||idut.g_dse.u_core.vc_block[0]!==28'h0)
  $fatal(1,"VC exact swap content wrong");
 $display("[PASS] VC4 A/B rescue, exact swap, and no AXI refill on victim hit");

 do_reset();
 iread(0);iread('h400);iread('h800);iread('hc00);iread('h1000);
 if(idut.g_dse.u_core.vc_valid!==4'hf||idut.g_dse.u_core.vc_replace_ptr!==0)
  $fatal(1,"VC invalid-first fill or pointer wrong valid=%b ptr=%0d",idut.g_dse.u_core.vc_valid,idut.g_dse.u_core.vc_replace_ptr);
 iread('h1400);
 if(idut.g_dse.u_core.vc_block[0]!==28'h100||idut.g_dse.u_core.vc_replace_ptr!==1)
  $fatal(1,"VC round-robin replacement wrong block0=%h ptr=%0d",idut.g_dse.u_core.vc_block[0],idut.g_dse.u_core.vc_replace_ptr);
 $display("[PASS] VC4 invalid-first fill and round-robin replacement");

 do_reset();dar=2;dgap=1;
 dread(0,dbe.mem[0]);dread('h400,dbe.mem['h100]);before_reads=drt;
 dstore(1,32'h0000_5500,4'b0010);
 if(drt!=before_reads||dvh!=1||dwt!=1)$fatal(1,"victim store generated refill or wrong counters");
 dread(0,32'h1000_5500);
 dstore(0,32'h0000_00aa,4'b0001);dread(0,32'h1000_55aa);
 dstore(0,32'hbeef_0000,4'b1100);dread(0,32'hbeef_55aa);
 dstore(0,32'hdead_beef,4'b1111);dread(0,32'hdead_beef);
 $display("[PASS] D-cache VC store swap and SB/SH/SW write-through merge");

 before_reads=drt;saved_valid=ddut.g_dse.u_core.valid_way0[0];
 saved_tag=ddut.g_dse.u_core.tag_way0[0];saved_vvalid=ddut.g_dse.u_core.vc_valid;
 saved_vtag0=ddut.g_dse.u_core.vc_block[0];
 dstore('h800,32'h1234_5678,4'hf);
 if(drt!=before_reads||ddut.g_dse.u_core.valid_way0[0]!==saved_valid||
    ddut.g_dse.u_core.tag_way0[0]!==saved_tag||ddut.g_dse.u_core.vc_valid!==saved_vvalid||
    ddut.g_dse.u_core.vc_block[0]!==saved_vtag0)
  $fatal(1,"store true miss changed cache state or issued refill");
 if(dbe.mem['h200]!==32'h1234_5678)$fatal(1,"store true miss did not write backing memory");
 $display("[PASS] D-cache store true miss remains no-write-allocate");
 if(da!==(dh+dm)||da!==(dr+dw)||dh!==(dmh+dvh)||dm!==dtm)
  $fatal(1,"D-cache exclusive accounting invariant failed");
 $display("[PASS] Victim-cache regression");
 $finish;
end
endmodule
