IMAGES = mainwindow/images/data-svg.png mainwindow/images/data-new_32.png mainwindow/images/data-open_32.png mainwindow/images/data-save_32.png mainwindow/images/part-new-honeycomb.png mainwindow/images/part-new-square.png mainwindow/images/slice-delete-last.png mainwindow/images/slice-move.png mainwindow/images/slice-renumber.png mainwindow/images/slice-edit.png mainwindow/images/slice-go-last.png mainwindow/images/slice-go-first.png mainwindow/images/add-bases.svg mainwindow/images/remove-bases.svg mainwindow/images/path-insert.png mainwindow/images/path-pen_48.png mainwindow/images/path-paint_48.png mainwindow/images/path-move.png mainwindow/images/path-skip.png mainwindow/images/path-force-xover.png mainwindow/images/path-break_48.png mainwindow/images/path-erase_32.png mainwindow/images/path-edit_32.png mainwindow/images/export-staples.png mainwindow/images/path-modify.png mainwindow/images/path-addseq.png mainwindow/images/path-autobreak.png mainwindow/images/part-filter-part.png mainwindow/images/part-filter-endpoint.png mainwindow/images/part-filter-xover.png mainwindow/images/part-filter-strand.png
DIALOGIMAGES = dialogs/images/path-edit_32.png dialogs/images/path-force-xover.png dialogs/images/path-paint_48.png

$(eval PYUIC_VERSION = -v $(shell pyuic5 -version 2> /dev/null):/output)
$(eval PYRCC_VERSION = -v $(shell pyrcc5 -version 2> /dev/null):/output)

all: mainwindow/icons_rc.py mainwindow/ui_mainwindow.py dialogs/dialogicons_rc.py dialogs/ui_preferences.py dialogs/ui_latticetype.py dialogs/ui_addseq.py dialogs/ui_about.py dialogs/ui_warning.py

mainwindow/icons_rc.py : mainwindow/ui.mainwindow.icons.qrc $(IMAGES)
ifdef PYRCC_VERSION
	pyrcc5 -o $@ $<
else
	@echo "ERROR:  pyrcc5 not found 1" $(PYUIC_VERSION) $(PYRCC_VERSION)
	pyrcc5 -o $@ $<
endif

dialogs/dialogicons_rc.py : dialogs/ui.dialogs.dialogicons.qrc $(DIALOGIMAGES)
ifdef PYRCC_VERSION
	pyrcc5 -o $@ $<
else
	@echo "ERROR:  pyrcc5 not found 2" $(PYUIC_VERSION) $(PYRCC_VERSION)
endif

mainwindow/ui_mainwindow.py : mainwindow/mainwindow.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif

dialogs/ui_preferences.py : dialogs/preferences.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif

dialogs/ui_latticetype.py : dialogs/latticetype.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif

dialogs/ui_addseq.py : dialogs/addseq.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif

dialogs/ui_about.py : dialogs/about.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif

dialogs/ui_warning.py : dialogs/warning.ui
ifdef PYUIC_VERSION
	pyuic5 $< > $@
else
	@echo "ERROR:  pyuic5 not found"
endif

