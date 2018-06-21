## 2.0.1

* Fixed circular scaffold highlighting when opening from an nno file.
* OSX: Reconnected objc bridge so files open via double-click or dock icon drop.
* Fixed bug in display of square-lattice crossover locations.
* Square lattice canvas extension now happens in 32-base steps.
* Updated icon for AddSeq Tool.
* Moved Frame button to the View menu and moved AutoStaple button to the top toolbar.


## 2.0.0

* Undo/redo.
* Unified interface for square-lattice and honeycomb-lattice parts. The new workflow is to open a document and then click the "Honeycomb" or "Square" button on the top toolbar to create a new part for editing.
* Stored user preferences.
* Scroll to zoom (e.g. via mousewheel). Command+mouse-drag to pan.
* Pencil tool: Left-click to create or destroy staple or scaffold. Right-click to create a forced crossover.
* DNA sequences are displayed live in the interface.
* Export button: creates a staple csv file, replacing the old SeqTool copy-to-clipboard dialog.
* Frame button: zoom-to-fit of path view.
* New file format (.nno extension)
* Loop is renamed to Insert. Its size can be edited in place via its numeric label.
* Multiple helices can be reordered by selecting the helix labels (leftmost orange circle) and dragging the group.
* Delete-Last button removed. To delete a helix, selecting its label and press delete.
* 3D view is removed. See planned features for future replacement. 