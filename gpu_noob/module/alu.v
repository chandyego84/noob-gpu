`timescale 1ns/1ps
`include "common_defs.v"

/**
--------------------------------------
ALU Unit
--------------------------------------
* Each lane in a SIMD has its own ALU
*/
module ALU # (
    parameter DATA_WIDTH = 64
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    input wire [2:0] simd_state,
    input wire [DATA_WIDTH-1:0] rm_data,
    input wire [DATA_WIDTH-1:0] rn_data,
    input wire [2:0] alu_op,

    output reg [DATA_WIDTH-1:0] alu_out
);

always @ (posedge(clk)) begin
    if (rst) begin
        alu_out <= 0;
    end

    else if (enable) begin
        if (simd_state == `SIMD_EXECUTE) begin
            case (alu_op) 
                `ALU_ADD: alu_out <= rm_data + rn_data;

                `ALU_SUB: alu_out <= rm_data - rn_data;

                `ALU_MUL: alu_out <= rm_data * rn_data;

                `ALU_DIV: alu_out <= rm_data / rn_data;
                
                `ALU_AND: alu_out <= rm_data & rn_data;

                `ALU_ORR: alu_out <= rm_data | rn_data;

                default: alu_out <= 0;
            endcase
        end
    end
end

endmodule