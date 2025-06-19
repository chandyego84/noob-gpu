/*
--------------------------------------
Register File (4 KB)
--------------------------------------
// 64b x 32 registers for each lane
// 16 lanes x 32 registers = 512 registers
--------------------------------------
READ-ONLY:
R28-R30: blockIdx, blockDim, threadIdx
R31: zero
--------------------------------------
WRITABLE:
R4-R31: general purpose
--------------------------------------
blockIdx: block's ID within a block grid
blockDim: number of threads per block
threadIdx: thread's ID within a block
*/
module RegisterFile # (
    parameter THREAD_ID_X = 0, // unique for each lane
    parameter DATA_REG_ADDR_WIDTH = 7, 
    parameter DATA_WIDTH = 64,
    parameter NUM_REGISTERS = 32,
)
(
    input wire clk,
    input wire rst,
    input wire enable,

    // kernel metadata
    input wire signed [31:0] block_id,
    input wire [31:0] block_dim,

    // signals
    input wire REG_WRITE,
    
    // registers
    input wire [DATA_REG_ADDR_WIDTH-1:0] rm,
    input wire [DATA_REG_ADDR_WIDTH-1:0] rn,
    input wire [DATA_REG_ADDR_WIDTH-1:0] rd,

    // write data -- from ALU or memory
    input wire [DATA_WIDTH-1:0] write_data, 

    // reading data from registers
    output reg [DATA_WIDTH-1:0] rm_data,
    output reg [DATA_WIDTH-1:0] rn_data
);

reg [DATA_WIDTH-1:0] reg_file [NUM_REGISTERS-1:0];

integer i;
always @ (posedege(clk)) begin
    if (rst) begin
        // initialize read-only registers
        reg_file[28] <= block_id;
        reg_file[29] <= block_dim;
        reg_file[30] <= THREAD_ID_X;
        reg_file[31] <= 0;
        
        for (i = 0; i < 28; i = i + 1) begin
            // initialize general purpose registers
            reg_file[i] <= 0;
        end
        
        // clear output data
        rm_data <= 0;
        rn_data <= 0;
    end

    else begin
        if (enable) begin
            rm_data <= reg_file[rm];
            rn_data <= reg_file[rn];

             // writing only allowed to general purpose registers
            if (REG_WRITE && rd > 3) begin
                reg_file[rd] = write_data;
            end

        end
    end
end

endmodule