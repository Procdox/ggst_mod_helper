from PySide6 import QtCore, QtWidgets, QtGui
from typing import Optional, Callable, Union
from pathlib import Path
import subprocess

ERROR_LOG = Path(".").joinpath("error.log")
ERROR_DELIM = "\n--------------------------------------------------\n"

def cleanSTD(dirty:Union[str,bytes]):
  if isinstance(dirty,bytes):
    dirty = dirty.decode()
  return dirty.replace("\r\n","\n")

def dumpError(error: Exception):
  print(error)
  with open(ERROR_LOG,'a') as error_log:
    error_log.write( f"{ERROR_DELIM}Error:\n{str(error)}" )

def dumpProcessOut(message:str, info:subprocess.CompletedProcess):
  with open(ERROR_LOG,'a') as error_log:
    error_log.write( f"{ERROR_DELIM}{message}\n----- STDOUT: -----\n" )
    error_log.write( cleanSTD(info.stdout) )
    error_log.write( "\n----- STDERR: -----\n" )
    error_log.write( cleanSTD(info.stderr) )

def dumpString(message:str):
  with open(ERROR_LOG,'a') as error_log:
    error_log.write( f"{ERROR_DELIM}{message}\n" )




"""
def safeProcess(msg, options:Union[List[str],str], returnOut:bool = True, cwd:Optional[str]=None, shell=False) -> str:
  info = subprocess.run(options, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, shell=shell)
  if info.returncode != 0: 
    logmsg = f"{msg}:\n'{' '.join(options)}'"
    dumpProcessOut(logmsg, info)
    raise Exception
  if returnOut:
    return cleanSTD(info.stdout)
  else:
    return ""
"""

def showWarning(title:str, msg:str, ask:bool) -> bool:
  warning = QtWidgets.QMessageBox()
  warning.setWindowTitle(title)
  warning.setText(msg)

  roles = QtWidgets.QMessageBox.StandardButton
  buttons = (roles.Yes | roles.No) if ask else (roles.Ok)
  warning.setStandardButtons(buttons)
  rcode = warning.exec()

  return (rcode == roles.Yes) if ask else True

class PathWidget(QtWidgets.QWidget):
  def __init__(self, settings_name:str, file_filter:Optional[str]=None, settings_default:str="", validator:Optional[Callable[[Path],bool]]=None, is_dir:bool=False):
    super().__init__()

    self.settings_name = settings_name
    self.display_name = self.settings_name.replace("_"," ")
    self.file_filter = file_filter
    self.settings_default = settings_default
    self.validator = validator
    self.is_dir = is_dir

    self.label = QtWidgets.QLabel()
    self.label.setText(self.display_name)
    self.text_field = QtWidgets.QLineEdit()
    self.text_field.setReadOnly(True)
    self.browse_button = QtWidgets.QPushButton("Browse")
    self.browse_button.clicked.connect(self.browse)

    layout = QtWidgets.QHBoxLayout(self)
    layout.addWidget(self.label)
    layout.addWidget(self.text_field)
    layout.addWidget(self.browse_button)

    self.value = Path()
  
  def loadSettings(self, settings:QtCore.QSettings):
    saved_value = settings.value(self.settings_name)
    if not isinstance(saved_value, str):
      saved_value = self.settings_default
    self.text_field.setText(saved_value)
    self.updateValue()

  def saveSettings(self, settings:QtCore.QSettings):
    settings.setValue(self.settings_name, self.text_field.text())

  def _validate(self) -> bool: 
    if len(self.text_field.text()) == 0:
      return False
    if not self.value.exists():
      return False
    if self.validator is not None and not self.validator(self.value):
      return False

    return True

  def updateValue(self) -> bool:
    raw_text = self.text_field.text()
    self.value = Path(raw_text)

    if self._validate():
      palette = QtGui.QPalette()
      self.text_field.setPalette(palette)
      return True
    else:
      palette = self.text_field.palette()
      palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor('red'))
      self.text_field.setPalette(palette)
      return False

  @QtCore.Slot()
  def browse(self):
    browse_path = str(self.value.parent) if self.value.parent.exists() else QtCore.QDir.currentPath()
    title = f"Select {self.display_name}"

    if self.is_dir:
      selected_path = QtWidgets.QFileDialog.getExistingDirectory(self, title, browse_path)
    elif self.file_filter is not None:
      selected_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, browse_path, self.file_filter)
    else:
      selected_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, browse_path)
    
    if len(selected_path) > 0:
      self.text_field.setText(selected_path)
      self.updateValue()

class TextWidget(QtWidgets.QWidget):
  def __init__(self, settings_name:str, settings_default:str="", validator:Optional[Callable[[str],bool]]=None):
    super().__init__()

    self.settings_name = settings_name
    self.display_name = self.settings_name.replace("_"," ")
    self.settings_default = settings_default
    self.validator = validator

    self.label = QtWidgets.QLabel()
    self.label.setText(self.display_name)
    self.text_field = QtWidgets.QLineEdit()
    self.text_field.editingFinished.connect(self.updateValue)

    layout = QtWidgets.QHBoxLayout(self)
    layout.addWidget(self.label)
    layout.addWidget(self.text_field)

    self.value = ""
  
  def loadSettings(self, settings:QtCore.QSettings):
    saved_value = settings.value(self.settings_name)
    if not isinstance(saved_value, str):
      saved_value = self.settings_default
    self.text_field.setText(saved_value)
    self.updateValue()

  def saveSettings(self, settings:QtCore.QSettings):
    settings.setValue(self.settings_name, self.text_field.text())

  def _validate(self) -> bool: 
    if len(self.value) == 0:
      return False
    if self.validator is not None and not self.validator(self.value):
      return False

    return True

  @QtCore.Slot()
  def updateValue(self) -> bool:
    self.value = self.text_field.text()
    if self._validate():
      palette = QtGui.QPalette()
      self.text_field.setPalette(palette)
      return True
    else:
      palette = self.text_field.palette()
      palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor('red'))
      self.text_field.setPalette(palette)
      return False

class CheckBox(QtWidgets.QCheckBox):
  def __init__(self, settings_name:str, settings_default:bool = False):
    self.settings_name = settings_name
    self.settings_default = settings_default
    self.display_name = self.settings_name.replace("_"," ")
    super().__init__(self.display_name)

  def loadSettings(self, settings:QtCore.QSettings):
    saved_value = settings.value(self.settings_name)
    if not isinstance(saved_value, str):
      saved_value = self.settings_default
    else:
      saved_value = (saved_value == "true")
    self.setChecked(saved_value)

  def saveSettings(self, settings:QtCore.QSettings):
    settings.setValue(self.settings_name, self.isChecked())