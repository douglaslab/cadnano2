"""
styles.py

Created by Shawn on 2010-06-15.
"""

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtGui', globals(), [ 'QColor', 'QFont', 'QFontMetricsF'])

# Slice Sizing
SLICE_HELIX_RADIUS = 15
SLICE_HELIX_STROKE_WIDTH = 0.5
SLICE_HELIX_HILIGHT_WIDTH = 2.5
SLICE_HELIX_MOD_HILIGHT_WIDTH = 1
HONEYCOMB_PART_MAXROWS = 30
HONEYCOMB_PART_MAXCOLS = 32
HONEYCOMB_PART_MAXSTEPS = 2
SQUARE_PART_MAXROWS = 50
SQUARE_PART_MAXCOLS = 50
SQUARE_PART_MAXSTEPS = 2

# Slice Colors
bluefill = QColor(153, 204, 255)  # 99ccff
bluestroke = QColor(0, 102, 204)  # 0066cc
bluishstroke = QColor(0, 182, 250)  # 
orangefill = QColor(255, 204, 153)  # ffcc99
orangestroke = QColor(204, 102, 51)  # cc6633
lightorangefill = QColor(255, 234, 183)
lightorangestroke = QColor(234, 132, 81)
grayfill = QColor(238, 238, 238)  # eeeeee (was a1a1a1)
graystroke = QColor(102, 102, 102)  # 666666 (was 424242)

# Path Sizing
VIRTUALHELIXHANDLEITEM_RADIUS = 30
VIRTUALHELIXHANDLEITEM_STROKE_WIDTH = 2
PATH_BASE_WIDTH = 20  # used to size bases (grid squares, handles, etc)
PATH_HELIX_HEIGHT = 2 * PATH_BASE_WIDTH  # staple + scaffold
PATH_HELIX_PADDING = 50 # gap between PathHelix objects in path view
PATH_GRID_STROKE_WIDTH = 0.5
SLICE_HANDLE_STROKE_WIDTH = 1
PATH_STRAND_STROKE_WIDTH = 3
PATH_STRAND_HIGHLIGHT_STROKE_WIDTH = 8
PATH_SELECTBOX_STROKE_WIDTH = 1.5
PCH_BORDER_PADDING = 1
PATH_BASE_HL_STROKE_WIDTH = 2  # PathTool highlight box
MINOR_GRID_STROKE_WIDTH = 0.5
MAJOR_GRID_STROKE_WIDTH = 0.5
oligoLenBelowWhichHighlight = 20
oligoLenAboveWhichHighlight = 49

# Path Drawing
PATH_XOVER_LINE_SCALE_X = 0.035
PATH_XOVER_LINE_SCALE_Y = 0.035

# Path Colors
scaffold_bkg_fill = QColor(230, 230, 230)
activeslicehandlefill = QColor(255, 204, 153, 128)  # ffcc99
activeslicehandlestroke = QColor(204, 102, 51, 128)  # cc6633
minorgridstroke = QColor(204, 204, 204)  # 999999
majorgridstroke = QColor(153, 153, 153)  # 333333
scafstroke = QColor(0, 102, 204)  # 0066cc
handlefill = QColor(0, 102, 204)  # 0066cc
pxi_scaf_stroke = QColor(0, 102, 204, 153)
pxi_stap_stroke = QColor(204, 0, 0, 153)
pxi_disab_stroke = QColor(204, 204, 204, 255)
redstroke = QColor(204, 0, 0)
erasefill = QColor(204, 0, 0, 63)
forcefill = QColor(0, 255, 255, 63)
breakfill = QColor(204, 0, 0, 255)
colorbox_fill = QColor(204, 0, 0)
colorbox_stroke = QColor(102, 102, 102)
stapColors = [
    QColor(204,   0,   0), #cc0000
    QColor(247,  67,   8), #f74308
    QColor(247, 147,  30), #f7931e
    QColor(170, 170,   0), #aaaa00
    QColor( 87, 187,   0), #57bb00
    QColor(  0, 114,   0), #007200
    QColor(  3, 182, 162), #03b6a2
    QColor( 23,   0, 222), #1700de
    QColor(115,   0, 222), #7300de
    QColor(184,   5, 108), #b8056c
    QColor( 51,  51,  51), #333333
    QColor(136, 136, 136)  #888888
]

