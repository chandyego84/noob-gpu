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
// LSU States
`define LSU_IDLE        2'b00
`define LSU_REQUESTING  2'b01
`define LSU_WAITING     2'b10
`define LSU_DONE        2'b11


`endif