from PySide.QtGui import *
from PySide.QtCore import *

import parse


class MyScene(QGraphicsScene):
    def __init__(self, window):
        super(MyScene, self).__init__()
        self.active_signals = []
        self.pixelspertick = 1
        self.activeItems = []
        self.model = None
        self.window = window
        self.leftAxis = self.addRect(QRectF(0, 0, 50, 200), Qt.NoPen, QBrush(QColor(47, 47, 46)))
        self.leftAxis.setZValue(1)
        self.topAxis = self.addRect(QRectF(0, 0, 200, 50), Qt.NoPen, QBrush(QColor(47, 47, 46)))
        self.topAxis.setZValue(1)
        self.starttime = None

    def update_viewport(self, e):
        # adjust the scene rect
        gv = self.window.graphicsView
        hbar = self.window.graphicsView.horizontalScrollBar()
        vbar = self.window.graphicsView.verticalScrollBar()

        scene_rect = gv.mapToScene(gv.viewport().rect()).boundingRect()
        self.leftAxis.setX(scene_rect.left())
        self.topAxis.setY(scene_rect.top())
        # weird bug workaround
        if hbar.value() == 0:
            self.leftAxis.setX(-50)
        if vbar.value() == 0:
            self.topAxis.setY(-50)

        self.update_timerange(scene_rect.left() + 50, scene_rect.right() + 50)

    def update_timerange(self, fromtime, totime):
        self.window.fromEdit.setText(str(fromtime))
        self.window.toEdit.setText(str(totime))

    def update_rect(self):
        # keep the scene rect as small as possible
        boundbox = self.itemsBoundingRect()
        # manually set these (it gets confused by the axes)
        boundbox.setLeft(-50)
        boundbox.setTop(-50)
        self.setSceneRect(boundbox)

    def refresh_items(self):
        for item in self.activeItems:
            self.removeItem(item)
        self.activeItems = []
        for sigindex, signal in enumerate(self.active_signals):
            currtime = None
            currval = None
            for change in signal.changes:
                if currtime is not None:
                    if currval == 'x':
                        pen = QPen(Qt.red)
                        y = sigindex * 50 + 10
                    if currval == '0':
                        pen = QPen(Qt.green)
                        y = sigindex * 50 + 20 + 10
                    if currval == '1':
                        pen = QPen(Qt.green)
                        y = sigindex * 50 - 20 + 10
                    fromx = (currtime - self.starttime) * self.pixelspertick
                    tox = (change.time - self.starttime) * self.pixelspertick
                    line = self.addLine(fromx,
                                        y,
                                        tox,
                                        y,
                                        pen)
                    self.activeItems.append(line)
                currtime = change.time
                currval = change.val
        self.update_viewport(None)
        self.update_rect()
        rect = self.leftAxis.rect()
        self.leftAxis.setRect(rect.x(), rect.y(), 50, 50 * len(self.active_signals) + 30)

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
        sigchanges = [s for s in parse.get_signal_changes(self.model.fname, sid)]
        # hypothetically, signals may start at different times
        if self.starttime is None or sigchanges[0].time < self.starttime:
            self.starttime = sigchanges[0].time
        self.model.sigdict[sid].changes = sigchanges
        self.refresh_items()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()
