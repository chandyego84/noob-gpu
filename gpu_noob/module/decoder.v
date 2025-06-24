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

    // Signals
    output reg REG_WRITE,
    output reg MEM_READ,
    output reg MEM_WRITE,
    output reg [1:0] REG_WRITE_MUX, // MEM, ALU, IMM
    output reg RET,
    output reg [2:0] alu_op,
 
    output reg [6:0] rd,
    output reg [6:0] rm,
    output reg [6:0] rn,
    output reg [18:0] imm_19
);

reg [5:0] op_code;
reg [4:0] other;

always @ (posedge(clk)) begin
    if (rst) begin
        REG_WRITE <= 0;
        MEM_READ <= 0;
        MEM_WRITE <= 0;
        REG_WRITE_MUX <= 0;
        RET <= 0;
        alu_op <= 0;
    end

    else if (enable) begin
        REG_WRITE <= 0;
        MEM_READ <= 0;
        MEM_WRITE <= 0;
        REG_WRITE_MUX <= 0;
        RET <= 0;
        alu_op <= 0;

        op_code <= instruction[31:26];
        rd <= instruction[25:19];
        rm <= instruction[18:12];
        rn <= instruction[11:5];
        other <= instruction[4:0];
        
        if (simd_state == `SIMD_DECODE) begin
            case (op_code)
                `OP_LOAD: begin
                    REG_WRITE <= 1;
                    MEM_READ <= 1;
                    REG_WRITE_MUX <= `REG_WRITE_LOAD;
                end

                `OP_STORE: begin
                    MEM_WRITE <= 0;
                end

                `OP_ADD: begin
                    REG_WRITE <= 1;
                    alu_op <= `ALU_ADD;
                    REG_WRITE_MUX <= `REG_WRITE_ALU;
                end

                `OP_SUB: begin
                    REG_WRITE <= 1;
                    alu_op <= `ALU_SUB;
                    REG_WRITE_MUX <= `REG_WRITE_ALU;
                end

                `OP_MUL: begin
                    REG_WRITE <= 1;
                    alu_op <= `ALU_MUL;
                    REG_WRITE_MUX <= `REG_WRITE_ALU;
                end

                `OP_DIV: begin
                    REG_WRITE <= 1;
                    alu_op <= `ALU_DIV;
                    REG_WRITE_MUX <= `REG_WRITE_ALU;
                end

                `OP_AND: begin
                    REG_WRITE <= 1;
                    alu_op <= `ALU_AND;
                    REG_WRITE_MUX <= `REG_WRITE_ALU;
                end

                `OP_ORR: begin
                    REG_WRITE <= 1;
                    alu_op <= `ALU_ORR;
                    REG_WRITE_MUX <= `REG_WRITE_ALU;
                end

                `OP_CONST: begin
                    REG_WRITE <= 1;
                    REG_WRITE_MUX <= `REG_WRITE_IMM;
                    imm_19 <= {rm, rn, other};
                end

                `OP_RET: begin
                    RET <= 1;
                end
            endcase
        end
    end

end

endmodule