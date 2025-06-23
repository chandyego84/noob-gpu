`timescale 1ns/1ps
`include "common_defs.v"

/**
--------------------------------------
Load/Store Unit
--------------------------------------
* Manages load and store instructions
* Each lane in a SIMD has its own LSU
*/

module LSU # (
    DATA_WIDTH = 64,
    DATA_REG_ADDR_WIDTH = 7
)
(
    /*INPUTS START*/
    input wire clk,
    input wire rst,
    input wire enable,

    input wire [2:0] simd_state,

    // register values
        // load: Rd = global_mem[Rm]
        // store: global_mem[Rm] = Rn
    input wire [DATA_REG_ADDR_WIDTH-1:0] rm, 
    input wire [DATA_REG_ADDR_WIDTH-1:0] rn,

    // enable signals -- which op to perform
    input wire MEM_READ,
    input wire MEM_WRITE,

    // from data memory inputs
    input wire mem_read_ack,
    input wire mem_write_ack,
    input wire [DATA_WIDTH-1:0] mem_read_data,
    /*INPUTS END*/

    /*OUTPUTS START*/
    // data memory outputs
    output reg mem_read_valid, // initiate mem_read signal
    output reg mem_write_valid, // initiate mem_write signal
    output reg [DATA_REG_ADDR_WIDTH-1:0] mem_addr,
    output reg [DATA_WIDTH-1:0] mem_write_data, 

    // outputs
    output reg [1:0] lsu_state,
    output reg [DATA_WIDTH-1:0] lsu_read_out
    /*OUTPUTS END*/
);

always @ (posedge(clk)) begin
    if (rst) begin
        lsu_state <= LSU_IDLE;
        lsu_read_out <= 0;
        // data mem outputs
        mem_read_valid <= 0;
        mem_write_valid <= 0;
        mem_addr <= 0;
        mem_write_data <= 0;
    end

    else if (enable) begin
        if (MEM_READ) begin
            case (lsu_state) 
                `LSU_IDLE: begin
                    if (simd_state == `SIMD_REQUEST) begin
                        // SIMD is making request to LSU
                        lsu_state <= `LSU_REQUESTING;
                    end
                end

                `LSU_REQUESTING: begin
                    // give signal/data to memory
                    mem_read_valid <= 1;
                    mem_addr <= rm;
                    lsu_state <= `LSU_WAITING;
                end

                `LSU_WAITING: begin
                    if (mem_read_ack) begin
                        // mem_read done/acked
                        mem_read_valid <= 0;
                        lsu_read_out <= mem_read_data;
                        lsu_state <= LSU_DONE;
                    end
                end

                `LSU_DONE: begin
                    if (simd_state == `SIMD_UPDATE) begin
                        // simd state == UPDATE
                        lsu_state <= `LSU_IDLE;
                    end
                end
            endcase
        end

        else if (MEM_WRITE) begin
            case(lsu_state)
                `LSU_IDLE: begin
                    // SIMD state == REQUEST
                    if (simd_state == `SIMD_REQUEST) begin
                        lsu_state <= `LSU_REQUESTING;
                    end
                end

                `LSU_REQUESTING: begin
                    // give signal/data to memory
                    mem_write_valid <= 1;
                    mem_addr <= rm;
                    mem_write_data <= rn;
                    lsu_state <= LSU_WAITING;
                end

                `LSU_WAITING: begin
                    if (mem_write_ack) begin
                        // mem_write done/acked
                        mem_write_valid <= 1;
                        lsu_state <= `LSU_DONE;
                    end
                end

                `LSU_DONE: begin
                    if (simd_state == `SIMD_UPDATE) begin
                        // simd state == UPDATE
                        lsu_state <= `LSU_IDLE;
                    end
                end
            endcase
        end
    end
end



endmodule