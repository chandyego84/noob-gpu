`ifndef COMMON_DEFS_V
`define COMMON_DEFS_V

/*
SIMD States
}

*/
`define SIMD_IDLE       3'b000
`define SIMD_FETCH      3'b001
`define SIMD_DECODE     3'b010
`define SIMD_REQUEST    3'b011
`define SIMD_WAIT       3'b100
`define SIMD_EXECUTE    3'b101
`define SIMD_UPDATE     3'b110
`define SIMD_DONE       3'b111 

/*
Fetcher states
*/
`define FETCHER_IDLE        2'b00
`define FETCHER_FETCHING    2'b01
`define FETCHER_FETCHED     2'b10

/*
LSU States
*/
`define LSU_IDLE        2'b00
`define LSU_REQUESTING  2'b01
`define LSU_WAITING     2'b10
`define LSU_DONE        2'b11

/*
OP Codes
*/
`define OP_LOAD         6'b000000
`define OP_STORE        6'b000001
`define OP_ADD          6'b000010
`define OP_SUB          6'b000011
`define OP_MUL          6'b000100
`define OP_DIV          6'b000101
`define OP_AND          6'b000110
`define OP_ORR          6'b000111
`define OP_CONST        6'b001000
`define OP_RET          6'b111111

/*
ALU OP Codes
*/
`define ALU_ADD         3'b000
`define ALU_SUB         3'b001
`define ALU_MUL         3'b010
`define ALU_DIV         3'b011
`define ALU_AND         3'b100
`define ALU_ORR         3'b101

/*
REG_WRITE INPUT MUX
*/
`define REG_WRITE_LOAD      2'b00
`define REG_WRITE_ALU       2'b01
`define REG_WRITE_IMM       2'b10

`endif