scafColors = [
    QColor(  0, 102, 204), #0066cc
    QColor(102,   0,   0), #990000
    QColor(139,  48,   6), #b83006
    QColor(198, 125,  23), #c67d17
    QColor(136, 136,   0), #888800
    QColor( 68, 119,   0), #447700
    QColor(  0,  85,   0), #005500
    QColor( 15,   0, 183), #0f00b7
    QColor( 91,   0, 171), #5b00ab
    QColor(157,   5, 108),  #9d034f
    QColor(  2, 126, 130), #027e82
]

DEFAULT_STAP_COLOR = "#888888"
DEFAULT_SCAF_COLOR = "#0066cc"
selected_color = QColor(255, 51, 51) #ff3333

# brightColors = [QColor() for i in range(10)]
# for i in range(len(brightColors)):
#     brightColors[i].setHsvF(i/12.0, 1.0, 1.0)
# bright_palette = Palette(brightColors)
# cadnn1_palette = Palette(cadnn1Colors)
# default_palette = cadnn1_palette

# Loop/Insertion path details
INSERTWIDTH = 2
SKIPWIDTH = 2

# Add Sequence Tool
INVALID_DNA_COLOR = QColor(255, 224, 224)
UNDERLINE_INVALID_DNA = True

# Additional Prefs
PREF_AUTOSCAF_INDEX = 0
PREF_STARTUP_TOOL_INDEX = 0
PREF_ZOOM_SPEED = 20#50
PREF_ZOOM_AFTER_HELIX_ADD = True


#Z values
#bottom
ZACTIVESLICEHANDLE = 10
ZPATHHELIXGROUP = 20
ZPATHHELIX = 30
ZPATHSELECTION = 40
ZSLICEHELIX = 50
ZDESELECTOR = 60
ZFOCUSRING = 70
ZPREXOVERHANDLE = 80
ZXOVERITEM = 90
ZBREAKPOINTHANDLE = 100
ZSKIPHANDLE = 110
ZBREAKITEM = 120
ZPATHTOOL = 130
ZSTRANDITEM = 140
ZENDPOINTITEM = 150
ZINSERTHANDLE = 160
ZPARTITEM = 200
#top

# sequence stuff
if hasattr(QFont, 'dummy'):
    SEQUENCEFONT = None
    SEQUENCEFONTH = 15
    SEQUENCEFONTCHARWIDTH = 12
    SEQUENCEFONTCHARHEIGHT = 12
    SEQUENCEFONTEXTRAWIDTH = 3
    SEQUENCETEXTXCENTERINGOFFSET = 0
else:
    SEQUENCEFONT = QFont("Monaco")
    if hasattr(QFont, 'Monospace'):
        SEQUENCEFONT.setStyleHint(QFont.Monospace)
    SEQUENCEFONT.setFixedPitch(True)
    SEQUENCEFONTH = PATH_BASE_WIDTH // 3
    SEQUENCEFONT.setPixelSize(SEQUENCEFONTH)
    SEQUENCEFONTMETRICS = QFontMetricsF(SEQUENCEFONT)
    SEQUENCEFONTCHARWIDTH = SEQUENCEFONTMETRICS.horizontalAdvance('A')
    SEQUENCEFONTCHARHEIGHT = SEQUENCEFONTMETRICS.height()
    SEQUENCEFONTEXTRAWIDTH = PATH_BASE_WIDTH - SEQUENCEFONTCHARWIDTH
    SEQUENCEFONT.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,
                                 SEQUENCEFONTEXTRAWIDTH)
    SEQUENCETEXTXCENTERINGOFFSET = SEQUENCEFONTEXTRAWIDTH / 4.
    SEQUENCETEXTYCENTERINGOFFSET = PATH_BASE_WIDTH * 0.6


if util.isMac():
    thefont = "Times"
    thefont = "Arial"
    thefontsize = 10
    XOVER_LABEL_FONT = QFont(thefont, thefontsize, QFont.Weight.Bold)
elif util.isWindows():
    thefont = "Segoe UI"
    thefont = "Calibri"
    thefont = "Arial"
    thefontsize = 9
    XOVER_LABEL_FONT = QFont(thefont, thefontsize, QFont.Weight.Bold)
else: # linux
    thefont = "DejaVu Sans"
    thefontsize = 9
    XOVER_LABEL_FONT = QFont(thefont, thefontsize, QFont.Weight.Bold)
 
SLICE_NUM_FONT = QFont(thefont, 10, QFont.Weight.Bold)
VIRTUALHELIXHANDLEITEM_FONT = QFont(thefont, 3*thefontsize, QFont.Weight.Bold)
XOVER_LABEL_COLOR = QColor(0,0,0) 

# Overwrite for Maya
# majorgridstroke = QColor(255, 255, 255)  # ffffff for maya

