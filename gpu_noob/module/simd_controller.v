`timescale 1ns/1ps
`include "common_defs.v"

/*
--------------------------------------
SIMD Controller
--------------------------------------
// Manages control flow of a SIMD processing a wavefront
--------------------------------------

*/
module SimdController # (
    parameter PROGRAM_MEM_ADDR_WIDTH = 6,
    parameter LANE_WIDTH = 16,
    parameter TOTAL_WAVE_CYCLES = 2
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    input wire simd_start,
    input wire RET,

    input wire [2:0] fetcher_state,
    input wire [1:0] lsu_state [LANE_WIDTH-1:0],
    input wire [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_out, // calculated by PC during SIMD_EXECUTE state
        
    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] curr_pc,
    output reg [$clog2(TOTAL_WAVE_CYCLES)-1:0] curr_wave_cycle, // current cycle when processing a wave (starting at 0)
    output reg  [2:0] simd_state,
    output reg simd_done // wave for simd has completed
);

integer i;
reg lane_waiting;

always @(*) begin
    lane_waiting = 0;
    for (i = 0; i < LANE_WIDTH; i = i + 1) begin
        if (lsu_state[i] == `LSU_REQUESTING || lsu_state[i] == `LSU_WAITING) begin
            lane_waiting = 1;
        end
    end
end

always @ (posedge(clk)) begin
    if (rst) begin
        simd_state <= `SIMD_IDLE;
        curr_wave_cycle <= 0;
        curr_pc <= 0;
        simd_done <= 0;
    end

    else if (enable) begin
        case (simd_state) 
            `SIMD_IDLE: begin
                if (simd_start) begin
                    // assigned new wave
                    simd_done <= 0;
                    simd_state <= `SIMD_FETCH;
                end
            end

            `SIMD_FETCH: begin
                if (fetcher_state == `FETCHER_FETCHED) begin
                    simd_state <= `SIMD_DECODE;
                end
            end

            `SIMD_DECODE: begin
                simd_state <= `SIMD_REQUEST;
            end

            `SIMD_REQUEST: begin
                simd_state <= `SIMD_WAIT;
            end

            `SIMD_WAIT: begin
                // start executing only once all lanes are NOT waiting
                if (!lane_waiting) begin
                    simd_state <= `SIMD_EXECUTE;
                end

            end

            `SIMD_EXECUTE: begin
                simd_state <= `SIMD_UPDATE;
            end

            `SIMD_UPDATE: begin
                if (RET && (curr_wave_cycle == TOTAL_WAVE_CYCLES - 1)) begin
                    // current wave is done executing kernel
                    simd_state <= `SIMD_DONE;
                    simd_done <= 1;
                end

                else if (RET) begin
                    // part of wave is done executing kernel
                    curr_wave_cycle <= curr_wave_cycle + 1;
                    curr_pc <= 0; // rst PC to 0 for next part of the wave
                end

                else begin
                    // move on to next instruction
                    curr_pc <= pc_out;
                end
            end

            `SIMD_DONE: begin
                simd_state <= `SIMD_IDLE;
            end

        endcase
    end
end

endmodule