`timescale 1ns/1ps
// Wavedispatcher --> 2 SIMDs (wavedispatcher holds up to one block)
// Dispatches waves to SIMDs in a compute unit
    // Track which SIMDs are ready to accept a new wavefront
    // Dispatch a new wave to a SIMD when it is available
    // Signals SIMDs to start execution on their waves
    // Track completions of waves and of its current block
// Assumes:
    // Our SIMD units can only hold up to one wave
    // All blocks are full, except for possibility of the last block in a block grid to be partially filled
module WaveDispatch #(
    parameter NUM_SIMDS = 2,
    parameter WAVE_SIZE = 32
)
(
    input wire clk,
    input wire rst,
    input wire enable,
    
    // kernel metadata
    input wire [31:0] num_threads, // num of total threads -- defined by kernel
    input wire [31:0] block_dim, // num of threads per block -- defined by kernel 
    
    input wire signed [31:0] core_block_id, // assigned block_id for corresponding CU
    
    input wire [NUM_SIMDS-1:0] simd_done, // SIMD signals for SIMD completing a wave

    output reg [NUM_SIMDS-1:0] simd_start, // high for when new wave given to SIMD to start working on
    output reg [NUM_SIMDS-1:0] simd_ready, // high for when SIMD can take a new wave

    output reg signed [31:0] simd_wave_id [0:NUM_SIMDS-1], // wave_id for a SIMD

    output reg block_done // signal for when all warps are processed (current block is done)
);

localparam signed [31:0] INVALID_WAVE_ID = -32'd1;

// internal states
reg [31:0] waves_dispatched; 
reg [31:0] waves_done;
reg [31:0] num_actual_block_threads; // num of threads in current block

wire [31:0] num_blocks;
assign num_blocks = (num_threads + block_dim - 1) / block_dim;

// calculate actual number of threads for the current block
    // (last block might be partially filled)
wire [31:0] remainder;
assign remainder = num_threads % block_dim;
always @ (*) begin
    if (core_block_id == (num_blocks - 1)) begin
        num_actual_block_threads = (remainder == 0) ? block_dim : (block_dim - remainder);
    end

    else begin
        num_actual_block_threads = block_dim;
    end
end

// how many waves in the current block -- depends on number of actual threads on the current block
wire [31:0] num_waves; // num of waves in current block
assign num_waves = (num_actual_block_threads + WAVE_SIZE - 1) / WAVE_SIZE;

integer i;
always @ (posedge(clk)) begin
    // rst = HIGH
    if (rst) begin
        waves_dispatched <= 0;
        waves_done <= 0;
        block_done <= 0;

        for (i = 0; i < NUM_SIMDS; i = i + 1) begin
            simd_wave_id[i] <= INVALID_WAVE_ID;
            simd_ready[i] <= 1;
            simd_start[i] <= 0;
        end
    end

    else if (enable) begin
        // check if current block is done (all waves are done)
        if (waves_done == num_waves) begin
            block_done <= 1; 
        end

        else begin
            for (i = 0; i < NUM_SIMDS; i = i + 1) begin
                // check for ready SIMD units to be given waves
                if ((waves_dispatched < num_waves) && simd_ready[i] && !simd_start[i]) begin
                    simd_wave_id[i] <= waves_dispatched;
                    simd_start[i] <= 1;
                    simd_ready[i] <= 0;
                    waves_dispatched = waves_dispatched + 1;                               
                end

                if (simd_done[i] && simd_start[i]) begin
                    // check if a simd finished processing its wave and set it back to ready
                    simd_start[i] <= 0;
                    simd_ready[i] <= 1;
                    simd_wave_id[i] <= INVALID_WAVE_ID;
                    waves_done = waves_done + 1;
                end
            end
        end
    end
end

endmodule