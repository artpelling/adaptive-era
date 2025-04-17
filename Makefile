#!/usr/bin/env make

.PHONY: clean

getdataset = $(word 2,$(subst /, ,$@))
getscenario = $(word 1, $(subst -, ,$(word 3,$(subst /, ,$@))))
getdte = $(word 1, $(subst /, ,$(word 2,$(subst -, ,$@))))

SMALL = MIRACLE/D1 MIRD/SHORT3
ALL = $(foreach t, MIRACLE, $(addprefix $t/, D1 A1 A1_RED A2 A2_RED R2 R2_RED)) $(foreach t, MIRD, $(addprefix $t/, SHORT3 MID3 LONG3))
DTE = NONE LC DTS

TARGETS = $(foreach t, $(ALL), $(addprefix $t-, $(DTE)))

.$(TARGETS): %: models/%/log.txt

$(addsuffix /log.txt, $(addprefix models/, $(TARGETS))):
	-mkdir -p models/$(getdataset)/$(getscenario)-$(getdte)
	-run-benchmark -dte $(getdte) $(getdataset) -s $(getscenario) > $@

ERR_BENCH = $(foreach t, $(SMALL), $(addprefix $t-, DTS))
MOD_BENCH = $(foreach t, $(ALL), $(addprefix $t-, DTS))
DTE_BENCH = $(foreach t, $(SMALL), $(addprefix $t-, $(DTE)))

error-bench: $(ERR_BENCH)
model-bench: $(MOD_BENCH)
dte-bench: $(DTE_BENCH)

all: error-bench model-bench dte-bench
