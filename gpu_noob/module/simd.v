`timescale 1ns/1ps
`include "common_defs.v"

/*
--------------------------------
SIMD Unit
--------------------------------
- Holds up to one wavefront
- Program Counter for wavefront
- 16-Lane ALU, LOAD/STORE
- Register File for each lane to store data for wavefront
--------------------------------
Global Thread Id Calculation
--------------------------------
g = blockId.x * blockDim + threadId.x
threadId.x = wave_id * wave_size + (warp_cycle * SIMD_width + lane_id)
--------------------------------
*/
module SIMD #(
    parameter DATA_WIDTH = 64,
    parameter INSTRUCTION_WIDTH = 32,
    parameter PROGRAM_MEM_ADDR_WIDTH = 6,
    parameter DATA_REG_ADDR_WIDTH = 7,
    parameter LANE_WIDTH = 16,
    parameter WAVE_SIZE = 32
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // kernel metadata
    input wire [31:0] num_threads, // num of total threads -- defined by kernel
    input wire [31:0] block_dim, // num of threads per block -- defined by kernel 

    // block and wave info
    input wire signed [31:0] block_id, // assigned block_id from block dispatcher
    input wire signed [31:0] wave_id, // assigned wave_id from wave dispatcher
    input wire [31:0] num_waves_in_block, // num of waves in current block of CU -- calculated by wave dispatcher

    // simd wave dispatch states
    input wire simd_ready, 
    input wire simd_start, 
    input wire simd_working, 
    output reg simd_done,

    // data memory feedback
    input wire [LANE_WIDTH-1:0] data_mem_ready_ack,
    input wire [LANE_WIDTH-1:0] data_mem_write_ack,
    input wire [DATA_WIDTH-1:0] mem_read_data [LANE_WIDTH-1:0],

    // program memory feedback
    input wire prog_mem_read_ack,
    input wire [INSTRUCTION_WIDTH-1:0] prog_mem_read_data,

    // data memory outputs
    output reg [LANE_WIDTH-1:0] mem_read_valid,
    output reg [LANE_WIDTH-1:0] mem_write_valid,
    output reg [DATA_REG_ADDR_WIDTH-1:0] mem_addr [LANE_WIDTH-1:0],
    output reg [DATA_WIDTH-1:0] mem_write_data [LANE_WIDTH-1:0],

    // program memory outputs
    output reg prog_mem_read_valid,
    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] prog_mem_addr
);

// -- START Shared States -- 
reg [2:0] simd_state;
reg [2:0] fetcher_state;
/* WAVE CYCLE LOGIC */
localparam TOTAL_WAVE_CYCLES = (WAVE_SIZE + LANE_WIDTH - 1) / LANE_WIDTH;
reg [$clog2(TOTAL_WAVE_CYCLES)-1:0] curr_wave_cycle;
reg [INSTRUCTION_WIDTH-1:0] instruction;
// -- END Shared States --

// -- START Registers --
// inputs -- come from instruction; same for each lane
reg [DATA_REG_ADDR_WIDTH-1:0] rm;
reg [DATA_REG_ADDR_WIDTH-1:0] rn;
reg [DATA_REG_ADDR_WIDTH-1:0] rd;
// outputs
reg [DATA_WIDTH-1:0] rm_data [LANE_WIDTH-1:0];
reg [DATA_WIDTH-1:0] rn_data [LANE_WIDTH-1:0];
reg [DATA_WIDTH-1:0] reg_write_data [LANE_WIDTH-1:0];
// -- END Registers --

// -- START LSU --
reg [1:0] lsu_state [LANE_WIDTH-1:0];
reg [DATA_WIDTH-1:0] lsu_read_out[LANE_WIDTH-1:0];
// -- END LSU --

// -- START Signals -- 
reg REG_WRITE; // enable write to reg_file
reg MEM_READ; // enable read from data memory
reg MEM_WRITE; // enable write to data memory
reg MEM_TO_REG; // mux: write from memory or ALU to reg_file
// -- END Signals --

// -- START PC --
wire curr_pc = pc_out; // TODO: PC_OUT should be set by SIMD controller
wire DISPATCH_NEW_WAVE = simd_start; 
// -- END PC --

PC#(.PROGRAM_MEM_ADDR_WIDTH(PROGRAM_MEM_ADDR_WIDTH)) pc (
    .clk(clk),
    .rst(rst),
    .simd_state(simd_state),
    .DISPATCH_NEW_WAVE(DISPATCH_NEW_WAVE),
    .pc_in(curr_pc),
    .pc_out(pc_out)
);

Fetcher fetcher (
    .clk(clk),
    .rst(rst),
    .enable(enable),
    .simd_state(simd_state),
    .curr_pc(curr_pc),
    .prog_mem_read_ack(prog_mem_read_ack),
    .prog_mem_read_data(prog_mem_read_data),

    .prog_mem_read_valid(prog_mem_read_valid),
    .prog_mem_addr(prog_mem_addr),
    .fetcher_state(fetcher_state),
    .instruction(instruction)
);

// TODO: SIMD Controller

genvar i;
generate 
    for (i = 0; i < LANE_WIDTH; i = i + 1) begin
        RegisterFile rf (
            .clk(clk),
            .rst(rst),
            .enable(enable),
            .block_id(block_id),
            .wave_id(wave_id),
            .block_dim(block_dim),
            .curr_wave_cycle(curr_wave_cycle),
            .lane_id(i),
            .REG_WRITE(REG_WRITE),
            .simd_state(simd_state),
            .rm(rm),
            .rn(rn),
            .rd(rd),
            .reg_write_data(reg_write_data[i]),
            .rm_data(rm_data[i]),
            .rn_data(rn_data[i])
        );

        LSU lsu (
            .clk(clk),
            .rst(rst),
            .enable(enable),
            .simd_state(simd_state),
            .rm(rm),
            .rn(rn),
            .MEM_READ(MEM_READ),
            .MEM_WRITE(MEM_WRITE),
            .mem_read_ack(data_mem_ready_ack[i]),
            .mem_write_ack(data_mem_write_ack[i]),
            .mem_read_data(mem_read_data[i]),

            .mem_read_valid(mem_read_valid[i]),
            .mem_write_valid(mem_write_valid[i]),
            .mem_addr(mem_addr[i]),
            .mem_write_data(mem_write_data[i]),
            .lsu_state(lsu_state[i]),
            .lsu_read_out(lsu_read_out[i])
        );
    end
endgenerate

endmodule
