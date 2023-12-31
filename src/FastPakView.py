from PySide6 import QtCore, QtWidgets
from pathlib import Path

from .ConfigView import ConfigWidget
from .Widgets import showWarning, PathWidget, TextWidget
from .ExportDriver import FastExportSession, cleanAsset
from .Process import ReturnCode

BAD_SYMBOLS=["..", "*", "?", ",", "'", "\""]
BAD_SYMBOLS_STR = ' '.join(BAD_SYMBOLS)

def validateAsset(value:str) -> ReturnCode[str]:
  if cleanAsset(value) is None:
    return ReturnCode(False, "Target Asset must be relative to Pak Content e.g. Chara/RAM/Costume01/Mesh/ram_body\n/RED/Content/ prefix and the file suffix are optional")
  if value.find("\\") > 1:
    showWarning("Invalid Target Asset", "Target Asset contains a '\\' or '\\\\', please use posix styled '/' paths instead ", False)
    return ReturnCode(False, "Target Asset contains a '\\' or '\\\\', please use posix styled '/' paths instead ")
  for symbol in BAD_SYMBOLS:
    if value.find(symbol) > -1:
      ReturnCode(False, f"Target Asset contains a '{symbol}', it and the following characters are prohibited:\n {BAD_SYMBOLS_STR}")
  return ReturnCode(True)

class FastPakWidget(QtWidgets.QWidget):
  def __init__(self, config:ConfigWidget):
    super().__init__()

    self.config = config
    
    self.target_field = PathWidget("Target_File", "*.blend")
    self.char_field = TextWidget("Target_Asset", validator=validateAsset)
    self.mod_field = TextWidget("Target_Mod")
    self.export_FBX = QtWidgets.QPushButton("One-Click Convert: Blender to PAK")
    self.export_FBX.clicked.connect(self.export)
    self.progress = QtWidgets.QProgressBar()
    self.progress.setMaximum(5)
    self.progress.setValue(0)
    self.state = QtWidgets.QLabel()

    layout = QtWidgets.QVBoxLayout(self)
    layout.addWidget(self.target_field)
    layout.addWidget(self.char_field)
    layout.addWidget(self.mod_field)
    layout.addWidget(self.export_FBX)
    layout.addWidget(self.progress)
    layout.addWidget(self.state)

    self.setWorking(False)
  
  def loadSettings(self, settings):
    self.target_field.loadSettings(settings)
    self.char_field.loadSettings(settings)
    self.mod_field.loadSettings(settings)
  def saveSettings(self, settings):
    self.target_field.saveSettings(settings)
    self.char_field.saveSettings(settings)
    self.mod_field.saveSettings(settings)

  def setWorking(self, working:bool):
    if working:
      self.config.stashMods()
    else:
      self.config.restoreMods()
    self.config.setEnabled(not working)
    self.export_FBX.setEnabled(not working)
    self.export_FBX.setVisible(not working)
    self.progress.setVisible(working)
    self.state.setVisible(working)

  @QtCore.Slot()
  def export(self):
    # ----- Config Validation
      session = FastExportSession(self.config, self.target_field, self.char_field, self.mod_field)
      self.setWorking(True)
      session.signals.error.connect(self.handleExportError)
      session.signals.progress.connect(self.handleExportProgress)
      session.signals.finished.connect(self.handleExportFinished)
      QtCore.QThreadPool.globalInstance().start(session)
      
  @QtCore.Slot()
  def handleExportError(self, msg:str):
    showWarning("Export Failed", msg, False)
    self.setWorking(False)

  @QtCore.Slot()
  def handleExportProgress(self, step:int, msg:str):
    self.progress.setValue(step)
    self.state.setText(msg)

  @QtCore.Slot()
  def handleExportFinished(self, result:Path):
    showWarning("Success", f"Successfully exported to: {result}", False)
    self.setWorking(False)