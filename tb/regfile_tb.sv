`timescale 1ns/1ps

// Register file unit test (2026-10-08, review A1: the FPGA view keeps the registers in two M9K copies with a
// registered read). The bench drives rs1 / rs2 as the datapath does: registers loaded at every edge from the
// read-ahead values rs1_n / rs2_n, which the FPGA view also receives (rs1_next / rs2_next). A cycle runs from one
// posedge to the next: the stimulus changes just after the edge, both ports are compared at the negedge with the old
// asynchronous array (write at the edge, write-through in the write cycle, x0 = 0), and every compare is classified
// by the path the M9K version must take (RAM read / write of the last edge / write-through), so the bench proves it
// exercised all three. The same bench runs on both views.
module tb_regfile;

reg         clk;
reg         we;
reg  [4:0]  rd;
reg  [31:0] wd;
reg  [4:0]  rs1_n, rs2_n;
reg  [4:0]  rs1, rs2;
wire [31:0] rd1, rd2;

reg  [31:0] model [0:31];
reg         last_we;
reg  [4:0]  last_rd;
integer     failures, checks, cov_ram, cov_last, cov_wt;
integer     cyc, r;

always @(posedge clk) begin
    rs1     <= rs1_n;
    rs2     <= rs2_n;
    last_we <= we && rd != 5'd0;
    last_rd <= rd;
    if (we && rd != 5'd0)
        model[rd] <= wd;
end

regfile dut (
    .clk   (clk),
    .we    (we),
    .rs1   (rs1),
    .rs2   (rs2),
    .rd    (rd),
    .wd    (wd),
`ifndef __openlane__
    .rs1_next (rs1_n),
    .rs2_next (rs2_n),
`endif
    .rd1_d (rd1),
    .rd2_d (rd2)
);

always #5 clk = ~clk;

function automatic [31:0] expect_rd(input [4:0] rs);
    expect_rd = (rs == 5'd0) ? 32'd0 : (we && rd == rs) ? wd : model[rs];
endfunction

task automatic classify(input [4:0] rs);
    begin
        if (rs != 5'd0) begin
            if (we && rd == rs)              cov_wt   = cov_wt + 1;
            else if (last_we && last_rd == rs) cov_last = cov_last + 1;
            else                             cov_ram  = cov_ram + 1;
        end
    end
endtask

// one cycle, entered just after an edge: drive, compare at the negedge, then the edge writes and loads rs1 / rs2
task automatic step(input w, input [4:0] d, input [31:0] v, input [4:0] a1, input [4:0] a2, input string tag);
    begin
        we = w; rd = d; wd = v; rs1_n = a1; rs2_n = a2;
        @(negedge clk);
        checks = checks + 1;
        classify(rs1);
        classify(rs2);
        if (rd1 !== expect_rd(rs1) || rd2 !== expect_rd(rs2)) begin
            failures = failures + 1;
            if (failures <= 10)
                $error("[FAIL] %s: rs1 x%0d = %h (expected %h), rs2 x%0d = %h (expected %h), we %b rd x%0d wd %h",
                       tag, rs1, rd1, expect_rd(rs1), rs2, rd2, expect_rd(rs2), we, rd, wd);
        end
        @(posedge clk);
        #1;
    end
endtask

task automatic check(input condition, input string message);
    begin
        if (condition !== 1'b1) begin
            failures = failures + 1;
            $error("[FAIL] %s", message);
        end
        else
            $display("[PASS] %s", message);
    end
endtask

integer c0, c1, c2;

initial begin
    clk = 1'b0; we = 1'b0; rd = 5'd0; wd = 32'd0; rs1_n = 5'd0; rs2_n = 5'd0;
    failures = 0; checks = 0; cov_ram = 0; cov_last = 0; cov_wt = 0;
    @(posedge clk);
    #1;

    $display("[TEST RF-1] fill x1..x31 through the write port, read every register back on both ports");
    for (r = 1; r < 32; r = r + 1)
        step(1'b1, r[4:0], 32'h0101_0101 * r, 5'd0, 5'd0, "fill");
    for (r = 1; r < 32; r = r + 1)
        step(1'b0, 5'd0, 32'd0, r[4:0], 5'd31 - r[4:0], "read back");
    step(1'b0, 5'd0, 32'd0, 5'd0, 5'd0, "read back");
    check(failures == 0 && cov_ram >= 61, "Every register reads back its value (RAM path)");

    $display("[TEST RF-2] read of the register written at the last edge");
    c1 = cov_last;
    step(1'b1, 5'd5, 32'hdead_0005, 5'd5, 5'd6, "write x5, next cycle reads x5");
    step(1'b0, 5'd0, 32'd0, 5'd0, 5'd0, "read x5 one cycle after its write");
    check(failures == 0 && cov_last == c1 + 1, "The register written at the last edge reads its new value");

    $display("[TEST RF-3] write-through in the write cycle");
    c2 = cov_wt;
    step(1'b0, 5'd0, 32'd0, 5'd6, 5'd6, "decode will read x6");
    step(1'b1, 5'd6, 32'hbeef_0006, 5'd0, 5'd0, "write x6 while decode reads it");
    step(1'b0, 5'd0, 32'd0, 5'd0, 5'd0, "after the write-through");
    check(failures == 0 && cov_wt == c2 + 2, "A read of the register written in that cycle returns the write data");

    $display("[TEST RF-4] x0");
    c0 = checks;
    step(1'b1, 5'd0, 32'hffff_ffff, 5'd0, 5'd0, "write x0");
    step(1'b0, 5'd0, 32'd0, 5'd0, 5'd0, "read x0 after a write to it");
    check(failures == 0 && checks == c0 + 2, "x0 reads 0 while and after it is written");

    $display("[TEST RF-5] two writes to one register on consecutive edges");
    step(1'b1, 5'd9, 32'h0000_0001, 5'd0, 5'd0, "x9 = 1");
    step(1'b1, 5'd9, 32'h0000_0002, 5'd9, 5'd9, "x9 = 2, next cycle reads x9");
    step(1'b0, 5'd0, 32'd0, 5'd0, 5'd0, "read x9");
    check(failures == 0, "The later of two back-to-back writes wins");

    $display("[TEST RF-6] random traffic, 20000 cycles, both ports checked every cycle");
    for (cyc = 0; cyc < 20000; cyc = cyc + 1)
        step($urandom_range(0, 1), $urandom_range(0, 31), $urandom, $urandom_range(0, 31), $urandom_range(0, 31),
             "random");
    check(failures == 0, "Random traffic matches the asynchronous register file");
    check(cov_ram > 1000 && cov_last > 100 && cov_wt > 100,
          $sformatf("All three read paths exercised: RAM %0d, last-edge write %0d, write-through %0d",
                    cov_ram, cov_last, cov_wt));

    if (failures == 0) begin
        $display("[PASS] Register file: %0d cycle checks, RAM path, last-edge write, write-through, x0", checks);
        $finish;
    end
    else
        $fatal(1, "[FAIL] regfile_tb: %0d failures in %0d checks", failures, checks);
end

initial begin
    #1000000;
    $fatal(1, "[FAIL] regfile_tb timeout");
end

endmodule
