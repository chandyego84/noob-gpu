import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.utils import get_sim_time
from common import safe_int, signed_int

BLOCK_DIM = 64
WAVE_SIZE = 32
THREADS_FULL = BLOCK_DIM # block is full

'''
For the following THREADS_PARTIAL_FULL:
(Assuming): NUM_SIMDS=2, WAVE_SIZE=32
Since BLOCK_DIM=64 and threads in the block=32,
there is only one warp that can be dispatched from this block.
    -- assuming no prior assignments, SIMD_0 should receive this WARP_0 and no other warp is assigned
'''
THREADS_HALF_FULL = BLOCK_DIM - WAVE_SIZE

async def log_signals(dut):
    cycle = 0
    dut._log.info(f"NUM_SIMDS = {int(dut.NUM_SIMDS.value)}")
    dut._log.info(f"WAVE_SIZE = {int(dut.WAVE_SIZE.value)}")

    while True:
        await RisingEdge(dut.clk)
        curr_ns = get_sim_time(units="ns")
        enable = safe_int(dut.enable.value)
        rst = safe_int(dut.rst.value)
        
        block_id = safe_int(dut.core_block_id.value)
        block_dim = safe_int(dut.block_dim.value)
        num_blocks = safe_int(dut.num_blocks)
        num_threads = safe_int(dut.num_threads.value)
        num_threads_in_block = safe_int(dut.num_actual_block_threads.value)
        num_waves = safe_int(dut.num_waves.value)

        dispatched = safe_int(dut.waves_dispatched.value)
        waves_done = safe_int(dut.waves_done.value)
        block_done = safe_int(dut.block_done.value)

        dut._log.info(
            f"\n---- CLOCK CYCLE: {cycle} @ {curr_ns} ns ----\n"
            f"enable={enable} rst={rst}\n"
            f"block_id={block_id}, block_dim={block_dim}, num_blocks={num_blocks}\n"
            f"total_threads={num_threads}, threads_in_block={num_threads_in_block}\n"
            f"waves dispatched={dispatched}, num_waves={num_waves}\n"
            f"waves_done={waves_done} block_done?={block_done}\n"
        )

        for i in range(int(dut.NUM_SIMDS.value)):
            dut._log.info(
                f"  SIMD {i}: wave_id={signed_int(dut.simd_wave_id[i].value)} "
                f"start={safe_int(dut.simd_start[i].value)} "
                f"simd_ready={safe_int(dut.simd_ready[i].value)} "
                f"simd_working={safe_int(dut.simd_working[i].value)} "
                f"done={safe_int(dut.simd_done[i].value)}"
            )
        cycle += 1

@cocotb.test()
async def test_full_block_wave_dispatch(dut):
    """
    Test wave dispatch module when the block is full
    """

    # start 100MHz clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    cocotb.start_soon(log_signals(dut))

    # reset
    dut.rst.value = 1
    dut.num_threads.value = THREADS_FULL
    dut.block_dim.value = BLOCK_DIM
    dut.core_block_id.value = 0
    dut.simd_done.value = 0 # none of simds are done (nothing processed yet)
    await Timer(20, units="ns") # hold rst to let signals propogate
    dut.rst.value = 0
    dut.enable.value = 1
    await RisingEdge(dut.clk) # rst and enable values are set

    # test -- after rst, wave_IDs for each SIMD should be default invalid values (no waves assigned yet)
    for i in range(dut.NUM_SIMDS.value):
        expected = signed_int(dut.INVALID_WAVE_ID.value)
        actual = signed_int(dut.simd_wave_id[i].value)
        assert actual == expected, f"After reset, wave_ID for SIMD {i} should be {expected}, got {actual}"
    # test waves dispatched, waves done, block done -- all should be 0 
    assert dut.waves_dispatched.value == 0, "After rst, waves dispatched should be 0"
    assert dut.waves_done.value == 0, "After rst, waves done should be 0"
    assert dut.block_done == 0, "After rst, block_done should be 0"

    await RisingEdge(dut.clk) # enable propogated
    # test -- all SIMDs have correct warp_id
    for i in range(int(dut.NUM_SIMDS.value)):
        exp_wave_id = i
        act_warp_id = signed_int(dut.simd_wave_id[i].value)
        assert act_warp_id == exp_wave_id, f"After enable=1, SIMD {i} should have warp_id {exp_wave_id}, got {act_warp_id}"
        act_working_state = safe_int(dut.simd_working[i].value)
        assert act_working_state == 1, f"For SIMD {i}: With warp_id {act_warp_id}, working_state should be 1, got {act_working_state}"
        # SIMD start states should be HIGH as they were just given new waves
        expected = 1
        actual = safe_int(dut.simd_start[i].value)
        assert expected == actual, f"For SIMD {i}: With warp_id {act_warp_id}, start_state should be 1, got {actual}"
    
    # let SIMDs work for a while
    for i in range(5):
        await RisingEdge(dut.clk)
        dut._log.info(f"SIMDs are working, STEP={i}")

    # test -- SIMD0 finishes its wave
    dut.simd_done[0].value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.simd_done[0].value = 0
    # waves_done test
    actual = safe_int(dut.waves_done.value)
    assert actual == 1, f"SIMD0 is done, waves done should be 1, got {actual}"
    # simd0 is ready for new wave
    actual = safe_int(dut.simd_ready[0].value)
    assert actual == 1, f"SIMD0 finished a wave and should be in ready state (1), got {actual}"

    # test -- SIMD0 looking for a wave, but there are none to give out
    await RisingEdge(dut.clk)
    # wave id should be default (invalid) value
    expected = dut.INVALID_WAVE_ID
    actual = signed_int(dut.simd_wave_id[0].value)
    assert actual == expected, f"SIMD0 is ready but with no more waves to dispatch, SIMD0's wave_id should be {expected}, got {actual}"

    # test -- SIMD1 finishes its wave
    dut.simd_done[1].value = 1
    await RisingEdge(dut.clk) # simd_done set
    await RisingEdge(dut.clk) # simd_done processed
    dut.simd_done[1].value = 0
    # waves_done test
    actual = safe_int(dut.waves_done.value)
    assert actual == 2, f"SIMD1 is done, waves done should be 2, got {actual}"
    # simd1 is ready for new wave
    actual = safe_int(dut.simd_ready[1].value)
    assert actual == 1, f"SIMD1 finished a wave, should be in ready state (1), got {actual}"
    await RisingEdge(dut.clk)
    # block is done
    actual = safe_int(dut.block_done.value)
    assert actual == 1, f"All waves done, block_done should be 1, got {actual}"

