OPENMP_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
include $(OPENMP_DIR)/../common.mk

OMPFLAGS = -fopenmp -I$(LLVM_BUILD_PATH)/include

CFLAGS   += $(OMPFLAGS) -D__FOR_PSCHEN_THESIS -I..
CXXFLAGS   += $(OMPFLAGS) -D__FUCK_FOR_THESIS__ -D__FOR_PSCHEN_THESIS -I..
LDLIBS   += $(OMPFLAGS)

ifdef OFFLOAD
$(warning "OFFLOAD enabled")
OMPOFFLOADFLAGS := -DOMP_OFFLOAD -fopenmp-targets=nvptx64 -I..
ifdef OMP_MASK
$(warning "MASK enabled")
OMPOFFLOADFLAGS += -DOMP_MASK -DOMP_DCAT
OMPOFFLOADFLAGS += -L $(LLVM_BUILD_PATH)/lib
OMPOFFLOADFLAGS += -lomptarget
endif
ifdef OMP_OFFSET
$(warning "OFFSET enabled")
OMPOFFLOADFLAGS += -DOMP_OFFSET -DOMP_DCAT
OMPOFFLOADFLAGS += -L $(LLVM_BUILD_PATH)/lib
OMPOFFLOADFLAGS += -lomptarget
endif
ifdef OMP_UVM
$(warning "UVM enabled")
OMPOFFLOADFLAGS += -DOMP_DCAT
OMPOFFLOADFLAGS += -L $(LLVM_BUILD_PATH)/lib
OMPOFFLOADFLAGS += -lomptarget
endif
CXXFLAGS += $(OMPOFFLOADFLAGS)
CFLAGS += $(OMPOFFLOADFLAGS)
LDLIBS += $(OMPOFFLOADFLAGS)
endif

ifdef DC
$(warning "DC enabled")
OMPDCFLAGS = -DOMP_DC
CXXFLAGS += $(OMPDCFLAGS)
CFLAGS += $(OMPDCFLAGS)
endif

ifdef PG
PGFLAGS = -pg
CXXFLAGS += $(PGFLAGS)
CFLAGS += $(PGFLAGS)
endif
