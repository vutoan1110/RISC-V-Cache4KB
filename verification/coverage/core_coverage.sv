`timescale 1ns/1ps

// Procedural functional coverage with explicit bins (portable to ModelSim ASE,
// where covergroup database access is license-dependent).
module core_coverage (
    input wire clk,
    input wire reset_n,
    input wire retire_valid,
    input wire [31:0] retire_instr,
    input wire [1:0] forward_a_e,
    input wire [1:0] forward_b_e,
    input wire load_use_hazard,
    input wire branch_resolve_fire,
    input wire [2:0] branch_funct3,
    input wire branch_taken,
    input wire predicted_taken,
    input wire branch_mispredict,
    input wire icache_hit_event,
    input wire icache_miss_event,
    input wire dcache_read_hit_event,
    input wire dcache_read_miss_event,
    input wire dcache_write_hit_event,
    input wire dcache_write_miss_event,
    input wire arvalid,
    input wire arready,
    input wire rvalid,
    input wire rready,
    input wire awvalid,
    input wire awready,
    input wire wvalid,
    input wire wready,
    input wire bvalid,
    input wire bready,
    input wire irq_accept,
    input wire cache_wait,
    input wire axi_busy
);

reg [11:0] instruction_bins;
reg [4:0] hazard_bins;
reg [5:0] branch_taken_bins;
reg [5:0] branch_not_taken_bins;
reg [3:0] prediction_bins;
reg [5:0] cache_bins;
reg [6:0] bus_bins;
reg [3:0] interrupt_bins;
reg saw_rvalid;
reg saw_aw_wait;
reg saw_w_wait;
reg aw_seen_for_write;
reg w_seen_for_write;

function [2:0] branch_slot;
    input [2:0] funct3;
    begin
        case(funct3)
            3'b000: branch_slot = 0;
            3'b001: branch_slot = 1;
            3'b100: branch_slot = 2;
            3'b101: branch_slot = 3;
            3'b110: branch_slot = 4;
            default: branch_slot = 5;
        endcase
    end
endfunction

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        instruction_bins <= 0;
        hazard_bins <= 0;
        branch_taken_bins <= 0;
        branch_not_taken_bins <= 0;
        prediction_bins <= 0;
        cache_bins <= 0;
        bus_bins <= 0;
        interrupt_bins <= 0;
        saw_rvalid <= 0;
        saw_aw_wait <= 0;
        saw_w_wait <= 0;
        aw_seen_for_write <= 0;
        w_seen_for_write <= 0;
    end
    else begin
        if(retire_valid) begin
            case(retire_instr[6:0])
                7'b0110011: begin
                    if(retire_instr[31:25] == 7'b0000001)
                        instruction_bins[9] <= 1'b1; // MUL*
                    else
                        instruction_bins[0] <= 1'b1; // R type
                end
                7'b0010011: instruction_bins[1] <= 1'b1;
                7'b0000011: instruction_bins[2] <= 1'b1;
                7'b0100011: instruction_bins[3] <= 1'b1;
                7'b1100011: instruction_bins[4] <= 1'b1;
                7'b1101111: instruction_bins[5] <= 1'b1;
                7'b1100111: instruction_bins[6] <= 1'b1;
                7'b0110111: instruction_bins[7] <= 1'b1;
                7'b0010111: instruction_bins[8] <= 1'b1;
                7'b1110011: instruction_bins[10] <= 1'b1;
                7'b0001111: instruction_bins[11] <= 1'b1;
                default: ;
            endcase
        end

        if(forward_a_e == 2'b10) hazard_bins[0] <= 1'b1;
        if(forward_b_e == 2'b10) hazard_bins[1] <= 1'b1;
        if(forward_a_e == 2'b01) hazard_bins[2] <= 1'b1;
        if(forward_b_e == 2'b01) hazard_bins[3] <= 1'b1;
        if(load_use_hazard)      hazard_bins[4] <= 1'b1;

        if(branch_resolve_fire) begin
            if(branch_taken)
                branch_taken_bins[branch_slot(branch_funct3)] <= 1'b1;
            else
                branch_not_taken_bins[branch_slot(branch_funct3)] <= 1'b1;
            prediction_bins[predicted_taken ? 1 : 0] <= 1'b1;
            prediction_bins[branch_mispredict ? 3 : 2] <= 1'b1;
        end

        if(icache_hit_event)        cache_bins[0] <= 1'b1;
        if(icache_miss_event)       cache_bins[1] <= 1'b1;
        if(dcache_read_hit_event)   cache_bins[2] <= 1'b1;
        if(dcache_read_miss_event)  cache_bins[3] <= 1'b1;
        if(dcache_write_hit_event)  cache_bins[4] <= 1'b1;
        if(dcache_write_miss_event) cache_bins[5] <= 1'b1;

        if(arvalid && arready) bus_bins[0] <= 1'b1;
        if(arvalid && !arready) bus_bins[1] <= 1'b1;
        if(saw_rvalid && !rvalid) bus_bins[2] <= 1'b1;
        saw_rvalid <= rvalid && rready;
        if(awvalid && awready && !(wvalid && wready)) bus_bins[3] <= 1'b1;
        if(wvalid && wready && !(awvalid && awready)) bus_bins[4] <= 1'b1;
        if(awvalid && awready && wvalid && wready) bus_bins[5] <= 1'b1;
        if((aw_seen_for_write || (awvalid && awready)) &&
           (w_seen_for_write || (wvalid && wready)) && !bvalid)
            bus_bins[6] <= 1'b1;
        if(awvalid && !awready) saw_aw_wait <= 1'b1;
        if(wvalid && !wready) saw_w_wait <= 1'b1;
        if(awvalid && awready) aw_seen_for_write <= 1'b1;
        if(wvalid && wready) w_seen_for_write <= 1'b1;
        if(bvalid && bready) begin
            aw_seen_for_write <= 1'b0;
            w_seen_for_write <= 1'b0;
        end

        if(irq_accept) begin
            interrupt_bins[0] <= 1'b1;
            if(branch_resolve_fire) interrupt_bins[1] <= 1'b1;
            if(cache_wait)          interrupt_bins[2] <= 1'b1;
            if(axi_busy)            interrupt_bins[3] <= 1'b1;
        end
    end
end

task report;
begin
    $display("[COVERAGE] Instruction bins R/I/L/S/B/JAL/JALR/LUI/AUIPC/MUL/CSR/FENCE = %012b", instruction_bins);
    $display("[COVERAGE] Hazard bins EX-a/EX-b/WB-a/WB-b/load-use = %05b", hazard_bins);
    $display("[COVERAGE] Branch taken types = %06b not-taken types = %06b", branch_taken_bins, branch_not_taken_bins);
    $display("[COVERAGE] Prediction NT/T/correct/miss = %04b", prediction_bins);
    $display("[COVERAGE] Cache I-H/I-M/DR-H/DR-M/DW-H/DW-M = %06b", cache_bins);
    $display("[COVERAGE] Bus no-stall/AR-BP/R-gap/AW-first/W-first/AW+W/B-delay = %07b", bus_bins);
    $display("[COVERAGE] IRQ normal/branch/cache-wait/AXI-wait = %04b", interrupt_bins);
    if(interrupt_bins != 4'b1111)
        $display("[COVERAGE] UNCOVERED: the directed ISA program does not hit every interrupt timing context");
    if(bus_bins != 7'b1111111)
        $display("[COVERAGE] UNCOVERED: specialized AXI ordering/backpressure bins are covered by the bus regression, not this program");
end
endtask

endmodule
