`timescale 1ns/1ps

// Dispatches thread blocks to compute units
// Assumes
    // Each CU can only hold up to one block
module BlockDispatch #(
    parameter NUM_CORES = 4
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // kernel metadata
    input wire [31:0] num_threads, // num of threads launched -- defined by kernel
    input wire [31:0] block_dim, // num of threads per block -- defined by kernel

    // info for each compute unit
    input wire [NUM_CORES-1:0] core_done, // given by compute unit
    output reg [NUM_CORES-1:0] core_start, // core is working on a block
    output reg [NUM_CORES-1:0] core_ready, // ready for a block

    // block_id assigned to each compute unit
    output reg signed [31:0] core_block_id [0:NUM_CORES-1],

    output reg kernel_done
);

// blocks dispatched vs finished tracker
reg [31:0] blocks_dispatched; // corresponds with block id
reg [31:0] blocks_done; // number of blocks a core has finished processing
 
// total thread blocks determined from num_threads kernel launches
wire [31:0] num_blocks;
assign num_blocks = (num_threads + block_dim - 1) / block_dim; 

localparam signed [31:0] INVALID_BLOCK_ID = -32'd1;

integer i;
always @ (posedge(clk)) begin
    if (rst) begin
        blocks_dispatched <= 0;
        blocks_done <= 0;
        kernel_done <= 0;

        for (i = 0; i < NUM_CORES; i = i + 1) begin
            core_block_id[i] <= INVALID_BLOCK_ID;
            core_ready[i] <= 1;
            core_start[i] <= 0;      
        end        
    end

    else if (enable) begin
        if (blocks_done == num_blocks) begin
            // all blocks have been processed by compute units
            kernel_done <= 1;
        end

        for (i = 0; i < NUM_CORES; i = i + 1) begin
            if (core_ready[i] && !core_start[i]) begin
                // check if there is a block that can be given
                if (blocks_dispatched < num_blocks) begin
                    core_block_id[i] <= blocks_dispatched; // give a block to a core
                    core_start[i] <= 1;
                    core_ready[i] <= 0;
                    blocks_dispatched = blocks_dispatched + 1; 
                end
            end

            if (core_done[i] && core_start[i]) begin
                // check if a compute unit has finished its block and set it back to ready state
                core_start[i] <= 0;
                core_ready[i] <= 1;
                core_block_id[i] <= INVALID_BLOCK_ID;
                blocks_done = blocks_done + 1;
            end
        end
    end
end

endmodule
