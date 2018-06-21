# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialogs/addseq.ui'
#
# Created: Thu Jul 21 17:35:26 2011
#      by: PyQt4 UI code generator snapshot-4.8.3-fbc8b1362812
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_AddSeqDialog(object):
    def setupUi(self, AddSeqDialog):
        AddSeqDialog.setObjectName(_fromUtf8("AddSeqDialog"))
        AddSeqDialog.resize(500, 500)
        AddSeqDialog.setModal(True)
        self.dialogGridLayout = QtGui.QGridLayout(AddSeqDialog)
        self.dialogGridLayout.setObjectName(_fromUtf8("dialogGridLayout"))
        self.tabWidget = QtGui.QTabWidget(AddSeqDialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabStandard = QtGui.QWidget()
        self.tabStandard.setObjectName(_fromUtf8("tabStandard"))
        self.standardTabGridLayout = QtGui.QGridLayout(self.tabStandard)
        self.standardTabGridLayout.setObjectName(_fromUtf8("standardTabGridLayout"))
        self.groupBox = QtGui.QGroupBox(self.tabStandard)
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.standardTabGridLayout.addWidget(self.groupBox, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.standardTabGridLayout.addItem(spacerItem, 0, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.standardTabGridLayout.addItem(spacerItem1, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabStandard, _fromUtf8(""))
        self.tabCustom = QtGui.QWidget()
        self.tabCustom.setObjectName(_fromUtf8("tabCustom"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.tabCustom)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.seqTextEdit = QtGui.QTextEdit(self.tabCustom)
        self.seqTextEdit.setObjectName(_fromUtf8("seqTextEdit"))
        self.verticalLayout_2.addWidget(self.seqTextEdit)
        self.tabWidget.addTab(self.tabCustom, _fromUtf8(""))
        self.dialogGridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.customButtonBox = QtGui.QDialogButtonBox(AddSeqDialog)
        self.customButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel)
        self.customButtonBox.setCenterButtons(True)
        self.customButtonBox.setObjectName(_fromUtf8("customButtonBox"))
        self.dialogGridLayout.addWidget(self.customButtonBox, 1, 0, 1, 1)

        self.retranslateUi(AddSeqDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.customButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AddSeqDialog.reject)
        QtCore.QObject.connect(self.customButtonBox, QtCore.SIGNAL(_fromUtf8("clicked(QAbstractButton*)")), AddSeqDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AddSeqDialog)
        AddSeqDialog.setTabOrder(self.customButtonBox, self.tabWidget)
        AddSeqDialog.setTabOrder(self.tabWidget, self.seqTextEdit)

    def retranslateUi(self, AddSeqDialog):
        AddSeqDialog.setWindowTitle(QtGui.QApplication.translate("AddSeqDialog", "Choose a sequence", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabStandard), QtGui.QApplication.translate("AddSeqDialog", "Standard", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCustom), QtGui.QApplication.translate("AddSeqDialog", "Custom", None, QtGui.QApplication.UnicodeUTF8))

