`timescale 1ns/1ps

module tb_bht;

localparam integer BHT_ENTRIES = 256;
localparam [1:0] RESET_STATE = 2'b01;

reg         clk;
reg         reset_n;
reg  [31:0] fetch_pc;
wire [7:0]  fetch_index;
wire [1:0]  fetch_state;
wire        predict_taken;
reg         update_en;
reg  [31:0] update_pc;
reg         actual_taken;

integer i;
integer failures;

bht_2bit #(
    .BHT_ENTRIES(BHT_ENTRIES),
    .BHT_RESET_STATE(RESET_STATE)
) dut (
    .clk(clk),
    .reset_n(reset_n),
    .fetch_pc(fetch_pc),
    .fetch_index(fetch_index),
    .fetch_state(fetch_state),
    .predict_taken(predict_taken),
    .update_en(update_en),
    .update_pc(update_pc),
    .actual_taken(actual_taken)
);

always #5 clk = ~clk;

task automatic check;
    input condition;
    input string message;
    begin
        if (condition !== 1'b1) begin
            failures = failures + 1;
            $error("[FAIL] %s", message);
        end
        else
            $display("[PASS] %s", message);
    end
endtask

task automatic update;
    input [31:0] pc;
    input        taken;
    begin
        @(negedge clk);
        update_pc    = pc;
        actual_taken = taken;
        update_en    = 1'b1;
        @(posedge clk);
        #1;
        update_en    = 1'b0;
        fetch_pc     = pc;
        #1;
    end
endtask

initial begin
    clk          = 1'b0;
    reset_n      = 1'b0;
    fetch_pc     = 32'h0000_0000;
    update_en    = 1'b0;
    update_pc    = 32'h0000_0000;
    actual_taken = 1'b0;
    failures     = 0;

    repeat (2) @(posedge clk);
    #1;

    $display("[TEST BHT-1] deterministic weakly-not-taken reset");
    for (i = 0; i < BHT_ENTRIES; i = i + 1) begin
        fetch_pc = i << 2;
        #1;
        if (fetch_state !== RESET_STATE || predict_taken !== 1'b0) begin
            failures = failures + 1;
            $error("[FAIL] reset entry %0d state=%b prediction=%b",
                   i, fetch_state, predict_taken);
        end
    end
    check(failures == 0, "BHT reset initializes every entry to 01 / predict NT");

    @(negedge clk);
    reset_n = 1'b1;
    fetch_pc = 32'h0000_0040;
    #1;

    $display("[TEST BHT-2] taken training");
    update(32'h0000_0040, 1'b1);
    check(fetch_state == 2'b10 && predict_taken,
          "Taken transition 01 -> 10 changes prediction to taken");
    update(32'h0000_0040, 1'b1);
    check(fetch_state == 2'b11 && predict_taken,
          "Taken transition 10 -> 11");

    $display("[TEST BHT-3] saturate taken");
    update(32'h0000_0040, 1'b1);
    update(32'h0000_0040, 1'b1);
    check(fetch_state == 2'b11, "Repeated taken updates saturate at 11");

    $display("[TEST BHT-4] not-taken training");
    update(32'h0000_0040, 1'b0);
    check(fetch_state == 2'b10, "Not-taken transition 11 -> 10");
    update(32'h0000_0040, 1'b0);
    check(fetch_state == 2'b01 && !predict_taken,
          "Not-taken transition 10 -> 01 changes prediction to NT");
    update(32'h0000_0040, 1'b0);
    check(fetch_state == 2'b00, "Not-taken transition 01 -> 00");

    $display("[TEST BHT-5] saturate not taken");
    update(32'h0000_0040, 1'b0);
    update(32'h0000_0040, 1'b0);
    check(fetch_state == 2'b00, "Repeated not-taken updates saturate at 00");

    $display("[TEST BHT-6] intentional tagless aliasing");
    // 0x00000080 and 0x00000480 differ above index bit 9 but both use index 0x20.
    update(32'h0000_0080, 1'b1);
    fetch_pc = 32'h0000_0480;
    #1;
    check(fetch_index == 8'h20 && fetch_state == 2'b10 && predict_taken,
          "Two PCs with the same pc[9:2] share one BHT entry");
    update(32'h0000_0480, 1'b1);
    fetch_pc = 32'h0000_0080;
    #1;
    check(fetch_state == 2'b11,
          "An update through the alias is visible through the original PC");

    if (failures == 0) begin
        $display("[PASS] BHT reset, FSM saturation and aliasing tests");
        $finish;
    end
    else
        $fatal(1, "[FAIL] bht_tb: %0d checks failed", failures);
end

initial begin
    #10000;
    $fatal(1, "[FAIL] bht_tb timeout");
end

endmodule
