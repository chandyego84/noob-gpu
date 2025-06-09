`timescale 1ns/1ps

// Each SIMD unit comes with a PC to track each wave
// Assuming:
    // No branching (ugh)
module PC #(
    parameter PROGRAM_MEM_ADDR_WIDTH = 32, // program memory addresses are 32b, though actual address space is much smaller
    parameter NUM_WAVES = 5 // max number of waves/SIMD
)
(
    input wire clk,
    input wire rst,

    // signals
    input wire update_pc, // signal to update current wavefront's PC
    input wire dispatch_new_wave, // signal to indicate a new wave was dispatched to SIMD unit

    // contexts
    input  wire [$clog2(NUM_WAVES)-1:0] active_context,

    // outputs
    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_out // PC of the active wavefront
);

reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_contexts [0:NUM_WAVES-1]; // track PC context for each wave

always @ (posedge(clk)) begin
    if (rst) begin
        integer i;
        for (i = 0; i < NUM_WAVES; i++) begin
            // reset each context pc value to 0
            pc_contexts[i] <= 0;
        end        
    end

    if (dispatch_new_wave) begin
        // new wave dispatched and starts back at 0
        pc_out <= 0;
        pc_contexts[active_context] <= 0;
    end 

    else if (update_pc) begin
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
