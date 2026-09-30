`timescale 1ns/1ps
// Gate-level simulation of the signed-off ASIC netlist (soc_asic_top after
// fill insertion) running an Embench kernel (FLOW_JOURNAL, EQY replacement).
//
// Yosys.EQY cannot finish on this host (Incident 64), so RTL = netlist is not
// proven formally. This is the functional substitute: the same firmware image
// the RTL runs, loaded straight into the four main-memory SRAM macro models,
// judged only on what the chip drives out:
//   LEDR = 8'hA5 -> the kernel's own self-check passed (8'hEE: failed)
//   HEX7..HEX0   -> disp_value = mcycle of the measured region
// The mcycle must equal the ASIC-view RTL run (results/asic_view_4kb_p1.csv,
// same SRAM models, same RTL): a gate netlist that differs from the RTL in
// any way that matters would change the cycle count or fail the self-check.
//
//   vsim -gMEMFILE=fw/up_crc32.hex work_gls.tb_gls_soc
module tb_gls_soc;
    parameter string  MEMFILE    = "fw/up_crc32.hex";
    parameter integer MAX_CYCLES = 3000000;
    parameter string  VCD_FILE   = "";        // non-empty: dump switching activity

    reg clk = 1'b0, reset_n = 1'b0, key1_n = 1'b1, uart_rx = 1'b1;
    always #10 clk = ~clk;   // zero-delay cell models: the period is nominal

    wire       uart_tx;
    wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
    wire [7:0] LEDR, LCD_DATA;
    wire       LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

    soc_asic_top dut (
        .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx),
        .uart_tx(uart_tx), .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3),
        .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7), .LEDR(LEDR),
        .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW),
        .LCD_ON(LCD_ON), .LCD_BLON(LCD_BLON));

    // Main memory: word w lives in bank w/512 at offset w%512
    // (axi_ram_32_asic_macro.v: bank_sel = word_addr[WORD_BITS-1:9]).
    // R14 (RAM16K_CHANGES.md): compile with +define+GLS_RAM16K for the 16 KiB design (8 banks, 4096 words).
    // Without it the testbench stays as it was for the signed-off 8 KiB netlists (4 banks, 2048 words): the
    // gate netlist's bank instances are escaped names, so each bank is listed explicitly.
`ifdef GLS_RAM16K
    localparam int RAM_WORDS = 4096;
`else
    localparam int RAM_WORDS = 2048;
`endif
    reg [31:0] img [0:RAM_WORDS-1];
    integer i;
    initial begin
        for (i = 0; i < RAM_WORDS; i = i + 1) img[i] = 32'h0;
        $readmemh(MEMFILE, img);
        for (i = 0; i < 512; i = i + 1) begin
            dut.\u_soc.u_axi_ram.g_bank[0].u_bank .mem[i] = img[i];
            dut.\u_soc.u_axi_ram.g_bank[1].u_bank .mem[i] = img[512  + i];
            dut.\u_soc.u_axi_ram.g_bank[2].u_bank .mem[i] = img[1024 + i];
            dut.\u_soc.u_axi_ram.g_bank[3].u_bank .mem[i] = img[1536 + i];
