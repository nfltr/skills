# make check: the gate. CI runs the same target.
# The nfltr release the command check runs against; bump it when a skill
# documents a newer command or flag.
NFLTR_VERSION ?= v2.1.37
BIN := .cache/nfltr-$(NFLTR_VERSION)
CLAUDE ?= $(shell command -v claude)

.PHONY: check
check: $(BIN)/nfltr
	python3 scripts/check.py --nfltr $(BIN)/nfltr $(if $(CLAUDE),--claude $(CLAUDE))

# The public installer verifies the release signature and checksums.
$(BIN)/nfltr:
	mkdir -p $(BIN)
	curl -fsSL https://nfltr.xyz/install.sh | NFLTR_VERSION=$(NFLTR_VERSION) NFLTR_INSTALL_DIR=$(CURDIR)/$(BIN) sh -s -- --with orch
