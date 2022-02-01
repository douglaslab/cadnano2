#!/usr/bin/env python
# encoding: utf-8

"""
CustomQGraphicsView.py
.. module:: CustomQGraphicsView
   :platform: Unix, Windows, Mac OS X
   :synopsis: A Custom QGraphicsView module to allow focus input events
   like mouse clicks and panning and zooming

.. moduleauthor::  Nick Conway on 2011-01-17.
Copyright (c) 2010 . All rights reserved.

"""
from cadnano2.cadnano import app
from cadnano2.views import styles

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['Qt', 'QTimer', 'pyqtSignal', 'QTimeLine'])
util.qtWrapImport('QtGui', globals(),  ['QGuiApplication', 'QPaintEngine'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsView',
                                           'QGraphicsScene'])

# for OpenGL mode
try:
    # from OpenGL import GL
    from PyQt6.QtWidgets import QOpenGLWidget
except ImportError:
    GL = False

GL = False


class CustomQGraphicsView(QGraphicsView):
    """
    Base class for QGraphicsViews with Mouse Zoom and Pan support via the
    Control/Command shortcut key.

    A QGraphics View stores info on the view and handles mouse events for
    zooming and panning

    Ctrl-MidMouseButton = Pan
    Ctrl-RightMouseButton = Dolly Zoom
    MouseWheel = Zoom

    Parameters
    ----------
    parent: type of QWidget, such as QWidget.splitter() for the type of
    View its has

    See Also
    --------

    Examples
    --------

    For details on these and other miscellaneous methods, see below.
    """
    def __init__(self, parent=None):
        """
        On initialization, we need to bind the Ctrl/command key to
        enable manipulation of the view.
        """
        QGraphicsView.__init__(self, parent)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self.setStyleSheet("QGraphicsView { background-color: rgb(96.5%, 96.5%, 96.5%); }")
        self._noDrag = QGraphicsView.DragMode.RubberBandDrag
        self._yesDrag = QGraphicsView.DragMode.ScrollHandDrag

        # reset things that are state dependent
        self.clearGraphicsView()
        self.setAcceptDrops(True)

        self._x0 = 0
        self._y0 = 0
        self._scale_size = 1.0
        self._scale_limit_max = 3.0
        self._scale_limit_min = 0.41
        self._scaleUpRate = 0.01
        self._scaleDownRate = 0.01
        self._scaleFitFactor = 1  # sets initial zoom level
        self._showDetails = True
        self._last_scale_factor = 0.0
        self.sceneRootItem = None  # the item to transform
        # Keyboard panning
        self._key_pan_delta_x = styles.PATH_BASE_WIDTH * 21
        self._key_pan_delta_y = styles.PATH_HELIX_HEIGHT + styles.PATH_HELIX_PADDING/2
        # Modifier keys and buttons
        self._key_mod = Qt.Key.Key_Control
        self._button_pan = Qt.MouseButton.LeftButton
        self._button_pan_alt = Qt.MouseButton.MiddleButton
        self._button_zoom = Qt.MouseButton.RightButton

        self.toolbar = None  # custom hack for the paint tool palette
        self._name = None

        if GL:
            self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
            self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        else:
            self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
            # self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
    # end def

    levelOfDetailChangedSignal = pyqtSignal(bool)

    def __repr__(self):
        clsName = self.__class__.__name__
        objId = self._name if self._name else str(id(self))[-4:]
        return "<%s %s>" % (clsName, objId)

    def setName(self, name):
        self._name = name
    # end def

    def setViewportUpdateOn(self, isEnabled):
        if isEnabled:
            self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        else:
            self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.NoViewportUpdate)
    # end def

    def activateSelection(self, isActive):
        if self._selectionLock:
            self._selectionLock.clearSelection(False)
        self.clearSelectionLockAndCallbacks()
        if isActive:
            self._noDrag = QGraphicsView.DragMode.RubberBandDrag
        else:
            self._noDrag = QGraphicsView.DragMode.NoDrag
        if self.dragMode() != self._yesDrag:
            self.setDragMode(self._noDrag)
    # end def

    def clearGraphicsView(self):
        # Event handling
        self._hasFocus = False
        # Misc
        self.clearSelectionLockAndCallbacks()
        # Pan and dolly defaults
        self._transformEnable = False
        self._dollyZoomEnable = False
        self.setDragMode(self._noDrag)
    # end def

    def clearSelectionLockAndCallbacks(self):
        self._selectionLock = None # a selection group to limit types of items selected
        self._pressList = [] # bookkeeping to handle passing mouseReleaseEvents to QGraphicsItems that don't get them
    # end def

    def setGLView(self, boolval):
        scene = self.scene()
        if boolval and self.isGL == False:
            self.isGL = True
            # scene.drawBackground = self.drawBackgroundGL
            # self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
            # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        elif not boolval and self.isGL == True:
            self.isGL = False
            # scene.drawBackground = self.drawBackgroundNonGL
            # self.setViewport(QWidget())
            # self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
    # end def

    def setupGL(self):
        scene = self.scene()
        win = self.sceneRootItem.window()
        self.isGL = True
        self.isGLSwitchAllowed = True
        self.qTimer = QTimer()
        # self.drawBackgroundNonGL = scene.drawBackground
        # scene.drawBackground = self.drawBackgroundGL
        # format = QGLFormat(QGL.SampleBuffers)
        # format.setSamples(16)
        # print "# of samples", format.samples(), format.sampleBuffers()
        # self.setViewport(QGLWidget(format))
        # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    # end def

    def resetGL(self):
        scaleFactor = self.transform().m11()
        # print "scaleFactor", scaleFactor
        self.sceneRootItem.window().statusBar().showMessage("%f" % scaleFactor)

        if scaleFactor < .15:# and self.isGLSwitchAllowed:
            # self.isGLSwitchAllowed = False
            self.setGLView(True)
            self._showDetails = False
            self.levelOfDetailChangedSignal.emit(False) # zoomed out
            self.qTimer.singleShot(500, self.allowGLSwitch)
        elif scaleFactor > .2:# and self.isGLSwitchAllowed:
            # self.isGLSwitchAllowed = False
            self.setGLView(False)
            self._showDetails = True
            self.levelOfDetailChangedSignal.emit(True) # zoomed in
            self.qTimer.singleShot(500, self.allowGLSwitch)
    # end def

    def shouldShowDetails(self):
        return self._showDetails
    # end def

    def allowGLSwitch(self):
        self.isGLSwitchAllowed = True
    # end def

    def drawBackgroundGL(self, painter, rect):
        """
        This method is for overloading the QGraphicsScene.
        """
        if painter.paintEngine().type() != QPaintEngine.OpenGL and \
            painter.paintEngine().type() != QPaintEngine.OpenGL2:

            qWarning("OpenGLScene: drawBackground needs a QGLWidget to be set as viewport on the graphics view");
            return
        # end if
        painter.beginNativePainting()
        GL.glDisable(GL.GL_DEPTH_TEST) # disable for 2D drawing
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        painter.endNativePainting()
    # end def

    def focusInEvent(self, event):
        self._hasFocus = True

    def focusOutEvent(self, event):
        self._transformEnable = False
        self._dollyZoomEnable = False
        self._hasFocus = False
        self._transformEnable = False
    # end def

    def setSelectionLock(self, selectionLock):
        self._selectionLock = selectionLock
    # end def

    def selectionLock(self):
        return self._selectionLock
    # end def

    def setScaleFitFactor(self, value):
        """docstring for setScaleFitFactor"""
        self._scaleFitFactor = value
    # end def

    def setKeyPan(self, button):
        """Set the class pan button remotely"""
        self._button_pan = button
    # end def

    def addToPressList(self, item):
        """docstring for addToPressList"""
        # self._pressList[self._pressListIdx].append(item)
        self._pressList.append(item)
    # end def

    def keyPanDeltaX(self):
        """Returns the distance in scene space to move the sceneRootItem when
        panning left or right."""
        # PyQt isn't aware that QGraphicsObject isa QGraphicsItem and so
        # it returns a separate python object if, say, childItems() returns
        # a QGraphicsObject casted to a QGraphicsItem. If this is the case,
        # we can still find the QGraphicsObject thusly:
        candidateDxDeciders = list(self.sceneRootItem.childItems())
        candidateDxDeciders = candidateDxDeciders +\
                           [cd.toGraphicsObject() for cd in candidateDxDeciders]
        for cd in candidateDxDeciders:
            if cd == None:
                continue
            keyPanDXMethod = getattr(cd, 'keyPanDeltaX', None)
            if keyPanDXMethod != None:
                return keyPanDXMethod()
        return 100

    def keyPanDeltaY(self):
        """Returns the distance in scene space to move the sceneRootItem when
        panning left or right."""
        candidateDyDeciders = list(self.sceneRootItem.childItems())
        candidateDyDeciders = candidateDyDeciders +\
                           [cd.toGraphicsObject() for cd in candidateDyDeciders]
        for cd in candidateDyDeciders:
            if cd == None:
                continue
            keyPanDYMethod = getattr(cd, 'keyPanDeltaY', None)
            if keyPanDYMethod != None:
                return keyPanDYMethod()
        return 100

    def keyPressEvent(self, event):
        """
        Handle key presses for mouse-drag transforms and arrow-key panning.
        """
        if not self._hasFocus:  # we don't have focus -> ignore keypress
            return
        if event.key() == self._key_mod:
            self._transformEnable = True
            QGraphicsView.keyPressEvent(self, event)
        elif event.key() == Qt.Key.Key_Left:
            transform = self.sceneRootItem.transform()
            transform.translate(self.keyPanDeltaX(), 0)
            self.sceneRootItem.setTransform(transform)
        elif event.key() == Qt.Key.Key_Up:
            transform = self.sceneRootItem.transform()
            transform.translate(0, self.keyPanDeltaY())
            self.sceneRootItem.setTransform(transform)
        elif event.key() == Qt.Key.Key_Right:
            transform = self.sceneRootItem.transform()
            transform.translate(-self.keyPanDeltaX(), 0)
            self.sceneRootItem.setTransform(transform)
        elif event.key() == Qt.Key.Key_Down:
            transform = self.sceneRootItem.transform()
            transform.translate(0, -self.keyPanDeltaY())
            self.sceneRootItem.setTransform(transform)
        elif event.key() == Qt.Key.Key_Plus:
            self.zoomIn(0.3)
        elif event.key() == Qt.Key.Key_Minus:
            self.zoomIn(0.03)
        else:
            return QGraphicsView.keyPressEvent(self, event)
        # end else
    # end def

    def keyReleaseEvent(self, event):
        """docstring for keyReleaseEvent"""
        if event.key() == self._key_mod:
            self._transformEnable = False
            self._dollyZoomEnable = False
            self._panDisable()
        # end if
        else:
            QGraphicsView.keyReleaseEvent(self, event)
        # end else
    # end def

    def enterEvent(self, event):
        self.setFocus()
        self.setDragMode(self._noDrag)
        QGraphicsView.enterEvent(self, event)

    def leaveEvent(self, event):
        self.clearFocus()
        QGraphicsView.leaveEvent(self, event)

    def mouseMoveEvent(self, event):
        """
        Must reimplement mouseMoveEvent of QGraphicsView to allow
        ScrollHandDrag due to the fact that events are intercepted
        breaks this feature.
        """
        if self._transformEnable == True:
            if self.dragMode() == self._yesDrag:
                # Add stuff to handle the pan event
                xf = event.pos().x()
                yf = event.pos().y()
                factor = self.transform().m11()
                transform = self.sceneRootItem.transform()

                transform.translate((xf - self._x0)/factor,
                                    (yf - self._y0)/factor)
                self.sceneRootItem.setTransform(transform)
                self._x0 = xf
                self._y0 = yf
            elif self._dollyZoomEnable == True:
                self.dollyZoom(event)
        # adding this allows events to be passed to items underneath
        QGraphicsView.mouseMoveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """docstring for mousePressEvent"""
        if self._transformEnable == True and QGuiApplication.keyboardModifiers():
            which_buttons = event.buttons()
            if which_buttons in [self._button_pan, self._button_pan_alt]:
                self._panEnable()
                self._x0 = event.pos().x()
                self._y0 = event.pos().y()
            elif which_buttons == self._button_zoom:
                self._dollyZoomEnable = True
                self._last_scale_factor = 0
                # QMouseEvent.y() returns the position of the mouse cursor
                # relative to the widget
                self._y0 = event.posF().y()
            else:
                QGraphicsView.mousePressEvent(self, event)
        else:
            QGraphicsView.mousePressEvent(self, event)
    #end def

    def mouseReleaseEvent(self, event):
        """If panning, stop. If handles were pressed, release them."""
        if self._transformEnable == True:
            # QMouseEvent.button() returns the button that triggered the event
            which_button = event.button()
            if which_button in [self._button_pan, self._button_pan_alt]:
                self._panDisable()
            elif which_button == self._button_zoom:
                self._dollyZoomEnable = False
            else:
                return QGraphicsView.mouseReleaseEvent(self, event)
        # end if
        else:
            if len(self._pressList):  # Notify any pressed items to release
                # event_pos = event.position()
                for item in self._pressList:
                    #try:
                    # print "item release", item
                    item.customMouseRelease(event)
                    #except:
                    #    item.mouseReleaseEvent(event)
                #end for
                self._pressList = []
            # end if
            if self._selectionLock:
                self._selectionLock.processPendingToAddList()
            return QGraphicsView.mouseReleaseEvent(self, event)

    #end def

    def _panEnable(self):
        """Enable ScrollHandDrag Mode in QGraphicsView (displays a hand
        pointer)"""
        self.setDragMode(self._yesDrag)
    # end def

    def _panDisable(self):
        """Disable ScrollHandDrag Mode in QGraphicsView (displays a hand
        pointer)"""
        self.setDragMode(self._noDrag)
    # end def

    def fname(self):
        """docstring for fname"""
        pass

    def wheelEvent(self, event):
        self.safeScale(event.angleDelta().y())
    # end def

    def safeScale(self, delta):
        currentScaleLevel = self.transform().m11()
        scaleFactor = 1 + delta * \
           (self._scaleDownRate if delta < 0 else self._scaleUpRate) * \
           (app().prefs.zoomSpeed/100.)
        newScaleLevel = currentScaleLevel * scaleFactor
        newScaleLevel = util.clamp(currentScaleLevel * scaleFactor,\
                              self._scale_limit_min,\
                              self._scale_limit_max)
        scaleChange = newScaleLevel / currentScaleLevel
        self.scale(scaleChange, scaleChange)

        self.resetGL()
    # end def

    def zoomIn(self, fractionOfMax=0.5):
        currentScaleLevel = self.transform().m11()
        scaleChange = (fractionOfMax * self._scale_limit_max) / currentScaleLevel
        self.scale(scaleChange, scaleChange)
    # end def

    def zoomOut(self, fractionOfMin=1):
        currentScaleLevel = self.transform().m11()
        scaleChange = (fractionOfMin * self._scale_limit_min) / currentScaleLevel
        self.scale(scaleChange, scaleChange)
    # end def

    def dollyZoom(self, event):
        """docstring for dollyZoom"""
        # QMouseEvent.y() returns the position of the mouse cursor relative
        # to the widget
        yf = event.y()
        denom = abs(yf - self._y0)
        if denom > 0:
            scale_factor = (self.height() / 2) % denom
            if self._last_scale_factor != scale_factor:
                self._last_scale_factor = scale_factor
                # zoom in if mouse y position is getting bigger
                if yf - self._y0 > 0:
                    self.safeScale(yf - self._y0)
                # end else
                else:  # else id smaller zoom out
                    self.safeScale(yf - self._y0)
                # end else
        # end if
    # end def

    def resetScale(self):
        """
        reset the scale to 1
        """
        # use the transform value if you want to get how much the view
        # has been scaled
        self._scale_size = self.transform().m11()

        # self._scale_limit_min = 0.41*self._scale_size
        # make it so fitting in view is zoomed minimum
        # still gives you one zoom level out before violates limit
        self._scale_limit_min = self._scale_size*self._scaleFitFactor

        # use this if you want to reset the zoom in limit
        # self._scale_limit_max = 3.0*self._scale_size

        self._last_scale_factor = 0.0
    # end def

    def zoomToFit(self):
        # Auto zoom to center the scene
        thescene = self.sceneRootItem.scene()
        # order matters?
        self.sceneRootItem.resetTransform() # zero out translations
        self.resetTransform() # zero out scaling
        if self.toolbar:  # HACK: move toolbar so it doesn't affect sceneRect
            self.toolbar.setPos(0, 0)
        thescene.setSceneRect(thescene.itemsBoundingRect())
        scene_rect = thescene.sceneRect()
        if self.toolbar:  # HACK, pt2: move toolbar back
            self.toolbar.setPos(self.mapToScene(0, 0))
        self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio) # fit in view
        self.resetScale() # adjust scaling so that translation works
        # adjust scaling so that the items don't fill 100% of the view
        # this is good for selection
        self.scale(self._scaleFitFactor, self._scaleFitFactor)
        self._scale_size *= self._scaleFitFactor

        self.resetGL()
    # end def

    def paintEvent(self, event):
        if self.toolbar:
            self.toolbar.setPos(self.mapToScene(0, 0))
        QGraphicsView.paintEvent(self, event)

    def dragEnterEvent(self, event):
        event.ignore()
#end class
