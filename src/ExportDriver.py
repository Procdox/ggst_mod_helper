from PySide6 import QtCore
from .ConfigView import ConfigWidget
from pathlib import Path
from .Widgets import PathWidget, TextWidget
from .UModelDriver import PackageManager
from .Constants import UNREAL_HOOK, BLENDER_HOOK
from .Process import runProcess

UASSET_SFX=".uasset"

def rm_tree(pth:Path):
  for child in pth.glob('*'):
    if child.is_file():
      #child.unlink()
      print(child)
    else:
      rm_tree(child)
  #pth.rmdir()
  print(pth)

def moveReplace(src:Path,dest:Path):
  dest = dest.joinpath(src.name)
  dest.unlink(True)
  src.rename(dest)

def breakAssetPath(src: str):
  delim_idx = src.rfind("/")
  return src[:delim_idx], src[delim_idx+1:]

def cleanAsset(value:str):
  if value[-len(UASSET_SFX):] == UASSET_SFX:
    value = value[:-len(UASSET_SFX)]
  if (path_index := value.find("Chara/")) > -1:
    value = value[path_index:]
  else:
    return None
  return value

class FastExportSignals(QtCore.QObject):
  error = QtCore.Signal(str)
  progress = QtCore.Signal(int, str)
  finished = QtCore.Signal(Path)


