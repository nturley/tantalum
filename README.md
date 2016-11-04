# Tantalum Waveform Viewer

Tantalum will be an HDL simulation waveform viewer, similar to gtkWave.

I'm going to try using Qt and python using the pyside bindings.

![screenshot](/screenshot.png)

## Status

Just started. It can sort of display simple vcd waveforms

## Build Instructions

 * install python and pip
 * install pyside (for linux: http://pyside.readthedocs.io/en/latest/building/linux.html)
 * pip install qdarkstyle

## Dev Details

We are using QGraphicsScene to view the waveforms. In terms of scene coordinates, The top waveform's top-left corner is always at (0, 0). The axis components are scene components but the left axis will track to the left side of the viewport and the top axis will track to the top of the viewport.

```
scene coordinate = (time - start) * scalefactor
time = scene coordinate / scalefactor + start
```
