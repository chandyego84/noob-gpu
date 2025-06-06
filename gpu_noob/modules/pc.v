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
    input wire [2:0] active_context, // which wave is active - 3b to hold up to 5 waves, but noobGPU SIMD unit can only hold up to 1 for simplicity

    // outputs
    output wire [31:0] current_pc // PC of the active wavefront
);

reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_contexts [0:NUM_WAVES-1]; // track PC context for each wave

always @ (posedge(clk)) begin
    if (rst) begin
        integer i;
        for (i = 0; i < NUM_WAVES; i++) begin
            pc_contexts[i] <= 32'b0;
        end        
    end

    else begin
        if (dispatch_new_wave) begin
            // new wave was dispatched, reset it to 0            
            pc_contexts[active_context] <= 32'b0;
        end

        else if (update_pc) begin
            // update current wave's PC
            pc_contexts[active_context] <= pc_contexts[active_context] + 1;
        end
    end
end

assign current_pc = pc_contexts[active_context];

endmodule