@cocotb.test()
async def test_half_full_block_wave_dispatch(dut):
    """
    Test wave dispatch module when the block is only half-filled
    """
    # start 100MHz clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    cocotb.start_soon(log_signals(dut))

    # reset
    dut.rst.value = 1
    dut.num_threads.value = THREADS_HALF_FULL
    dut.block_dim.value = BLOCK_DIM
    dut.core_block_id.value = 0
    dut.simd_done.value = 0 # none of simds are done (nothing processed yet)
    await Timer(20, units="ns") # hold rst to let signals propogate
    dut.rst.value = 0
    dut.enable.value = 1
    await RisingEdge(dut.clk) # rst and enable values are set

    # test -- after rst, wave_IDs for each SIMD should be default invalid values (no waves assigned yet)
    for i in range(dut.NUM_SIMDS.value):
        expected = signed_int(dut.INVALID_WAVE_ID.value)
        actual = signed_int(dut.simd_wave_id[i].value)
        assert actual == expected, f"After reset, wave_ID for SIMD {i} should be {expected}, got {actual}"
    # test waves dispatched, waves done, block done -- all should be 0 
    assert dut.waves_dispatched.value == 0, "After rst, waves dispatched should be 0"
    assert dut.waves_done.value == 0, "After rst, waves done should be 0"
    assert dut.block_done == 0, "After rst, block_done should be 0"

    await RisingEdge(dut.clk) # enable propogated
    # test -- all SIMDs have correct wave_id
    act_wave_id = signed_int(dut.simd_wave_id[0].value) # SIMD0 wave id
    assert act_wave_id == 0, f"After enable=1, SIMD 0 should have warp_id 0, got {act_wave_id}"
    exp_wave_id = signed_int(dut.INVALID_WAVE_ID.value)
    act_wave_id = signed_int(dut.simd_wave_id[1].value) # SIMD1 wave id
    assert act_wave_id == exp_wave_id, f"After enable=1, SIMD 1 should have warp_id {exp_wave_id}, got {act_wave_id}"
    # test -- SIMD0 was assigned a new wave, SIMD1 wasn't.
        # check start_states
    # SIMD0
    expected = 1
    actual = safe_int(dut.simd_start[0].value)
    assert expected == actual, f"SIMD0 was given new wave, start_state should be 1, got {actual}"
    # SIMD1
    expected = 0
    actual = safe_int(dut.simd_start[1].value)
    assert expected == actual, f"SIMD1 wasn't given a wave, start_state should be 0, got {actual}"
    
    # let SIMDs work for a while
    for i in range(5):
        await RisingEdge(dut.clk)
        dut._log.info(f"SIMDs are working, STEP={i}")

    # test -- SIMD0 finishes its wave
    dut.simd_done[0].value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.simd_done[0].value = 0
    # waves_done test
    actual = safe_int(dut.waves_done.value)
    assert actual == 1, f"SIMD0 is done, waves done should be 1, got {actual}"
    # simd0 is ready for new wave
    actual = safe_int(dut.simd_ready[0].value)
    assert actual == 1, f"SIMD0 finished a wave and should be in ready state (1), got {actual}"
    # block_done test 
    await RisingEdge(dut.clk)
    actual = safe_int(dut.block_done.value)
    assert actual == 1, f"All waves ({safe_int(dut.num_waves.value)} are done, block_done should be 1, got {actual})"

    # test -- simd0 is looking for wave, but none to give out
    await RisingEdge(dut.clk)
    # wave id should be default value for wave 0 now
    expected = signed_int(dut.INVALID_WAVE_ID)
    actual = signed_int(dut.simd_wave_id[0].value)
    assert actual == expected, f"SIMD0 is ready but with no more waves to dispatch, SIMD0's wave_id should be {expected}, got {actual}"
    # final check for simd1 to still have default wave_id
    expected = signed_int(dut.INVALID_WAVE_ID)
    actual = signed_int(dut.simd_wave_id[0].value)
    assert actual == expected, f"SIMD1 should still have default wave_id {expected} from start, got {actual}"