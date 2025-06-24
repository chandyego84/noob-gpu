`timescale 1ns/1ps
`include "common_defs.v"

/*
--------------------------------
Instruction Fetcher
--------------------------------
- Fetches instructions from program memory based on current PC
--------------------------------
*/

module Fetcher # (
    parameter PROGRAM_MEM_ADDR_WIDTH = 6,
    parameter INSTRUCTION_WIDTH = 32
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // States
    input wire [2:0] simd_state,
    input wire [PROGRAM_MEM_ADDR_WIDTH-1:0] curr_pc,

    // From program memory
    input wire prog_mem_read_ack,
    input wire [INSTRUCTION_WIDTH-1:0] prog_mem_read_data,

    // Outputs
    output reg prog_mem_read_valid,
    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] prog_mem_addr,
    output reg [2:0] fetcher_state,
    output reg [INSTRUCTION_WIDTH-1:0] instruction
);

always @ (posedge(clk)) begin
    if (rst) begin
        prog_mem_read_valid <= 0;
        prog_mem_addr <= 0;
        instruction <= 0;
        fetcher_state <= `FETCHER_IDLE;
    end

    else if (enable) begin
        case (fetcher_state) 
            `FETCHER_IDLE: begin
                if (simd_state == `SIMD_FETCH) begin
                    prog_mem_read_valid <= 1;
                    prog_mem_addr <= curr_pc;
                    fetcher_state <= `FETCHER_FETCHING;
                end
            end

            `FETCHER_FETCHING: begin
                if (prog_mem_read_ack) begin
                    prog_mem_addr <= 0;
                    instruction <= prog_mem_read_data;
                    fetcher_state <= `FETCHER_FETCHED;
                end
            end

            `FETCHER_FETCHED: begin
                if (simd_state == `SIMD_DECODE) begin
                    fetcher_state <= `FETCHER_IDLE;
                end
            end
        endcase
    end
end

endmodule