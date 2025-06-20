`timescale 1ns/1ps
/*
--------------------------------------
Register File (4 KB)
--------------------------------------
// 64b x 32 registers for each lane
// 16 lanes x 32 registers = 512 registers
--------------------------------------
READ-ONLY:
R28-R30: blockIdx, blockDim, threadIdx
R31: zero
--------------------------------------
WRITABLE:
R4-R31: general purpose
--------------------------------------
blockIdx: block's ID within a block grid
blockDim: number of threads per block
threadIdx: thread's ID within a block
*/
module RegisterFile # (
    parameter DATA_REG_ADDR_WIDTH = 7, 
    parameter DATA_WIDTH = 64,
    parameter NUM_REGISTERS = 32,
    parameter WAVE_SIZE = 32,
    parameter LANE_WIDTH = 16
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // kernel metadata
    input wire signed [31:0] block_id,
    input wire  signed [31:0] wave_id,
    input wire [31:0] block_dim,

    input wire [$clog2((WAVE_SIZE + LANE_WIDTH - 1) / LANE_WIDTH)] curr_wave_cycle,
    input wire [$clog2(LANE_WIDTH-1):0] lane_id, // corresponding SIMD lane the reg_file is associated with

    // signals
    input wire REG_WRITE,
    input wire [2:0] simd_state,

    // registers
    input wire [DATA_REG_ADDR_WIDTH-1:0] rm,
    input wire [DATA_REG_ADDR_WIDTH-1:0] rn,
    input wire [DATA_REG_ADDR_WIDTH-1:0] rd,

    // write data -- from ALU or memory
    input wire [DATA_WIDTH-1:0] write_data, 

    // reading data from registers
    output reg [DATA_WIDTH-1:0] rm_data,
    output reg [DATA_WIDTH-1:0] rn_data
);

reg [DATA_WIDTH-1:0] reg_file [NUM_REGISTERS-1:0];

wire [31:0] thread_id_x;
assign thread_id_x = wave_id * WAVE_SIZE + (curr_wave_cycle * LANE_WIDTH + lane_id);

always @ (block_id, block_dim, thread_id_x) begin
    reg_file[28] <= block_id;
    reg_file[29] <= block_dim;
    reg_file[30] <= thread_id_x;
end

integer i;
always @ (posedge(clk)) begin
    if (rst) begin
        // initialize read-only registers
        reg_file[28] <= block_id;
        reg_file[29] <= block_dim;
        reg_file[30] <= thread_id_x;
        reg_file[31] <= 0;
        
        for (i = 0; i < 28; i = i + 1) begin
            // initialize general purpose registers
            reg_file[i] <= 0;
        end
        
        // clear output data
        rm_data <= 0;
        rn_data <= 0;
    end

    else begin
        if (enable) begin
            // if SIMD state == REQUEST
            if (simd_state == 3'b011) begin
                rm_data <= reg_file[rm];
                rn_data <= reg_file[rn];
            end

            // if REG_WRITE enabled and SIMD state == UPDATE
            // writing only allowed to general purpose registers
            if (REG_WRITE && simd_state == 3'b110 && rd < 28) begin
                reg_file[rd] = write_data;
            end

        end
    end
end

endmodule