class FastExportSession(QtCore.QRunnable):
  def exportBlender(self, target_project:Path) -> Path:
    fbx_src = self.config.fastBlenderRoot().joinpath(f"{self.asset_name}.fbx")
    if fbx_src.exists(): fbx_src.unlink() # delete pre-existing
    
    options = [ 
      self.config.blender().as_posix(), 
      "--background", "--factory-startup", 
      target_project.as_posix(), 
      "--python", BLENDER_HOOK, "--", 
      self.config.work().as_posix(), 
      self.asset_path
    ]

    blender_result = runProcess(options, True)
    blender_stdout = blender_result()
    if not blender_result or blender_stdout is None:
      raise Exception(f"Blender FBX Export Failed. An unexpected error occured while trying to run Blender, check the error log for details.")
    
    fails = [line[6:] for line in blender_stdout.split("\n") if line[:6] == "FAIL: "]
    if len(fails) > 0:
      fails = '\n'.join(fails)
      raise Exception(f"Blender FBX Export Failed. Blender project failed validation, please address the following issues before continuing:\n{fails}")
    
    if not fbx_src.exists():
      raise Exception(f"Blender FBX Export Failed. Blender appeared to run correctly, but the exported FBX was not found")
    
    return fbx_src

  def importUnreal(self, fbx_src:Path):
    ue_content = self.config.fastUnrealContent()
    ue_chara = ue_content.joinpath("Chara")
    if ue_chara.exists(): rm_tree(ue_chara)
    ue_precooked = ue_content.joinpath(self.asset_stub)
    ue_precooked.mkdir(parents=True,exist_ok=True)

    options = ' '.join([ 
      self.config.unreal().as_posix(), 
      self.config.fastUnrealUproj().as_posix(), 
      "-stdout", 
      f'-ExecutePythonScript="{UNREAL_HOOK} {fbx_src.as_posix()} {self.asset_stub}"' 
    ])
    unreal_result = runProcess(options, True)
    unreal_stdout = unreal_result()
    if not unreal_result or unreal_stdout is None:
      raise Exception(f"Unreal Import Failed. An unexpected error occured while trying to run Unreal, check the error log for details.")
    
    if unreal_stdout.find("Successfully exported") < 0:
      raise Exception(f"Unreal Import Failed. Unreal did not appear to correctly import the fbx.")

    if not ue_precooked.joinpath(f"{self.asset_name}.uasset").exists():
      raise Exception(f"Unreal Import Failed. Unreal appeared to run correctly, but the imported uasset was not found")

  def cookUnreal(self):
    ue_cooked = self.config.fastUnrealCooked()
    uasset_src = ue_cooked.joinpath(self.asset_stub, f"{self.asset_name}.uasset")
    uexp_src = ue_cooked.joinpath(self.asset_stub, f"{self.asset_name}.uexp")
    if uasset_src.exists(): uasset_src.unlink()
    if uexp_src.exists(): uexp_src.unlink()

    options = [ 
      self.config.unreal().as_posix(), 
      self.config.fastUnrealUproj().as_posix(), 
      "-run=cook", "-targetplatform=WindowsNoEditor" 
    ]

    cook_result = runProcess(options)
    if not cook_result:
      raise Exception(f"Unreal Cook Failed. An unexpected error occured while trying to run Unreal, check the error log for details.")

    if not uasset_src.exists() or not uexp_src.exists():
      raise Exception("Unreal Cook Failed. Unreal appeared to cook correctly, but the cooked uasset was not found")

    return uasset_src, uexp_src

  def pak(self, uasset_src:Path, uexp_src:Path, mod_name:str):
    mod_dir = self.config.pak().joinpath(mod_name)
    pak_src = self.config.pak().joinpath(f"{mod_name}.pak")
    if Path(pak_src).exists(): Path(pak_src).unlink()

    build_home = mod_dir.joinpath("RED/Content").joinpath(self.asset_stub)
    build_home.mkdir(parents=True, exist_ok=True)
    moveReplace(uasset_src, build_home)
    moveReplace(uexp_src, build_home)
    
    with open(self.config.packer().parent.joinpath('filelist.txt'),'w') as filelist:
      filelist.write( '"' + mod_dir.as_posix() + r'\*.*" "..\..\..\*.*"' )

    options = [ self.config.packer().as_posix(), pak_src, "-create=filelist.txt", "-compress"]
    pak_result = runProcess(options)
    if not pak_result:
      raise Exception(f"Unreal PAK Failed. An unexpected error occured while trying to run Unreal PAK, check the error log for details.")

    if not Path(pak_src).exists():
      raise Exception(f"Unreal PAK Failed. Unreal PAK appeared to run correctly, but the pak was not found")
    return pak_src

  def __init__(self, config:ConfigWidget, blender_target:PathWidget, asset_target:TextWidget, mod_name:TextWidget):
    super().__init__()
    # ----- Config and Target Validation -----
    if not config.validate():
      raise Exception("Bad Config. Please verify your install paths and aes key.")
    if not blender_target.updateValue():
      raise Exception("Bad Target. Please verify your target blender project.")
    if not asset_target.updateValue():
      raise Exception("Bad Target. Please verify your target asset.")
    asset_path = cleanAsset(asset_target.value)
    if asset_path is None:
      raise Exception("Bad Target. Something is wrong with your target asset. How the hell did you get here!?")
    if not mod_name.updateValue():
      raise Exception("Bad Target. Please verify your target mod name.")
    
    self.config = config
    self.output = None
    self.asset_path = asset_path
    self.asset_stub, self.asset_name = breakAssetPath(self.asset_path)
    self.blender_target = blender_target.value
    self.mod_name = mod_name.value
    self.signals = FastExportSignals()

  def run(self):
    try:
      self.signals.progress.emit(0, "Validating Asset Info")
      manager = PackageManager(self.config.umodel(), self.config.pak(), self.config.aes())
      manager.ensureAssetInfo(self.config.work(), self.asset_path)
    except:
      self.signals.error.emit("Bad Target. Failed to dump info for the target asset, it may not exist.")
      return

    
    
    try:
      self.signals.progress.emit(1, "Exporting Blender Project to FBX")
      fbx_src = self.exportBlender(self.blender_target)
      self.signals.progress.emit(2, "Importing FBX into Unreal Engine")
      self.importUnreal(fbx_src)
      self.signals.progress.emit(3, "Cooking Unreal project")
      uasset_src, uexp_src = self.cookUnreal()
      self.signals.progress.emit(4, "Packing mod")
      self.output = self.pak(uasset_src, uexp_src, self.mod_name)
      self.signals.progress.emit(5, "Finished")
    except Exception as error:
      self.signals.error.emit(str(error))
      return

    self.signals.finished.emit(self.output)




    
    


    
