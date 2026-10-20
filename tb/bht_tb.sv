`timescale 1ns/1ps

// BHT unit test. Since 2026-10-08 (review A1) the FPGA view keeps the counters in M9K with a registered read, so the
// bench drives the PCs as the datapath does: fetch_pc / update_pc are registers loaded at every edge from the
// read-ahead values fetch_pc_n / update_pc_n, which the FPGA view also receives (fetch_pc_next / update_pc_next).
// A PC change therefore shows one edge later; the expected values are those of the old asynchronous table, and
// the same bench runs on both views. BHT-7..10 cover the M9K paths: the RAM read without bypass, back-to-back
// updates, a fetch of the entry being updated, and a reset in the middle of a run (valid bits).
module tb_bht;

localparam integer BHT_ENTRIES = 256;
localparam [1:0] RESET_STATE = 2'b01;

reg         clk;
reg         reset_n;
reg  [31:0] fetch_pc_n;
reg  [31:0] update_pc_n;
reg  [31:0] fetch_pc;
reg  [31:0] update_pc;
wire [7:0]  fetch_index;
wire [1:0]  fetch_state;
wire        predict_taken;
reg         update_en;
reg         actual_taken;

integer i;
integer failures;

always @(posedge clk) begin
    fetch_pc  <= fetch_pc_n;
    update_pc <= update_pc_n;
end

bht_2bit #(
    .BHT_ENTRIES(BHT_ENTRIES),
    .BHT_RESET_STATE(RESET_STATE)
) dut (
    .clk(clk),
    .reset_n(reset_n),
    .fetch_pc(fetch_pc),
`ifndef __openlane__
    .fetch_pc_next(fetch_pc_n),
    .update_pc_next(update_pc_n),
`endif
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

// fetch_pc = pc after the next edge
task automatic fetch;
    input [31:0] pc;
    begin
        @(negedge clk);
        fetch_pc_n = pc;
        @(posedge clk);
        #1;
    end
endtask

// fetch_pc = update_pc = pc, then one update of that entry; returns just after the edge that writes it
task automatic update;
    input [31:0] pc;
    input        taken;
    begin
        @(negedge clk);
        update_pc_n = pc;
        fetch_pc_n  = pc;
        @(posedge clk);
        #1;
        actual_taken = taken;
        update_en    = 1'b1;
        @(posedge clk);
        #1;
        update_en    = 1'b0;
    end
endtask

initial begin
    clk          = 1'b0;
    reset_n      = 1'b0;
    fetch_pc_n   = 32'h0000_0000;
    update_pc_n  = 32'h0000_0000;
    update_en    = 1'b0;
    actual_taken = 1'b0;
    failures     = 0;

    repeat (2) @(posedge clk);
    #1;

    $display("[TEST BHT-1] deterministic weakly-not-taken reset");
    for (i = 0; i < BHT_ENTRIES; i = i + 1) begin
        fetch(i << 2);
        if (fetch_state !== RESET_STATE || predict_taken !== 1'b0) begin
            failures = failures + 1;
            $error("[FAIL] reset entry %0d state=%b prediction=%b",
                   i, fetch_state, predict_taken);
        end
    end
    check(failures == 0, "BHT reset initializes every entry to 01 / predict NT");

    @(negedge clk);
    reset_n = 1'b1;
    fetch(32'h0000_0040);

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
    fetch(32'h0000_0480);
    check(fetch_index == 8'h20 && fetch_state == 2'b10 && predict_taken,
          "Two PCs with the same pc[9:2] share one BHT entry");
    update(32'h0000_0480, 1'b1);
    fetch(32'h0000_0080);
    check(fetch_state == 2'b11,
          "An update through the alias is visible through the original PC");

    $display("[TEST BHT-7] value read back after idle cycles (no bypass)");
    update(32'h0000_0100, 1'b1);
    fetch(32'h0000_0000);
    repeat (3) @(posedge clk);
    fetch(32'h0000_0100);
    check(fetch_state == 2'b10, "Fetch reads the stored counter several cycles after its update");
    @(negedge clk);
    update_pc_n = 32'h0000_0000;
    repeat (3) @(posedge clk);
    update(32'h0000_0100, 1'b1);
    check(fetch_state == 2'b11, "Update reads the stored counter several cycles after its last update");

    $display("[TEST BHT-8] back-to-back updates of different entries");
    @(negedge clk);
    update_pc_n  = 32'h0000_0200;
    @(posedge clk);
    #1;
    update_en    = 1'b1;
    actual_taken = 1'b1;
    @(negedge clk);
    update_pc_n  = 32'h0000_0204;
    @(posedge clk);                        // writes 0x200 (01 -> 10)
    #1;
    actual_taken = 1'b0;
    @(negedge clk);
    update_pc_n  = 32'h0000_0200;
    @(posedge clk);                        // writes 0x204 (01 -> 00)
    #1;
    actual_taken = 1'b1;
    @(posedge clk);                        // writes 0x200 again (10 -> 11), read two edges after its first write
    #1;
    update_en    = 1'b0;
    fetch(32'h0000_0200);
    check(fetch_state == 2'b11, "Entry 0x200 sees both of its updates around another entry's update");
    fetch(32'h0000_0204);
    check(fetch_state == 2'b00, "Entry 0x204 keeps its own update");

    $display("[TEST BHT-9] fetch of the entry being updated");
    update(32'h0000_0300, 1'b1);           // 01 -> 10
    repeat (3) @(posedge clk);
    #1;
    update_en    = 1'b1;
    actual_taken = 1'b1;
    #1;
    check(fetch_state == 2'b10, "In the update cycle fetch still sees the old counter");
    @(posedge clk);                        // 10 -> 11
    #1;
    update_en = 1'b0;
    check(fetch_state == 2'b11, "The cycle after the update fetch sees the new counter");

    $display("[TEST BHT-10] reset in the middle of a run");
    @(negedge clk);
    reset_n = 1'b0;
    @(posedge clk);
    #1;
    @(negedge clk);
    reset_n = 1'b1;
    fetch(32'h0000_0040);
    check(fetch_state == RESET_STATE, "Reset returns a trained entry (00) to 01");
    fetch(32'h0000_0080);
    check(fetch_state == RESET_STATE, "Reset returns a trained entry (11) to 01");
    update(32'h0000_0040, 1'b1);
    check(fetch_state == 2'b10, "First update after reset starts from 01, not from the stale counter");

    if (failures == 0) begin
        $display("[PASS] BHT reset, FSM saturation and aliasing tests");
        $finish;
    end
    else
        $fatal(1, "[FAIL] bht_tb: %0d checks failed", failures);
end

initial begin
    #20000;
    $fatal(1, "[FAIL] bht_tb timeout");
end

endmodule
