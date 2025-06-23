`timescale 1ns/1ps
`include "common_defs.v"

/*
--------------------------------
Decoder
--------------------------------
- Decodes instructions and sets control signals
*/
module Decoder # (
    parameter INSTRUCTION_WIDTH = 32
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // States
    input wire [2:0] simd_state,
    input [INSTRUCTION_WIDTH-1:0] instruction,

    // Decoded outputs
    // SIGNALS
        // REG WRITE
        // mem read -- data mem
        // mem write -- data mem
        // MEM 2 REG mux -- data from memory or ALU to reg file?

    // INSTRUCTION values
        // alu op
        // rd
        // rm
        // rn
        // imm_19 = rd_rm_rn_other
);

endmodule