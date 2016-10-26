from PySide.QtGui import *
from PySide.QtCore import *

import parse
from main import AppResources

class Placement:
    AXIS_HEIGHT = 50
    SIGNAL_SPAN = 26
    TOP_MARGIN = 15
    SIG_MARGIN = 5

    TRANS_WIDTH = 4

    HIGH = 1
    MID = 0
    LOW = -1

    @staticmethod
    def get_sig_y(index, val):
        rel_pos = val * (Placement.SIGNAL_SPAN / 2 - Placement.SIG_MARGIN)
        return index * Placement.SIGNAL_SPAN + Placement.TOP_MARGIN + rel_pos

    @staticmethod
    def get_sigedge(index):
        return index * Placement.SIGNAL_SPAN + Placement.TOP_MARGIN - Placement.SIGNAL_SPAN / 2


class MyScene(QGraphicsScene):
    def __init__(self, window):
        super(MyScene, self).__init__()
        self.active_signals = []
        self.pixelspertick = 1
        self.activeItems = []
        self.model = None
        self.window = window
        self.topAxis = self.addRect(QRectF(0, 0, 500, Placement.AXIS_HEIGHT),
                                    Qt.NoPen,
                                    QBrush(QColor(47, 47, 46)))
        self.topAxis.setZValue(1)
        self.starttime = None
        self.endtime = None

    def time_to_pix(self, tick):
        return (tick - self.starttime) * self.pixelspertick

    def pix_to_time(self, pos):
        return pos / self.pixelspertick + self.starttime

    def view_changed(self, e):
        gv = self.window.graphicsView
        vbar = gv.verticalScrollBar()
        scene_rect = gv.mapToScene(gv.viewport().rect()).boundingRect()
        self.topAxis.setY(scene_rect.top())
        # print 'topaxis.y: ', self.topAxis.y()
        # print 'vbar.value: ', vbar.value()

        alist = self.window.active_signal_list
        vb = alist.verticalScrollBar()
        vb.setValue(vbar.value() - vbar.minimum())
        
        if self.starttime:
            left_time = self.pix_to_time(scene_rect.left())
            right_time = self.pix_to_time(scene_rect.right())
            self.update_timerange(left_time, right_time)

    def update_timerange(self, fromtime, totime):
        """
        update the text boxes that indicate
        what window of time is being viewed
        """
        self.window.fromEdit.setText(str(fromtime))
        self.window.toEdit.setText(str(totime))

    def update_scene_bounds(self):
        """
        adjust the scene bounds to match to item bounding box
        """
        # keep the scene rect as small as possible
        boundbox = self.itemsBoundingRect()
        # manually set these (it gets confused by the time axis)
        boundbox.setLeft(0)
        boundbox.setTop(-Placement.AXIS_HEIGHT)
        boundbox.setHeight(boundbox.height())
        self.setSceneRect(boundbox)

    def draw_generic_value(self, sigindex, fromx, tox, tolevel):
        pen = QPen(Qt.green)
        toy = Placement.get_sig_y(sigindex, tolevel)
        hiy = Placement.get_sig_y(sigindex, Placement.HIGH)
        loy = Placement.get_sig_y(sigindex, tolevel.LOW)
        
        # horizontal lines from fromx, to tox
        line = self.addLine(fromx + Placement.TRANS_WIDTH,
                            hiy,
                            tox - Placement.TRANS_WIDTH,
                            hiy,
                            pen)
        self.activeItems.append(line)
        line = self.addLine(fromx + Placement.TRANS_WIDTH,
                            loy,
                            tox - Placement.TRANS_WIDTH,
                            loy,
                            pen)
        self.activeItems.append(line)
        # setup everything for next value
        line = self.addLine(tox - Placement.TRANS_WIDTH,
                            hiy,
                            tox + Placement.TRANS_WIDTH,
                            toy,
                            pen)
        self.activeItems.append(line)
        line = self.addLine(tox - Placement.TRANS_WIDTH,
                            loy,
                            tox + Placement.TRANS_WIDTH,
                            toy,
                            pen)
        self.activeItems.append(line)

    def draw_single_val(self, sigindex, fromx, tox, fromlevel, tolevel):
        pen = QPen(Qt.green)
        midy = Placement.get_sig_y(sigindex, Placement.MID)
        fromy = Placement.get_sig_y(sigindex, fromlevel)
        toy = Placement.get_sig_y(sigindex, tolevel)
        line = self.addLine(fromx,
                            midy,
                            fromx + Placement.TRANS_WIDTH,
                            fromy,
                            pen)
        self.activeItems.append(line)
        line = self.addLine(fromx + Placement.TRANS_WIDTH,
                            fromy, 
                            tox - Placement.TRANS_WIDTH,
                            fromy,
                            pen)
        self.activeItems.append(line)
        line = self.addLine(tox - Placement.TRANS_WIDTH,
                            fromy,
                            tox + Placement.TRANS_WIDTH,
                            toy,
                            pen)
        self.activeItems.append(line)

    def draw_signal(self, sigindex, signal):
        lasttime = None
        single_levels = { '0': Placement.LOW, '1': Placement.HIGH }
        for change in signal.changes:
            if change.val in single_levels:
                level = single_levels[change.val]
            else:
                level = Placement.MID
            # if it's not our first iteration
            if lasttime is not None:
                fromx =  self.time_to_pix(lasttime)
                tox = self.time_to_pix(change.time)
                if lastlevel == Placement.MID:
                    self.draw_generic_value(sigindex, fromx, tox, level)
                else:
                    self.draw_single_val(sigindex, fromx, tox, lastlevel, level)    
            lasttime = change.time
            lastlevel = level

    def update_signals(self):
        """
        update the signal views from the signal models
        """
        # we're gonna start from scratch
        for item in self.activeItems:
            self.removeItem(item)

        # TODO: this needs to be cleaned up
        self.activeItems = []
        for sigindex, signal in enumerate(self.active_signals):
            if sigindex % 2 == 1:
                r = self.addRect(QRectF(0,
                                        Placement.get_sigedge(sigindex),
                                        self.time_to_pix(self.endtime),
                                        Placement.SIGNAL_SPAN),
                                 Qt.NoPen,
                                 QBrush(QColor(52, 52, 52)))
                self.activeItems.append(r)
            self.draw_signal(sigindex, signal)
            
        self.view_changed(None)
        rect = self.topAxis.rect()
        self.topAxis.setRect(0, rect.y(), self.time_to_pix(self.endtime), Placement.AXIS_HEIGHT)
        self.update_scene_bounds()
        self.view_changed(None)
        
    def wheelEvent(self, e):
        print 'wheel'
        print e.delta()
        e.accept()

    def add2activelist(self, sig):
        """ add sig to the left side list of active signals """
        newitem = QStandardItem(AppResources().icon, sig.signame)
        newitem.setDragEnabled(True)
        newitem.setData(sig)
        self.activesiglistmodel.appendRow(newitem)        

    def dropEvent(self, e):
        """
        this event occurs when a signal is dropped on the scene
        """
        sid = e.mimeData().text()
        # we already verified it's in our sigdict
        sig = self.model.sigdict[sid]
        # don't do anything if we already have this signal
        if sig in self.active_signals:
            return
        # add to active list model
        self.active_signals.append(sig)
        # add to left-side list
        self.add2activelist(sig)
        # get a list of signal changes
        sigchanges = [s for s in parse.get_signal_changes(self.model.fname, sid)]
        
        # hypothetically, signals may start and end at different times
        # in practice, I'm not sure if this ever really happens
        if self.starttime is None or sigchanges[0].time < self.starttime:
            self.starttime = sigchanges[0].time
        if self.endtime is None or sigchanges[-1].time > self.endtime:
            self.endtime = sigchanges[-1].time

        self.model.sigdict[sid].changes = sigchanges

        # update the signals view
        self.update_signals()

    def dragMoveEvent(self, e):
        """
        this event occurs when something is being dragged over us
        """
        sid = e.mimeData().text()
        if sid in self.model.sigdict:
            e.acceptProposedAction()

    def dragEnterEvent(self, e):
        self.dragMoveEvent(e)


