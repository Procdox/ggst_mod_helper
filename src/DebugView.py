from PySide6 import QtCore, QtWidgets

from .ConfigView import ConfigWidget
from .UModelDriver import PackageManager, CharManifest
from .Widgets import showWarning

class DebugWidget(QtWidgets.QWidget):
  def __init__(self, config:ConfigWidget):
    super().__init__()

    self.config = config

    dump_slots = QtWidgets.QPushButton("Dump Mesh Slots")
    dump_slots.clicked.connect(self.dump_slots)

    layout = QtWidgets.QVBoxLayout(self)
    layout.addWidget(dump_slots)

  @QtCore.Slot()
  def dump_slots(self):
    if not self.config.validate():
      showWarning("Bad Config", "Please verify your paths and aes key first", False)
      return

    manager = PackageManager(self.config.umodel(), self.config.pak(), self.config.aes())
    self.char_info = manager.getCharacterInfo()

    slot_names = set()

    targets = []
    for info in self.char_info.values():
      if info.body_mesh is not None: targets.append( info.body_mesh )
      if info.high_mesh is not None: targets.append( info.high_mesh )
      if info.low_mesh is not None: targets.append( info.low_mesh )
      targets += info.weapon_meshes
      targets += info.other_meshes

    for mesh in targets:
      full_asset_name = "/RED/Content/" + mesh
      manager.dumpTarget(full_asset_name)

    for slot in slot_names:
      print(slot)

  def loadSettings(self, settings):
    pass
  def saveSettings(self, settings):
    pass