from PySide6 import QtCore, QtWidgets, QtGui
from typing import Optional, Callable
from pathlib import Path

from .Process import ReturnCode

def showWarning(title:str, msg:str, ask:bool) -> bool:
  warning = QtWidgets.QMessageBox()
  warning.setWindowTitle(title)
  warning.setText(msg)

  roles = QtWidgets.QMessageBox.StandardButton
  buttons = (roles.Yes | roles.No) if ask else (roles.Ok)
  warning.setStandardButtons(buttons)
  rcode = warning.exec()

  return (rcode == roles.Yes) if ask else True

PathValFunc=Callable[[Path],ReturnCode[str]]
StrValFunc=Callable[[str],ReturnCode[str]]

class PathWidget(QtWidgets.QWidget):
  def __init__(self, settings_name:str, file_filter:Optional[str]=None, settings_default:str="", validator:Optional[PathValFunc]=None, is_dir:bool=False):
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

  def _validate(self, warn:bool=True) -> ReturnCode[str]: 
    if len(self.text_field.text()) == 0:
      return ReturnCode(False, "Invalid empty path")
    if not self.value.exists():
      return ReturnCode(False, "Path does not exist")
    if self.validator is not None:
      return self.validator(self.value)

    return ReturnCode(True)

  def updateValue(self) -> ReturnCode[str]:
    raw_text = self.text_field.text()
    self.value = Path(raw_text)

    rcode = self._validate()
    if rcode:
      palette = QtGui.QPalette()
      self.text_field.setPalette(palette)
      self.text_field.setToolTip("")
    else:
      palette = self.text_field.palette()
      palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor('yellow'))
      self.text_field.setPalette(palette)
      self.text_field.setToolTip(rcode.value or "")
    return rcode

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
  def __init__(self, settings_name:str, settings_default:str="", validator:Optional[StrValFunc]=None):
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

  def _validate(self) -> ReturnCode[str]: 
    if len(self.value) == 0:
      return ReturnCode(False, "Invalid empty path")
    if self.validator is not None:
      return self.validator(self.value)

    return ReturnCode(True)

  @QtCore.Slot()
  def updateValue(self) -> ReturnCode[str]:
    self.value = self.text_field.text()

    rcode = self._validate()
    if rcode:
      palette = QtGui.QPalette()
      self.text_field.setPalette(palette)
      self.text_field.setToolTip("")
    else:
      palette = self.text_field.palette()
      palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor('red'))
      self.text_field.setPalette(palette)
      self.text_field.setToolTip(rcode.value or "")
    return rcode

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