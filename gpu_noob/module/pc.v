`timescale 1ns/1ps

// Each SIMD unit comes with a PC to track each wave
// No branching implemented
module PC #(
    parameter PROGRAM_MEM_ADDR_WIDTH = 32, // program memory addresses are 32b, though actual address space is much smaller
    parameter WAVES_PER_SIMD = 1 // max number of waves/SIMD 
)
(
    input wire clk,
    input wire rst,

    // signals
    input wire UPDATE_PC, // signal to update current wavefront's PC
    input wire DISPATCH_NEW_WAVE, // signal to indicate a new wave was dispatched to SIMD unit

    // contexts
    input wire [$clog2(WAVES_PER_SIMD)-1:0] active_context,

    // outputs
    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_out // PC of the active wavefront
);

reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_contexts [0:WAVES_PER_SIMD-1]; // track PC context for each wave

always @ (posedge(clk)) begin
    if (rst) begin
        integer i;
        for (i = 0; i < WAVES_PER_SIMD; i++) begin
            // reset each context pc value to 0
            pc_contexts[i] <= 0;
        end        
    end

    if (DISPATCH_NEW_WAVE) begin
        // new wave dispatched and starts back at 0
        pc_out <= 0;
        pc_contexts[active_context] <= 0;
    end 

    else if (UPDATE_PC) begin
        // update active context pc
        pc_out <= pc_contexts[active_context] + 1;
        pc_contexts[active_context] <= pc_contexts[active_context] + 1;
    end

    else begin
        // default (resuming to another context)
        pc_out <= pc_contexts[active_context];
    end
end

endmodule
