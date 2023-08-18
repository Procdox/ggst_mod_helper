from __future__ import annotations
from PySide6 import QtCore, QtWidgets, QtGui
import sys, signal, atexit, subprocess, re
from pathlib import Path
from typing import Optional, Callable, List, Union, Tuple, NamedTuple, Dict, Set

from src.ConfigView import ConfigWidget
from src.DumpView import DumpWidget
from src.BlenderView import BlenderWidget

from src.Constants import WINDOW_TITLE

import logging
logging.basicConfig(filename='error.log', level=logging.DEBUG)

def getSettings():
  return QtCore.QSettings("Procdox", "ggst_mod_helper")

class Dummy(QtWidgets.QWidget):
  def __init__(self):
    super().__init__()
  def loadSettings(self, settings):
    pass
  def saveSettings(self, settings):
    pass

class MainWindow(QtWidgets.QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle(WINDOW_TITLE)

    config = ConfigWidget()
    self.tabs = [
      ("Config", config),
      ("Dump From Game", DumpWidget(config)),
      ("Fast Package Blender", BlenderWidget(config)),
    ]

    top = QtWidgets.QTabWidget()
    for title, widget in self.tabs:
      top.addTab(widget,title)
    self.setCentralWidget(top)

  def loadSettings(self, settings):
    print(settings.fileName())
    for _, widget in self.tabs:
      widget.loadSettings(settings)

  def saveSettings(self, settings):
    for _, widget in self.tabs:
      widget.saveSettings(settings)


class HelperApplication:
  def __init__(self):
    # QT core components
    self.app = QtWidgets.QApplication(sys.argv)
    self.win = MainWindow()

    self.win.loadSettings(getSettings())

    signal.signal(signal.SIGINT, self.stopGui)
    signal.signal(signal.SIGTERM, self.stopGui)
    atexit.register(self.stopGui)

  def run(self):
    self.win.show()
    try:
      rcode = self.app.exec()
      self.stopGui()
      return rcode
    except Exception as error:
      return 0

  def stopGui(self, *args, **kwargs):
    self.win.saveSettings(getSettings())
    self.app.quit()

if __name__ == "__main__":
  capp = HelperApplication()
  sys.exit(capp.run())