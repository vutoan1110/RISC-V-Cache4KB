module cache_backend_model #(
    parameter WORDS = 4096,
    // Words per cache line. The refill returns this many beats and asserts
    // rsp_last on the final one; hard-coding four made every other line size
    // untestable through this model.
    parameter LINE_WORDS = 4
)(
    input  logic        clk,
    input  logic        reset_n,
    input  logic        refill_req_valid,
    input  logic [31:0] refill_req_addr,
    output logic        refill_req_ready,
    output logic        refill_rsp_valid,
    output logic [31:0] refill_rsp_data,
    output logic        refill_rsp_last,
    output logic        refill_rsp_error,
    input  logic        mem_wr_valid,
    input  logic [31:0] mem_wr_addr,
    input  logic [31:0] mem_wr_data,
    input  logic [3:0]  mem_wr_strb,
    output logic        mem_wr_ready,
    output logic        mem_wr_rsp_valid,
    output logic        mem_wr_rsp_error,
    input  integer      ar_delay_cfg,
    input  integer      r_gap_cfg,
    output integer      read_txn_count,
    output integer      write_txn_count
);

logic [31:0] mem [0:WORDS-1];
logic read_active;
logic ar_waiting;
integer ar_wait;
integer gap_wait;
logic [31:0] line_base;
logic [4:0] beat;   // wide enough for the sixteen-word ceiling
integer i;

function automatic [31:0] merge_wstrb(
    input [31:0] old_word,input [31:0] new_word,input [3:0] strb);
    begin
        merge_wstrb=old_word;
        if(strb[0]) merge_wstrb[7:0]=new_word[7:0];
        if(strb[1]) merge_wstrb[15:8]=new_word[15:8];
        if(strb[2]) merge_wstrb[23:16]=new_word[23:16];
        if(strb[3]) merge_wstrb[31:24]=new_word[31:24];
    end
endfunction

initial for(i=0;i<WORDS;i=i+1) mem[i]=32'h1000_0000+i;

always_comb begin
    refill_req_ready = !read_active && ar_waiting && (ar_wait==0);
    mem_wr_ready = 1'b1;
end

// Plain `always` (not `always_ff`): `mem` is seeded by the initial block above,
// so the single-driver rule of `always_ff` (QuestaSim vopt-7061) does not apply.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        read_active<=0; ar_waiting<=0; ar_wait<=0; gap_wait<=0;
        line_base<=0; beat<=0; refill_rsp_valid<=0; refill_rsp_data<=0;
        refill_rsp_last<=0; refill_rsp_error<=0; mem_wr_rsp_valid<=0;
        mem_wr_rsp_error<=0; read_txn_count<=0; write_txn_count<=0;
    end else begin
        refill_rsp_valid<=0; refill_rsp_last<=0; refill_rsp_error<=0;
        mem_wr_rsp_valid<=0; mem_wr_rsp_error<=0;

        if(!read_active) begin
            if(refill_req_valid && !ar_waiting) begin
                ar_waiting<=1;
                ar_wait<=ar_delay_cfg;
            end else if(ar_waiting && ar_wait>0) begin
                ar_wait<=ar_wait-1;
            end
            if(refill_req_valid && refill_req_ready) begin
                // A refill delivers the line containing the address, so the
                // model must start at the line base, not at the raw request.
                read_active<=1; ar_waiting<=0;
                line_base<=refill_req_addr & ~32'((LINE_WORDS*4)-1);
                beat<=0; gap_wait<=r_gap_cfg; read_txn_count<=read_txn_count+1;
            end
        end else if(gap_wait>0) begin
            gap_wait<=gap_wait-1;
        end else begin
            refill_rsp_valid<=1;
            refill_rsp_data<=mem[(line_base[15:2])+beat];
            refill_rsp_last<=(beat==(LINE_WORDS-1));
            if(beat==(LINE_WORDS-1)) begin read_active<=0; beat<=0; end
            else begin beat<=beat+1'b1; gap_wait<=r_gap_cfg; end
        end

        if(mem_wr_valid && mem_wr_ready) begin
            mem[mem_wr_addr[15:2]]<=merge_wstrb(mem[mem_wr_addr[15:2]],mem_wr_data,mem_wr_strb);
            mem_wr_rsp_valid<=1; write_txn_count<=write_txn_count+1;
        end
    end
end
endmodule
