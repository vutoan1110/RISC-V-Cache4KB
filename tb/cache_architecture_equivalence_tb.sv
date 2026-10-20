`timescale 1ns/1ps
// R16 (review M1): FAST_HIT=1 builds SA2 and DM_VC4 with CACHE_FAST_HIT (main-array hits answered in ST_LOOKUP);
// the retirement traces, GPRs and memory must still equal DM's, which has no such parameter.
module tb_cache_architecture_equivalence #(parameter integer FAST_HIT=0);
localparam [31:0] HALT=32'h0000_006f;
logic clk=0,reset_n=0;always #5 clk=~clk;
wire [7:0] led_dm,led_sa,led_vc;

soc_top #(.MEMFILE("verification/directed/directed_isa.hex"),.BRANCH_PREDICT_ENABLE(1),
 .CACHE_CONFIG(0),.VICTIM_ENTRIES(4)) dm(.clk(clk),.reset_n(reset_n),.key1_n(1'b1),.uart_rx(1'b1),
 .uart_tx(),.HEX0(),.HEX1(),.HEX2(),.HEX3(),.HEX4(),.HEX5(),.HEX6(),.HEX7(),.LEDR(led_dm),
 .LCD_DATA(),.LCD_EN(),.LCD_RS(),.LCD_RW(),.LCD_ON(),.LCD_BLON());
soc_top #(.MEMFILE("verification/directed/directed_isa.hex"),.BRANCH_PREDICT_ENABLE(1),
 .CACHE_CONFIG(1),.VICTIM_ENTRIES(4),.CACHE_FAST_HIT(FAST_HIT)) sa(.clk(clk),.reset_n(reset_n),.key1_n(1'b1),.uart_rx(1'b1),
 .uart_tx(),.HEX0(),.HEX1(),.HEX2(),.HEX3(),.HEX4(),.HEX5(),.HEX6(),.HEX7(),.LEDR(led_sa),
 .LCD_DATA(),.LCD_EN(),.LCD_RS(),.LCD_RW(),.LCD_ON(),.LCD_BLON());
soc_top #(.MEMFILE("verification/directed/directed_isa.hex"),.BRANCH_PREDICT_ENABLE(1),
 .CACHE_CONFIG(2),.VICTIM_ENTRIES(4),.CACHE_FAST_HIT(FAST_HIT)) vc(.clk(clk),.reset_n(reset_n),.key1_n(1'b1),.uart_rx(1'b1),
 .uart_tx(),.HEX0(),.HEX1(),.HEX2(),.HEX3(),.HEX4(),.HEX5(),.HEX6(),.HEX7(),.LEDR(led_vc),
 .LCD_DATA(),.LCD_EN(),.LCD_RS(),.LCD_RW(),.LCD_ON(),.LCD_BLON());

logic done_dm=0,done_sa=0,done_vc=0;
integer n_dm=0,n_sa=0,n_vc=0;
logic[31:0] pc_dm[0:2047],pc_sa[0:2047],pc_vc[0:2047];
logic[31:0] ins_dm[0:2047],ins_sa[0:2047],ins_vc[0:2047];
logic[4:0] rd_dm[0:2047],rd_sa[0:2047],rd_vc[0:2047];
logic we_dm[0:2047],we_sa[0:2047],we_vc[0:2047];
logic[31:0] val_dm[0:2047],val_sa[0:2047],val_vc[0:2047];
logic mwe_dm[0:2047],mwe_sa[0:2047],mwe_vc[0:2047];
logic[31:0] ma_dm[0:2047],ma_sa[0:2047],ma_vc[0:2047];
logic[3:0] ms_dm[0:2047],ms_sa[0:2047],ms_vc[0:2047];
logic[31:0] regs_dm[0:31],regs_sa[0:31],regs_vc[0:31];
integer i;
function automatic perf_csr_read(input [31:0] insn);
 begin perf_csr_read=(insn[6:0]==7'b1110011)&&((insn[31:20]==12'hb00)||(insn[31:20]==12'hb02)); end
endfunction

task automatic record_dm;
 begin
  if(dm.retire_instr==HALT)done_dm<=1;else begin
   if(n_dm>=2048)$fatal(1,"DM trace overflow");pc_dm[n_dm]<=dm.retire_pc;ins_dm[n_dm]<=dm.retire_instr;
   rd_dm[n_dm]<=dm.retire_rd_addr;we_dm[n_dm]<=dm.retire_rd_we;val_dm[n_dm]<=dm.retire_rd_wdata;
   mwe_dm[n_dm]<=dm.retire_mem_write;ma_dm[n_dm]<=dm.retire_mem_addr;ms_dm[n_dm]<=dm.retire_mem_wstrb;
   if(dm.retire_rd_we&&!perf_csr_read(dm.retire_instr))regs_dm[dm.retire_rd_addr]<=dm.retire_rd_wdata;n_dm<=n_dm+1;end
 end
endtask
task automatic record_sa;
 begin
  if(sa.retire_instr==HALT)done_sa<=1;else begin
   if(n_sa>=2048)$fatal(1,"SA trace overflow");pc_sa[n_sa]<=sa.retire_pc;ins_sa[n_sa]<=sa.retire_instr;
   rd_sa[n_sa]<=sa.retire_rd_addr;we_sa[n_sa]<=sa.retire_rd_we;val_sa[n_sa]<=sa.retire_rd_wdata;
   mwe_sa[n_sa]<=sa.retire_mem_write;ma_sa[n_sa]<=sa.retire_mem_addr;ms_sa[n_sa]<=sa.retire_mem_wstrb;
   if(sa.retire_rd_we&&!perf_csr_read(sa.retire_instr))regs_sa[sa.retire_rd_addr]<=sa.retire_rd_wdata;n_sa<=n_sa+1;end
 end
endtask
task automatic record_vc;
 begin
  if(vc.retire_instr==HALT)done_vc<=1;else begin
   if(n_vc>=2048)$fatal(1,"VC trace overflow");pc_vc[n_vc]<=vc.retire_pc;ins_vc[n_vc]<=vc.retire_instr;
   rd_vc[n_vc]<=vc.retire_rd_addr;we_vc[n_vc]<=vc.retire_rd_we;val_vc[n_vc]<=vc.retire_rd_wdata;
   mwe_vc[n_vc]<=vc.retire_mem_write;ma_vc[n_vc]<=vc.retire_mem_addr;ms_vc[n_vc]<=vc.retire_mem_wstrb;
   if(vc.retire_rd_we&&!perf_csr_read(vc.retire_instr))regs_vc[vc.retire_rd_addr]<=vc.retire_rd_wdata;n_vc<=n_vc+1;end
 end
endtask

always@(posedge clk)if(reset_n)begin
 if(dm.retire_valid)record_dm();if(sa.retire_valid)record_sa();if(vc.retire_valid)record_vc();
end

initial begin
 for(i=0;i<32;i=i+1)begin regs_dm[i]=0;regs_sa[i]=0;regs_vc[i]=0;end
 repeat(5)@(posedge clk);@(negedge clk);reset_n=1;
 fork begin wait(done_dm&&done_sa&&done_vc);end begin repeat(500000)@(posedge clk);$fatal(1,"equivalence watchdog");end join_any disable fork;
 #2;
 if(n_dm!=n_sa||n_dm!=n_vc)$fatal(1,"retire count mismatch DM=%0d SA=%0d VC=%0d",n_dm,n_sa,n_vc);
 for(i=0;i<n_dm;i=i+1)begin
  if(pc_dm[i]!==pc_sa[i]||pc_dm[i]!==pc_vc[i]||ins_dm[i]!==ins_sa[i]||ins_dm[i]!==ins_vc[i]||
     rd_dm[i]!==rd_sa[i]||rd_dm[i]!==rd_vc[i]||we_dm[i]!==we_sa[i]||we_dm[i]!==we_vc[i]||
     ((!perf_csr_read(ins_dm[i]))&&(val_dm[i]!==val_sa[i]||val_dm[i]!==val_vc[i]))||
     mwe_dm[i]!==mwe_sa[i]||mwe_dm[i]!==mwe_vc[i]||
     ma_dm[i]!==ma_sa[i]||ma_dm[i]!==ma_vc[i]||ms_dm[i]!==ms_sa[i]||ms_dm[i]!==ms_vc[i])
   $fatal(1,"retirement mismatch order=%0d DM pc/i=%h/%h SA=%h/%h VC=%h/%h",i,pc_dm[i],ins_dm[i],pc_sa[i],ins_sa[i],pc_vc[i],ins_vc[i]);
 end
 for(i=0;i<32;i=i+1)if(regs_dm[i]!==regs_sa[i]||regs_dm[i]!==regs_vc[i])
  $fatal(1,"GPR mismatch x%0d DM=%h SA=%h VC=%h",i,regs_dm[i],regs_sa[i],regs_vc[i]);
 for(i=0;i<2048;i=i+1)begin
  if({dm.u_axi_ram.RAM3[i],dm.u_axi_ram.RAM2[i],dm.u_axi_ram.RAM1[i],dm.u_axi_ram.RAM0[i]}!==
     {sa.u_axi_ram.RAM3[i],sa.u_axi_ram.RAM2[i],sa.u_axi_ram.RAM1[i],sa.u_axi_ram.RAM0[i]}||
     {dm.u_axi_ram.RAM3[i],dm.u_axi_ram.RAM2[i],dm.u_axi_ram.RAM1[i],dm.u_axi_ram.RAM0[i]}!==
     {vc.u_axi_ram.RAM3[i],vc.u_axi_ram.RAM2[i],vc.u_axi_ram.RAM1[i],vc.u_axi_ram.RAM0[i]})
   $fatal(1,"architectural memory mismatch word=%0d",i);
 end
 if(regs_dm[31]!==1)$fatal(1,"directed ISA self-check code=%0d",regs_dm[31]);
 $display("[PASS] DM/SA2/DM_VC4 (FAST_HIT=%0d) retirement traces identical (%0d instructions)",FAST_HIT,n_dm);
 $display("[PASS] DM/SA2/DM_VC4 GPR and architectural memory identical");
 $finish;
end
endmodule
