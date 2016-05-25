# Tantalum Waveform Viewer

The goal for Tantalum is to provide a visually attractive interface for viewing HDL simulation waveforms.

I think modelsim uses Tk. GtkWave obviously uses gtk. I'm going to try Qt.

I'll be using python, at least for glue logic, using pyside qt bindings. At least initially, I might leverage some gtkwave components to parse the files, but I might reimplement it myself at some point.

![screenshot](/screenshot.png)

## Status

Just started. It can barely display simple VCD files
