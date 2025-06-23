# === Simulator and Language ===
SIM             ?= icarus
TOPLEVEL_LANG   ?= verilog
WAVE            ?= 0

# === Design and Testbench Modules ===
DUT             ?= RegisterFile
TESTBENCH       ?= register_tb

TOPLEVEL        ?= $(DUT)
MODULE          ?= $(TESTBENCH)

# === Source File Paths ===
VERILOG_SOURCES = \
    $(PWD)/module/block_dispatch.v \
    $(PWD)/module/common_defs.v \
    $(PWD)/module/lsu.v \
    $(PWD)/module/pc.v \
    $(PWD)/module/register.v \
    $(PWD)/module/simd.v \
    $(PWD)/module/simd_controller.v \
    $(PWD)/module/wave_dispatch.v

# === Verilog Include Directories ===
VERILOG_INCLUDE_DIRS := $(PWD)/module

# === Python Path for test modules ===
PYTHONPATH := $(PWD)/test:$(PYTHONPATH)

# === Optional: Enable Waveform Output ===
ifeq ($(WAVE),1)
    export WAVES=1
    export COCOTB_VCD_WAVEFORM=wave.vcd
endif

# === Export for Cocotb ===
export VERILOG_SOURCES
export VERILOG_INCLUDE_DIRS
export TOPLEVEL
export MODULE
export PYTHONPATH

# === Import cocotb Makefile ===
include $(shell cocotb-config --makefiles)/Makefile.sim