`ifdef GLS_RAM16K
            dut.\u_soc.u_axi_ram.g_bank[4].u_bank .mem[i] = img[2048 + i];
            dut.\u_soc.u_axi_ram.g_bank[5].u_bank .mem[i] = img[2560 + i];
            dut.\u_soc.u_axi_ram.g_bank[6].u_bank .mem[i] = img[3072 + i];
            dut.\u_soc.u_axi_ram.g_bank[7].u_bank .mem[i] = img[3584 + i];
`endif
        end
    end

    function automatic logic [3:0] unseg(input logic [6:0] s, output bit ok);
        ok = 1'b1;
        case (s)
            7'b1000000: return 4'h0;  7'b1111001: return 4'h1;
            7'b0100100: return 4'h2;  7'b0110000: return 4'h3;
            7'b0011001: return 4'h4;  7'b0010010: return 4'h5;
            7'b0000010: return 4'h6;  7'b1111000: return 4'h7;
            7'b0000000: return 4'h8;  7'b0010000: return 4'h9;
            7'b0001000: return 4'hA;  7'b0000011: return 4'hB;
            7'b1000110: return 4'hC;  7'b0100001: return 4'hD;
            7'b0000110: return 4'hE;  7'b0001110: return 4'hF;
            default: begin ok = 1'b0; return 4'h0; end
        endcase
    endfunction

    // Measured region, for activity capture (SAIF, asic/gls/run_gls_power.sh).
    // The perf counters run from the kernel's sysmon_clear_start() (the perf
    // counter mcycle, soc_top.perf_mcycle_count_dbg, drops back to 0 -- not
    // the core's CSR mcycle_dbg, which never clears) until
    // sysmon_freeze_snapshot() (freeze_q rises); win_on spans those cycles, and
    // win_cycles is checked against the decoded mcycle.
    // Sampled on the falling edge: the zero-delay flop models update on the
    // rising edge in the same time step, so a rising-edge read would race.
    wire [31:0] mcyc = {dut.\u_soc.perf_mcycle_count_dbg[31] , dut.\u_soc.perf_mcycle_count_dbg[30] , dut.\u_soc.perf_mcycle_count_dbg[29] , dut.\u_soc.perf_mcycle_count_dbg[28] , dut.\u_soc.perf_mcycle_count_dbg[27] , dut.\u_soc.perf_mcycle_count_dbg[26] , dut.\u_soc.perf_mcycle_count_dbg[25] , dut.\u_soc.perf_mcycle_count_dbg[24] , dut.\u_soc.perf_mcycle_count_dbg[23] , dut.\u_soc.perf_mcycle_count_dbg[22] , dut.\u_soc.perf_mcycle_count_dbg[21] , dut.\u_soc.perf_mcycle_count_dbg[20] , dut.\u_soc.perf_mcycle_count_dbg[19] , dut.\u_soc.perf_mcycle_count_dbg[18] , dut.\u_soc.perf_mcycle_count_dbg[17] , dut.\u_soc.perf_mcycle_count_dbg[16] , dut.\u_soc.perf_mcycle_count_dbg[15] , dut.\u_soc.perf_mcycle_count_dbg[14] , dut.\u_soc.perf_mcycle_count_dbg[13] , dut.\u_soc.perf_mcycle_count_dbg[12] , dut.\u_soc.perf_mcycle_count_dbg[11] , dut.\u_soc.perf_mcycle_count_dbg[10] , dut.\u_soc.perf_mcycle_count_dbg[9] , dut.\u_soc.perf_mcycle_count_dbg[8] , dut.\u_soc.perf_mcycle_count_dbg[7] , dut.\u_soc.perf_mcycle_count_dbg[6] , dut.\u_soc.perf_mcycle_count_dbg[5] , dut.\u_soc.perf_mcycle_count_dbg[4] , dut.\u_soc.perf_mcycle_count_dbg[3] , dut.\u_soc.perf_mcycle_count_dbg[2] , dut.\u_soc.perf_mcycle_count_dbg[1] , dut.\u_soc.perf_mcycle_count_dbg[0] };
    wire frz = dut.\u_soc.u_observability.u_sysmon.freeze_q ;
    reg        win_on = 1'b0, win_done = 1'b0;
    reg [31:0] mcyc_q = 32'h0;
    integer    win_cycles = 0;
    time       win_t0 = 0, win_t1 = 0;
    always @(negedge clk) begin
        mcyc_q <= mcyc;
        if (reset_n && !win_done) begin
            if (mcyc < mcyc_q) begin
                win_on     <= 1'b1;
                win_cycles <= 0;
                win_t0     <= $time;
            end
            else if (win_on && frz) begin
                win_on   <= 1'b0;
                win_done <= 1'b1;
                win_t1   <= $time;
            end
            else if (win_on)
                win_cycles <= win_cycles + 1;
        end
    end

    integer cycles = 0;
    logic [31:0] disp;
    bit ok, all_ok;
    initial begin
        if (VCD_FILE != "") begin
            $dumpfile(VCD_FILE);
            $dumpvars(0, dut);
        end
        repeat (5) @(posedge clk);
        reset_n = 1'b1;
        while (cycles < MAX_CYCLES && LEDR !== 8'hA5 && LEDR !== 8'hEE) begin
            @(posedge clk);
            cycles = cycles + 1;
        end
        repeat (2) @(posedge clk);
        all_ok = 1'b1;
        disp = {unseg(HEX7, ok), 28'h0};             all_ok &= ok;
        disp[27:24] = unseg(HEX6, ok);                all_ok &= ok;
        disp[23:20] = unseg(HEX5, ok);                all_ok &= ok;
        disp[19:16] = unseg(HEX4, ok);                all_ok &= ok;
        disp[15:12] = unseg(HEX3, ok);                all_ok &= ok;
        disp[11: 8] = unseg(HEX2, ok);                all_ok &= ok;
        disp[ 7: 4] = unseg(HEX1, ok);                all_ok &= ok;
        disp[ 3: 0] = unseg(HEX0, ok);                all_ok &= ok;
        if (cycles >= MAX_CYCLES)
            $display("GLS_RESULT memfile=%s status=TIMEOUT cycles=%0d LEDR=%h", MEMFILE, cycles, LEDR);
        else
            $display("GLS_RESULT memfile=%s status=%s mcycle=%0d hex_decoded=%0d cycles_to_done=%0d LEDR=%h win_cycles=%0d win_t0=%0t win_t1=%0t",
                     MEMFILE, (LEDR === 8'hA5) ? "PASS" : "FAIL", disp, all_ok, cycles, LEDR,
                     win_cycles, win_t0, win_t1);
        $finish;
    end
endmodule
