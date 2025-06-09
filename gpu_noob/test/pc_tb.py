import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer
import random

async def log_signals(dut):
    signals = {
        "clk": dut.clk,
        "rst": dut.rst,
        "dispatch_new_wave": dut.dispatch_new_wave,
        "active_context": dut.active_context,
        "update_pc": dut.update_pc,
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

@cocotb.test()
async def test_pc(dut):
    """Test program counter (PC) module functionality."""

    # Start the clock (100 MHz)
    clock = Clock(dut.clk, 10, units="ns")  # 10ns period = 100 MHz
    cocotb.start_soon(clock.start())
    cocotb.start_soon(log_signals(dut))

    # Initial reset
    dut.rst.value = 1
    dut.update_pc.value = 0
    dut.dispatch_new_wave.value = 0
    dut.active_context = 0
    await Timer(20, units="ns")  # Hold reset for a while
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Check reset behavior: all internal PCs should be 0
    for i in range(5):  # NUM_WAVES = 5
        dut.active_context.value = i
        assert dut.pc_out.value == 0, f"Expected pc_out = 0 after reset for context {i}"

    # Test wave dispatch: set active_context and dispatch_new_wave
    for i in range(5):
        dut.active_context.value = i
        dut.dispatch_new_wave.value = 1
        await RisingEdge(dut.clk)
        dut.dispatch_new_wave.value = 0
        assert dut.pc_out.value == 0, f"Expected pc_out = 0 after wave dispatch for context {i}"

    # Test PC update: set update_pc and check increment
    for c in range(5):
        # switch to context c
        dut.active_context.value = c
        for i in range(3):  # increment PC 3 times per context
            dut.update_pc.value = 1
            await RisingEdge(dut.clk)
            dut.update_pc.value = 0
            await RisingEdge(dut.clk)
            assert dut.pc_out.value == i + 1, f"Expected pc_out = {i + 1}, Actual pc_out = {dut.pc_out.value} for C{c}"