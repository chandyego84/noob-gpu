`timescale 1ns/1ps
/*
--------------------------------
SIMD Unit
--------------------------------
- Holds up to one wavefront
- Program Counter for wavefront
- 16-Lane ALU, LOAD/STORE
- Vector Register File to store data for wavefront
--------------------------------
Global Thread Id Calculation
--------------------------------
g = blockId.x * blockDim + threadId.x
threadId.x = wave_id * wave_size + (warp_cycle * SIMD_width + lane_id)
*/
module SIMD #(
    parameter PROGRAM_MEM_ADDR_WIDTH = 32,
    parameter WAVE_SIZE = 32,
    parameter LANE_WIDTH = 16
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // kernel metadata
    input wire [31:0] num_threads, // num of total threads -- defined by kernel
    input wire [31:0] block_dim, // num of threads per block -- defined by kernel 

    input wire signed [31:0] block_id, // assigned block_id from block dispatcher
    input wire signed [31:0] wave_id, // assigned wave_id from wave dispatcher
    input wire [31:0] num_waves_in_block, // num of waves in current block of CU -- calculated by wave dispatcher

    // simd states
    input wire simd_start,
    input wire simd_ready,
    output reg simd_done,

    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_out,
    output reg [63:0] mem_address [0:LANE_WIDTH-1],
    output reg [63:0] mem_write_data [0:LANE_WIDTH-1]
);

// PC
wire curr_pc;
wire DISPATCH_NEW_WAVE; 
reg UPDATE_PC; // TODO

assign curr_pc = pc_out;
assign DISPATCH_NEW_WAVE = simd_start;

PC#(.PROGRAM_MEM_ADDR_WIDTH(PROGRAM_MEM_ADDR_WIDTH)) pc (
    .clk(clk),
    .rst(rst),
    .UPDATE_PC(UPDATE_PC),
    .DISPATCH_NEW_WAVE(DISPATCH_NEW_WAVE),
    .pc_in(curr_pc),
    .pc_out(pc_out)
);

// Vector Register File (4 KB)
    // 64b x 32 registers for each lane
    // 16 lanes x 32 registers = 512 registers

// Vector ALU, LSU

always @ (posedge(clk)) begin
    // check if current wave is done executing

    // dispatcher assigns new wave

    // executing a wave
        // if switching context:
            // set active_context to slot index of wave to run
        // execute current instruction, UPDATE_PC=0
            // when done, UPDATE_PC=1

end

endmodule
