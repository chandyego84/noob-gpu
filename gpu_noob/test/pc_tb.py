import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.utils import get_sim_time
from common import safe_int, signed_int

async def log_signals(dut):
    signals = {
        "clk": dut.clk,
        "rst": dut.rst,
        "DISPATCH_NEW_WAVE": dut.DISPATCH_NEW_WAVE,
        "active_context": dut.active_context,
        "UPDATE_PC": dut.UPDATE_PC,
        "pc_out": dut.pc_out
    }
    cycle = 0
    while True:
        await RisingEdge(dut.clk)
        log_entries = []
        for name, sig in signals.items():
                log_entries.append(f"{name}={sig.value}")
        log_line = f"Cycle {cycle}: " + " | ".join(log_entries)
        dut._log.info(log_line)
        cycle += 1

async def log_signals(dut):
    cycle = 0
    dut._log.info(f"PROGRAM_MEM_ADDR_WIDTH = {safe_int(dut.PROGRAM_MEM_ADDR_WIDTH.value)}")

    while True:
        await RisingEdge(dut.clk)
        curr_ns = get_sim_time(units="ns")
        
        enable = safe_int(dut.enable.value)
        rst = safe_int(dut.rst.value)
        update_pc = safe_int(dut.UPDATE_PC.value)
        dispatch_new_wave = safe_int(dut.DISPATCH_NEW_WAVE.value)
        pc_in = safe_int(dut.pc_in.value)
        pc_out = safe_int(dut.pc_out.value)

        dut._log.info(
            f"\n---- CLOCK CYCLE: {cycle} @ {curr_ns} ns ----\n"
            f"enable={enable} rst={rst}\n"
            f"UPDATE_PC={update_pc}, NEW_WAVE={dispatch_new_wave}\n"
            f"pc_in={pc_in} pc_out={pc_out}\n"
        )

        cycle += 1


@cocotb.test()
async def test_pc(dut):
    """Test program counter (PC) module functionality."""

    # Start the clock (100 MHz)
    clock = Clock(dut.clk, 10, units="ns")  # 10ns period = 100 MHz
    cocotb.start_soon(clock.start())
    cocotb.start_soon(log_signals(dut))

    # Initial reset
    dut.rst.value = 1
    dut.enable.value = 1
    dut.UPDATE_PC.value = 0
    dut.DISPATCH_NEW_WAVE.value = 0
    await Timer(20, units="ns")  # Hold reset for a while
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Check reset behavior: all internal PCs should be 0
    expected = 0
    actual = safe_int(dut.pc_out.value)
    assert expected == actual, f"On RST, pc_out should be {expected}, got {actual}"

    '''
    # Test wave dispatch: set active_context and DISPATCH_NEW_WAVE
    for i in range(dut.WAVES_PER_SIMD.value):
        dut.active_context.value = i
        dut.DISPATCH_NEW_WAVE.value = 1
        await RisingEdge(dut.clk)
        dut.DISPATCH_NEW_WAVE.value = 0
        assert dut.pc_out.value == 0, f"Expected pc_out = 0 after wave dispatch for context {i}"

    # Test PC update: set UPDATE_PC and check increment
    for c in range(dut.WAVES_PER_SIMD.value):
        # switch to context c
        dut.active_context.value = c
        for i in range(3):  # increment PC 3 times per context
            dut.UPDATE_PC.value = 1
            await RisingEdge(dut.clk)
            dut.UPDATE_PC.value = 0
            await RisingEdge(dut.clk)
            assert dut.pc_out.value == i + 1, f"Expected pc_out = {i + 1}, Actual pc_out = {dut.pc_out.value} for C{c}"
    '''