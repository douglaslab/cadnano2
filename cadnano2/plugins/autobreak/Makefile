$(eval PYUIC_VERSION = -v $(shell pyuic5 -version 2> /dev/null):/output)

all: autobreakconfig_ui.py

autobreakconfig_ui.py : autobreakconfig.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif