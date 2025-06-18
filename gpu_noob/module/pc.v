`timescale 1ns/1ps

// Each SIMD unit comes with a PC to track the current wave
// No branching implemented
// Assumptions:
    // Only up to 1 wave per SIMD
module PC #(
    parameter PROGRAM_MEM_ADDR_WIDTH = 32 // program memory addresses are 32b, though actual address space is much smaller
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // signals
    input wire UPDATE_PC, // signal to update current wavefront's PC
    input wire DISPATCH_NEW_WAVE, // signal to indicate a new wave was dispatched to SIMD unit

    input wire [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_in,
    output reg [PROGRAM_MEM_ADDR_WIDTH-1:0] pc_out
);

always @ (posedge(clk)) begin
    if (rst) begin
        pc_out <= 0;
    end

    else begin
        if (enable) begin
            if (DISPATCH_NEW_WAVE) begin
                pc_out <= 0;
            end 

            else if (UPDATE_PC) begin
                pc_out <= pc_in + 1;
            end
        end
    end
end

endmodule
