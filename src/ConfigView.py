from PySide6 import QtWidgets
from pathlib import Path

from .Widgets import PathWidget, TextWidget, showWarning
from .Process import runProcess
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

def validateGGST(value:Path) -> bool:
  pak_path = value.parent.joinpath(Constants.PAK_LOC)
  if not pak_path.exists():
    showWarning("Missing Content", "Failed to find GGST Pak, please verify your GGST path", False)
    return False
  return True

def validateBlender(value:Path) -> bool:
  blender_result = runProcess([value.as_posix(), "--version"])
  blender_stdout = blender_result()
  if not blender_result or blender_stdout is None or len(blender_stdout) == None:
    showWarning("Blender problem", f"Failed to validate chosen Blender install", False)
    return False
  version = blender_stdout.split("\n")[0]
  if version != Constants.BLENDER_VERSION:
    showWarning("Blender problem", f"Expected version: {Constants.BLENDER_VERSION}, Found Version: {version}", False)
    return False
  return True

def validateUnreal(value:Path) -> bool:
  return True

def validateAES(value:str) -> bool:
  return value[0:2] == "0x"

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

    layout = QtWidgets.QVBoxLayout(self)
    layout.addWidget(self.ggst_field)
    layout.addWidget(self.umodel_field)
    layout.addWidget(self.noesis_field)
    layout.addWidget(self.ue4exp_field)
    layout.addWidget(self.blender_field)
    layout.addWidget(self.unreal_field)
    layout.addWidget(self.packer_field)
    layout.addWidget(self.unverum_field)
    layout.addWidget(self.work_field)
    layout.addWidget(self.aes_field)
  
  def validate(self) -> bool:
    safe = True
    safe = self.ggst_field.updateValue() and safe
    safe = self.umodel_field.updateValue() and safe
    safe = self.noesis_field.updateValue() and safe
    safe = self.ue4exp_field.updateValue() and safe
    safe = self.blender_field.updateValue() and safe
    safe = self.unreal_field.updateValue() and safe
    safe = self.packer_field.updateValue() and safe
    safe = self.unverum_field.updateValue() and safe
    safe = self.work_field.updateValue() and safe
    safe = self.aes_field.updateValue() and safe
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
  
  def loadSettings(self, settings):
    self.ggst_field.loadSettings(settings)
    self.umodel_field.loadSettings(settings)
    self.noesis_field.loadSettings(settings)
    self.ue4exp_field.loadSettings(settings)
    self.blender_field.loadSettings(settings)
    self.unreal_field.loadSettings(settings)
    self.packer_field.loadSettings(settings)
    self.unverum_field.loadSettings(settings)
    self.work_field.loadSettings(settings)
    self.aes_field.loadSettings(settings)

  def saveSettings(self, settings):
    self.ggst_field.saveSettings(settings)
    self.umodel_field.saveSettings(settings)
    self.noesis_field.saveSettings(settings)
    self.ue4exp_field.saveSettings(settings)
    self.blender_field.saveSettings(settings)
    self.unreal_field.saveSettings(settings)
    self.packer_field.saveSettings(settings)
    self.unverum_field.saveSettings(settings)
    self.work_field.saveSettings(settings)
    #self.aes_field.saveSettings(settings)


