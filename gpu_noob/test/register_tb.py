import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from common import safe_int

BLOCK_ID = 7
BLOCK_DIM = 64
WAVE_ID = 2
CURR_WAVE_CYCLE = 1
LANE_ID = 3
WAVE_SIZE = 32
LANE_WIDTH = 16

async def reg_logger(dut):
    """Logs the value of each register every clock cycle in a readable format."""
    cycle = 0
    while True:
        await RisingEdge(dut.clk)
        reg_vals = [safe_int(dut.reg_file[i].value) for i in range(32)]

        lines = []
        for i in range(0, 32, 4):
            line = []
            for j in range(4):
                reg_index = i + j
                val = reg_vals[reg_index]
                # Mark read-only registers
                ro_marker = "*" if reg_index >= 28 else " "
                line.append(f"{ro_marker}R{reg_index:02d}={val:<7}")
            lines.append("  ".join(line))

        header = f"[Cycle {cycle:03d}] Register File:"
        body = "\n" + "\n".join(lines)
        note = "(* = read-only)"
        dut._log.info(f"{header}{body}\n{note}")
        cycle += 1

async def reset_and_check_readonly(dut):
    """Check reset and read-only registers."""
    dut._log.info("Asserting reset and initializing kernel metadata.")
    dut.rst.value = 1
    dut.enable.value = 1
    dut.block_id.value = BLOCK_ID
    dut.block_dim.value = BLOCK_DIM
    dut.wave_id.value = WAVE_ID
    dut.curr_wave_cycle.value = CURR_WAVE_CYCLE
    dut.lane_id.value = LANE_ID
    await Timer(10, units="ns")
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Check blockIdx, blockDim, threadIdx, zero
    dut._log.info("Checking read-only registers after reset.")
    assert safe_int(dut.reg_file[28].value) == BLOCK_ID, "blockIdx (R28) incorrect after reset"
    assert safe_int(dut.reg_file[29].value) == BLOCK_DIM, "blockDim (R29) incorrect after reset"
    expected_thread_idx = WAVE_ID * WAVE_SIZE + (CURR_WAVE_CYCLE * LANE_WIDTH + LANE_ID)
    assert safe_int(dut.reg_file[30].value) == expected_thread_idx, f"threadIdx (R30) incorrect after reset, expected {expected_thread_idx}"
    assert safe_int(dut.reg_file[31].value) == 0, "Zero register (R31) should be 0 after reset"

@cocotb.test()
async def test_register_file(dut):
    """Test RegisterFile basic functionality."""

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    cocotb.start_soon(reg_logger(dut))

    dut._log.info("Starting RegisterFile test.")

    # Reset and check read-only registers
    await reset_and_check_readonly(dut)

    # Test writing to general-purpose register (R4)
    dut._log.info("Testing write to general-purpose register R4.")
    dut.REG_WRITE.value = 1
    dut.simd_state.value = 0b110  # UPDATE state
    dut.rd.value = 4
    test_val = 12345
    dut.reg_write_data.value = test_val
    await RisingEdge(dut.clk)
    dut.REG_WRITE.value = 0
    await RisingEdge(dut.clk)
    assert safe_int(dut.reg_file[4].value) == test_val, "Failed to write to general-purpose register R4"

    # Test that writing to read-only register (R28) does not change its value
    dut._log.info("Testing write attempt to read-only register R28.")
    dut.REG_WRITE.value = 1
    dut.simd_state.value = 0b110  # UPDATE state
    dut.rd.value = 28
    dut.reg_write_data.value = 99999
    await RisingEdge(dut.clk)
    dut.REG_WRITE.value = 0
    await RisingEdge(dut.clk)
    assert safe_int(dut.reg_file[28].value) == BLOCK_ID, "Should not be able to write to read-only register R28"

    # Test reading from registers
    dut._log.info("Testing register read (R4 and R5).")
    dut.rm.value = 4
    dut.rn.value = 5
    dut.simd_state.value = 0b011  # REQUEST state
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert safe_int(dut.rm_data.value) == test_val, "rm_data should match value in R4"
    assert safe_int(dut.rn_data.value) == 0, "rn_data should match value in R5 (default 0)"

    # Test writing to R31 (zero register) does not change its value
    dut._log.info("Testing write attempt to zero register R31.")
    dut.REG_WRITE.value = 1
    dut.simd_state.value = 0b110
    dut.rd.value = 31
    dut.reg_write_data.value = 55555
    await RisingEdge(dut.clk)
    dut.REG_WRITE.value = 0
    await RisingEdge(dut.clk)
    assert safe_int(dut.reg_file[31].value) == 0, "Zero register (R31) should always be 0"

    dut._log.info("RegisterFile test passed.")