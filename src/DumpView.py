from PySide6 import QtCore, QtWidgets
from typing import List, Dict
from pathlib import Path

from . import Constants
from .Widgets import showWarning, CheckBox
from .ConfigView import ConfigWidget
from .UModelDriver import PackageManager, CharManifest
from .Process import runProcess

CheckState = QtCore.Qt.CheckState
ItemFlag = QtCore.Qt.ItemFlag

EXPORT_MSG = "Failed to export with Noesis"

def invertCheckState(old: CheckState) -> CheckState:
  assert old != CheckState.PartiallyChecked
  return CheckState.Unchecked if old == CheckState.Checked else CheckState.Checked

def makeTableItem(label:str, checkable:bool=False) -> QtWidgets.QTableWidgetItem:
  item = QtWidgets.QTableWidgetItem(label)
  if checkable:
    item.setFlags(item.flags() | ItemFlag.ItemIsUserCheckable | ItemFlag.ItemIsEnabled)
    item.setCheckState(QtCore.Qt.CheckState.Unchecked)
  else:
    item.setFlags(item.flags() ^ ItemFlag.ItemIsUserCheckable)
  item.setFlags(item.flags() ^ ItemFlag.ItemIsEditable)
  return item

class ExportTarget:
  def __init__(self, name:str, file:str):
    self.name, self.file = name, file

class CharList(QtWidgets.QTableWidget):
  def __init__(self):
    super().__init__()
    self.itemPressed.connect(self.handleSelect)

  @QtCore.Slot()
  def handleSelect(self, item:QtWidgets.QTableWidgetItem):
    if bool(item.flags() & ItemFlag.ItemIsUserCheckable):
      #this is a hell of a fucking line
      item.setCheckState( invertCheckState(item.checkState()) )

