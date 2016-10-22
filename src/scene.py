from PySide.QtGui import *
from PySide.QtCore import *

import parse
from main import AppResources


class MyScene(QGraphicsScene):
    def __init__(self, window):
        super(MyScene, self).__init__()
        self.active_signals = []
        self.pixelspertick = 1
        self.activeItems = []
        self.model = None
        self.window = window
        self.topAxis = self.addRect(QRectF(0, 0, 200, 50), Qt.NoPen, QBrush(QColor(47, 47, 46)))
        self.topAxis.setZValue(1)
        self.starttime = None

    def update_viewport(self, e):
        # adjust the scene rect
        gv = self.window.graphicsView
        hbar = self.window.graphicsView.horizontalScrollBar()
        vbar = self.window.graphicsView.verticalScrollBar()

        scene_rect = gv.mapToScene(gv.viewport().rect()).boundingRect()
        self.topAxis.setY(scene_rect.top())
        # weird bug workaround
        if vbar.value() == 0:
            self.topAxis.setY(-50)
        if self.starttime:    
        	self.update_timerange(scene_rect.left()/self.pixelspertick + self.starttime, scene_rect.right()/self.pixelspertick + self.starttime)

    def update_timerange(self, fromtime, totime):
        self.window.fromEdit.setText(str(fromtime))
        self.window.toEdit.setText(str(totime))

    def update_rect(self):
        # keep the scene rect as small as possible
        boundbox = self.itemsBoundingRect()
        # manually set these (it gets confused by the axes)
        boundbox.setLeft(0)
        boundbox.setTop(-50)
        boundbox.setHeight(boundbox.height()+50)
        self.setSceneRect(boundbox)

    def refresh_items(self):
        for item in self.activeItems:
            self.removeItem(item)
        maxtime = 0
        self.activeItems = []
        for sigindex, signal in enumerate(self.active_signals):
            currtime = None
            currval = None
            lasty = None
            y = None
            for change in signal.changes:
                if currtime is not None:
                    if currval == 'x':
                        pen = QPen(Qt.red)
                        y = sigindex * 26 + 14
                    if currval == '0':
                        pen = QPen(Qt.green)
                        y = sigindex * 26 + 10 + 14
                    if currval == '1':
                        pen = QPen(Qt.green)
                        y = sigindex * 26 - 10 + 14
                    fromx = (currtime - self.starttime) * self.pixelspertick
                    tox = (change.time - self.starttime) * self.pixelspertick
                    if change.time > maxtime:
                    	maxtime = change.time
                    line = self.addLine(fromx,
                                        y,
                                        tox,
                                        y,
                                        pen)
                    self.activeItems.append(line)
                    if lasty is not None:
                        line = self.addLine(fromx,
                    	                    lasty,
                    	                    fromx,
                    	                    y,
                    	                    pen)
                        self.activeItems.append(line)

                currtime = change.time
                currval = change.val
                lasty = y
        self.update_viewport(None)
        self.update_rect()
        rect = self.topAxis.rect()
        self.topAxis.setRect(rect.x(), rect.y(), (maxtime-self.starttime) * self.pixelspertick + 50, 50)
        self.update_viewport(None)
        
    def wheelEvent(self, e):
        print 'wheel'
        print e.delta()
        e.accept()

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        sid = e.mimeData().text()
        sig = self.model.sigdict[sid]
        if sig in self.active_signals:
            return
        self.active_signals.append(sig)

        
        newitem = QStandardItem(AppResources().icon, sig.signame)
        newitem.setDragEnabled(True)
        newitem.setData(sig)
        self.activesiglistmodel.appendRow(newitem)
        
        sigchanges = [s for s in parse.get_signal_changes(self.model.fname, sid)]
        # hypothetically, signals may start at different times
        if self.starttime is None or sigchanges[0].time < self.starttime:
            self.starttime = sigchanges[0].time
        self.model.sigdict[sid].changes = sigchanges
        self.refresh_items()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()
