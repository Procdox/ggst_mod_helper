from PySide6 import QtWidgets
from pathlib import Path
from typing import List, Union

from .Widgets import PathWidget, TextWidget, showWarning
from .Process import runProcess, ReturnCode
from . import Constants

GGST_EXE="GGST.exe"
UMODEL_EXE="umodel.exe"
NOESIS_EXE="Noesis.exe"
UE4EXP_EXE="Ue4Export.exe"
BLENDER_EXE="blender.exe"
UNREAL_EXE="UE4Editor-Cmd.exe"
UNVERUM_EXE="Unverum.exe"
UE_PACK_EXE="UnrealPak.exe"

DEFAULT_GGST_PATH="C:/Program Files (x86)/Steam/steamapps/common/GUILTY GEAR STRIVE/" + GGST_EXE
DEFAULT_BLENDER_PATH="C:/Program Files/Blender Foundation/Blender 3.4/" + BLENDER_EXE

def rm_tree(pth:Path):
  for child in pth.glob('*'):
    if child.is_file():
      child.unlink()
    else:
      rm_tree(child)
  pth.rmdir()

def validateGGST(value:Path) -> ReturnCode[str]:
  pak_path = value.parent.joinpath(Constants.PAK_LOC)
  if not pak_path.exists():
    return ReturnCode(False, "Failed to find GGST Pak")
  return ReturnCode(True)

def validateBlender(value:Path) -> ReturnCode[str]:
  blender_result = runProcess([value.as_posix(), "--version"])
  blender_stdout = blender_result()
  if not blender_result or blender_stdout is None or len(blender_stdout) == None:
    return ReturnCode(False, "Failed to validate chosen Blender install")
  first_line = blender_stdout.split("\n")[0]
  raw_version = first_line.split(" ")[1]
  full_version = [int(x) for x in raw_version.split(".")]
  major_version = full_version[0]
  if major_version < 3:
    return ReturnCode(False, f"Expected at least version 3.0.0, Found Version: {raw_version}")
  return ReturnCode(True)

def validateUnreal(value:Path) -> ReturnCode[str]:
  return ReturnCode(True)

def validateAES(value:str) -> ReturnCode[str]:
  return ReturnCode(value[0:2] == "0x", "AES must start with '0x'")

field_list = List[Union[PathWidget,TextWidget]]

class ConfigWidget(QtWidgets.QWidget):
  def __init__(self):
    super().__init__()
    self.ggst_field = PathWidget("GGST_Install", GGST_EXE, DEFAULT_GGST_PATH, validateGGST)
    self.umodel_field = PathWidget("UModel_Install", UMODEL_EXE)
    self.noesis_field = PathWidget("Noesis_Install", NOESIS_EXE)
    self.ue4exp_field = PathWidget("UE4Export_Install", UE4EXP_EXE)
    self.blender_field = PathWidget("Blender_Install", BLENDER_EXE, DEFAULT_BLENDER_PATH, validateBlender)
    self.unreal_field = PathWidget("Unreal_Install", UNREAL_EXE, validator=validateUnreal)
    self.packer_field = PathWidget("UE_Pack_Install", UE_PACK_EXE)
    self.unverum_field = PathWidget("Unverum_Install", UNVERUM_EXE)
    self.work_field = PathWidget("Working_Dir", is_dir=True)

    self.aes_field = TextWidget("AES_Key", validator=validateAES)

    self.all_fields:field_list = [
      self.ggst_field, self.umodel_field, self.noesis_field, self.ue4exp_field, 
      self.blender_field, self.unreal_field, self.packer_field, self.unverum_field,
      self.work_field, self.aes_field
    ]

    layout = QtWidgets.QVBoxLayout(self)
    for field in self.all_fields:
      layout.addWidget(field)

    self.mods_are_stashed = False
    self.wants_mods_stashed = None
  
  def validate(self) -> bool:
    safe = True
    for field in self.all_fields:
      safe = field.updateValue().success and safe
    return safe

  # Direct accesors
  def ggst(self) -> Path:
    return self.ggst_field.value
  def umodel(self) -> Path:
    return self.umodel_field.value
  def noesis(self) -> Path:
    return self.noesis_field.value
  def ue4exp(self) -> Path:
    return self.ue4exp_field.value
  def blender(self) -> Path:
    return self.blender_field.value
  def unreal(self) -> Path:
    return self.unreal_field.value
  def packer(self) -> Path:
    return self.packer_field.value
  def unverum(self) -> Path:
    return self.unverum_field.value
  def work(self) -> Path:
    return self.work_field.value
  def aes(self) -> str:
    return self.aes_field.value

  # Faked accessors, these are derived from Constants or multiple fields
  def pak(self) -> Path:
    return self.ggst().parent.joinpath(Constants.PAK_LOC)
  def fastBlenderRoot(self) -> Path:
    return self.work().joinpath(Constants.FAST_BLENDER_OUT)
  def fastUnrealRoot(self) -> Path:
    return self.work().joinpath(Constants.FAST_UE_OUT)
  def fastUnrealUproj(self) -> Path:
    return self.work().joinpath(Constants.FAST_UE_OUT, f"{Constants.FAST_UE_OUT}.uproject")
  def fastUnrealContent(self) -> Path:
    return self.work().joinpath(Constants.FAST_UE_OUT, "Content")
  def fastUnrealCooked(self) -> Path:
    return self.work().joinpath(Constants.FAST_UE_OUT, "Saved/Cooked/WindowsNoEditor/Unreal_Fast_Build/Content")
  
  def stashMods(self):
    game_mods = self.pak().joinpath("~mods")
    stashed_mods = self.work().joinpath(Constants.MOD_STASH)

    if not game_mods.exists() or not any(game_mods.iterdir()): return

    if self.wants_mods_stashed is None:
      self.wants_mods_stashed = showWarning("Found mods", f"Would you like to move mods and explore the raw game files?\nMods will be moved to <work dir>/{Constants.MOD_STASH} and automatically moved back after.", True)
    
    if game_mods.exists() and self.wants_mods_stashed and not self.mods_are_stashed:
      if not stashed_mods.exists(): stashed_mods.mkdir(parents=True)
      self.mods_are_stashed = True
      for mod_folder in stashed_mods.iterdir():
        rm_tree(mod_folder)
      for mod_folder in game_mods.iterdir():
        mod_folder.rename(stashed_mods.joinpath(mod_folder.name))

  def restoreMods(self):
    if not self.mods_are_stashed: return
    
    self.mods_are_stashed = False
    game_mods = self.pak().joinpath("~mods")
    stashed_mods = self.work().joinpath(Constants.MOD_STASH)
    for mod_folder in stashed_mods.iterdir():
      mod_folder.rename(game_mods.joinpath(mod_folder.name))
  
  def loadSettings(self, settings):
    for field in self.all_fields:
      field.loadSettings(settings)

  def saveSettings(self, settings):
    for field in self.all_fields:
      field.saveSettings(settings)