class DumpWidget(QtWidgets.QWidget):
  def makeCheckBox(self, label:str, layout:QtWidgets.QVBoxLayout):
    widget = CheckBox(label)
    widget.toggled.connect(self.updateCounts)
    layout.addWidget(widget)
    return widget

  def __init__(self, config:ConfigWidget):
    super().__init__()

    self.config = config
    self.char_info: Dict[str, CharManifest] = {}

    top_layout = QtWidgets.QVBoxLayout(self)
    
    scan_game = QtWidgets.QPushButton("Scan Game Files")
    scan_game.clicked.connect(self.scanChars)
    top_layout.addWidget(scan_game)

    select_widget = QtWidgets.QWidget()
    select_layout = QtWidgets.QHBoxLayout(select_widget)

    # ---- Left Side, Character filtering table -----
    self.character_list = CharList()
    self.character_list.itemChanged.connect(self.updateCounts)
    select_layout.addWidget(self.character_list)

    # ---- Right Side, Mesh filtering options -----
    mesh_widget = QtWidgets.QWidget()
    mesh_layout = QtWidgets.QVBoxLayout(mesh_widget)

    all_chars = QtWidgets.QPushButton("All Characters")
    all_chars.clicked.connect(self.selectAllChars)
    mesh_layout.addWidget(all_chars)

    self.body_mesh = self.makeCheckBox("Body_Meshes", mesh_layout)
    self.high_mesh = self.makeCheckBox("Head_High_Meshes", mesh_layout)
    self.lower_mesh = self.makeCheckBox("Head_Lower_Meshes", mesh_layout)
    self.weapon_mesh = self.makeCheckBox("Weapon_Meshes", mesh_layout)
    self.other_mesh = self.makeCheckBox("Other_Meshes", mesh_layout)

    self.counts = QtWidgets.QLabel("Exporting: 0")
    mesh_layout.addWidget(self.counts)

    self.export = QtWidgets.QPushButton("Export")
    self.export.clicked.connect(self.doExport)
    self.export.setEnabled(False)
    mesh_layout.addWidget(self.export)

    # ----- Connect Up Layouts -----
    select_layout.addWidget(mesh_widget)
    top_layout.addWidget(select_widget)

  @QtCore.Slot()
  def selectAllChars(self):
    for row in range(0,self.character_list.rowCount()):
      button = self.character_list.item(row,0)
      button.setCheckState(QtCore.Qt.CheckState.Checked)

  def checkMods(self, work_path:Path, pak_path:Path):
    actual_mod_path = pak_path.joinpath("~mods")
    safe_mod_path = work_path.joinpath("moved_mod")
    safe_mod_path.mkdir(exist_ok=True)

    if actual_mod_path.exists() and any(actual_mod_path.iterdir()):
      do_mod_move = showWarning("Found mods", f"Would you like to move mods and explore the raw game files?\nMods will be moved to {safe_mod_path}", True)
      if do_mod_move:
        for mod_entry in actual_mod_path.iterdir():
          target = safe_mod_path.joinpath(mod_entry.name)
          print(f"Move Mod: {mod_entry} -> {target}")
          #mod_entry.rename(target)

  @QtCore.Slot()
  def scanChars(self):
    self.character_list.clear()
    self.export.setEnabled(False)
    self.targets:List[ExportTarget] = []
    self.counts.setText("Exporting: 0")

    if not self.config.validate():
      showWarning("Bad Config", "Please verify your paths and aes key first", False)
      return

    ggst_path = self.config.ggst()
    umodel_path = self.config.umodel()
    work_path = self.config.work()
    aes_key = self.config.aes()

    pak_path = ggst_path.parent.joinpath(Constants.PAK_LOC)
    self.checkMods(work_path,pak_path)
    
    manager = PackageManager(umodel_path, pak_path, aes_key)
    try:
      self.char_info = manager.getCharacterInfo()
    except:
      showWarning("Scan Issue", "An issue occured while scanning, check error.log for details.", False)
      return
    
    self.character_list.setRowCount(len(self.char_info))
    self.character_list.setColumnCount(3)
    self.character_list.setHorizontalHeaderLabels(["Character", "Weapon Meshes", "Misc Meshes"])
    self.character_list.verticalHeader().hide()
    for row, char in enumerate(self.char_info.values()):
      name = makeTableItem(char.name, True)
      self.character_list.setItem(row, 0, name)

      wep = makeTableItem( str(len(char.weapon_meshes)) )
      self.character_list.setItem(row, 1, wep)

      misc = makeTableItem( str(len(char.other_meshes)) )
      self.character_list.setItem(row, 2, misc)

    self.export.setEnabled(True)
    self.updateCounts()

  def calculateTargets(self):
    self.targets:List[ExportTarget] = []

    body = self.body_mesh.isChecked()
    high = self.high_mesh.isChecked()
    lower = self.lower_mesh.isChecked()
    weps = self.weapon_mesh.isChecked()
    other = self.other_mesh.isChecked()

    for row in range(0,self.character_list.rowCount()):
      button = self.character_list.item(row,0)
      if button.checkState() != CheckState.Checked: continue

      char_name = button.text()
      info = self.char_info[char_name]
      if body and info.body_mesh is not None: self.targets.append( ExportTarget(char_name, info.body_mesh) )
      if high and info.high_mesh is not None: self.targets.append( ExportTarget(char_name, info.high_mesh) )
      if lower and info.low_mesh is not None: self.targets.append( ExportTarget(char_name, info.low_mesh) )
      if weps: 
        self.targets += [ ExportTarget(char_name, file) for file in info.weapon_meshes ]
      if other: 
        self.targets += [ ExportTarget(char_name, file) for file in info.other_meshes ]

  @QtCore.Slot()
  def updateCounts(self):
    if not self.export.isEnabled(): return

    self.calculateTargets()
    self.counts.setText(f"Exporting: {len(self.targets)}")


  @QtCore.Slot()
  def doExport(self):
    if not self.config.validate():
      showWarning("Bad Config", "Please verify your paths and aes key first", False)
      return

    if len(self.targets) == 0:
      showWarning("Nothing to Export", "You haven't selected any meshes to export", False)
      return

    ggst_path = self.config.ggst()
    umodel_path = self.config.umodel()
    noesis_path = self.config.noesis()
    work_path = self.config.work()
    aes_key = self.config.aes()

    pak_path = self.config.pak()
    self.checkMods(work_path,pak_path)

    dump_dir = work_path.joinpath("dump")

    manager = PackageManager(umodel_path, pak_path, aes_key)

    for target in self.targets:
      manager.exportTarget(dump_dir, target.file)
      stub_name = dump_dir.joinpath("/".join(target.file.split("/")[3:])).as_posix()[:-7]
      psk_path = stub_name + ".psk"
      fbx_path = stub_name + ".fbx"

      options = [noesis_path.as_posix(), "?cmode", psk_path, fbx_path, "-fbxnewexport", "-rotate 90 0 0"]
      result = runProcess(options)
      if not result:
        stop = showWarning("Export Issue", "An issue occured while exporting, check error.log for details.\nContinue Exporting?", True)
        if not stop:
          break
        

  def loadSettings(self, settings):
    self.body_mesh.loadSettings(settings)
    self.high_mesh.loadSettings(settings)
    self.lower_mesh.loadSettings(settings)
    self.weapon_mesh.loadSettings(settings)
    self.other_mesh.loadSettings(settings)

  def saveSettings(self, settings):
    self.body_mesh.saveSettings(settings)
    self.high_mesh.saveSettings(settings)
    self.lower_mesh.saveSettings(settings)
    self.weapon_mesh.saveSettings(settings)
    self.other_mesh.saveSettings(settings)
