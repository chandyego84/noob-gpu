# === Simulator and Language ===
SIM             ?= icarus
TOPLEVEL_LANG   ?= verilog
WAVE            ?= 0

# === Design and Testbench Modules ===
DUT             ?= SIMD
TESTBENCH       ?= simd_tb

TOPLEVEL        ?= $(DUT)
MODULE          ?= $(TESTBENCH)

# === Source File Paths ===
VERILOG_SOURCES := $(wildcard $(PWD)/module/*.v)

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
