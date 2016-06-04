import sys
from PySide import QtUiTools
from PySide.QtGui import *
from PySide.QtCore import *
import qdarkstyle

import parse
import model
import scene


class MainApp():
    def __init__(self):
        # start the application and load the UI
        self.app = QApplication(sys.argv)
        self.window = QtUiTools.QUiLoader().load("mainwindow.ui")

        # setup widgets
        self.window.treeWidget.clear()
        self.siglistmodel = SigListModel()
        self.window.listView.setModel(self.siglistmodel)
        self.window.listView.setDragEnabled(True)
        self.scene = scene.MyScene(self.window)
        self.window.graphicsView.setScene(self.scene)
        self.window.graphicsView.setAcceptDrops(True)

        # connect signals
        self.window.actionOpen.triggered.connect(self.openfile)
        self.window.treeWidget.itemSelectionChanged.connect(self.treeselectchanged)

        hbar = self.window.graphicsView.horizontalScrollBar()
        hbar.rangeChanged.connect(self.scene.update_viewport)
        hbar.valueChanged.connect(self.scene.update_viewport)

        vbar = self.window.graphicsView.verticalScrollBar()
        vbar.rangeChanged.connect(self.scene.update_viewport)
        vbar.valueChanged.connect(self.scene.update_viewport)

        # setup look and feel
        self.res = AppResources()
        self.app.setStyleSheet(qdarkstyle.load_stylesheet())
        self.scene.setBackgroundBrush(QBrush(self.res.bgcolor))

        self.window.show()

    def treeselectchanged(self):
        self.loadsigs(self.window.treeWidget.selectedItems()[0].scope)

    def openfile(self):
        fname, _ = QFileDialog.getOpenFileName(self.window,
                                               'Open file',
                                               "",
                                               "Waveform Files (*.vcd)")
        if fname:
            head = parse.get_header(fname)

            vpmodel = model.ViewPortModel(fname, head.rootscope.getsigdict(), head)
            self.scene.model = vpmodel

            self.window.treeWidget.clear()
            root = self.loadScopes(head.rootscope, self.window.treeWidget)
            self.window.treeWidget.expandAll()
            self.window.treeWidget.setCurrentItem(root, 0)
            self.loadsigs(head.rootscope)

    def loadsigs(self, scope):
        self.siglistmodel.clear()
        for sig in scope.childsigs:
            newitem = QStandardItem(self.res.icon, sig.signame)
            newitem.setDragEnabled(True)
            newitem.setData(sig)
            self.siglistmodel.appendRow(newitem)

    def loadScopes(self, scope, currparent):
        newItem = QTreeWidgetItem(currparent)
        newItem.setText(0, scope.name)
        newItem.setIcon(0, self.res.blockIcon)
        newItem.scope = scope
        for childscope in scope.childscopes:
            self.loadScopes(childscope, newItem)
        return newItem


class SigListModel(QStandardItemModel):
    def __init__(self):
        super(SigListModel, self).__init__()

    def mimeData(self, indices):
        data = QMimeData()
        siginfo = self.itemFromIndex(indices[0]).data()
        data.setText(siginfo.sid)
        return data


class AppResources():
    def __init__(self):
        self.blockIcon = QPixmap("block.png")
        self.icon = QPixmap("signal.png")
        self.bgcolor = QColor(32, 31, 31)
        self.textColor = Qt.lightGray

if __name__ == '__main__':
    app = MainApp()
    sys.exit(app.app.exec_())
