import re
from pathlib import Path
from typing import Optional, List, Dict

from . import Constants
from .Process import runProcess

CLEAN_WHITESPACE = re.compile(r'\s+')

GETPACK_MSG = "getPackageObjects UModel Failed to Parse"
EXPORT_MSG = "exportTarget UModel Failed to Parse"

class Asset:
  def __init__(self, desc:str):
    parts = CLEAN_WHITESPACE.sub(" ", desc).strip(" ").split(" ")
    self.index = int(parts[0])
    self.offset = int(parts[1],16)
    self.size = int(parts[2],16)
    self.type = parts[3]
    self.name = parts[4]
class AssetFile:
  def __init__(self, desc:str):
    lines = desc.split("\n")
    self.path = lines[0]
    self.contents = [Asset(line) for line in lines[1:] if len(line) > 1]
  def contains(self, desired_type:str):
    for child in self.contents:
      if child.type == desired_type:
        return True
    return False

class CharManifest:
  def __init__(self, char_name:str):
    self.name = char_name
    self.body_mesh = None
    self.high_mesh = None
    self.low_mesh = None
    self.weapon_meshes:List[str] = []
    self.other_meshes:List[str] = []

  def addMesh(self, mesh:str):
    mesh_file = mesh.split("/")[-1]
    if mesh_file[len(self.name):len(self.name)+7] == "_weapon":
      self.weapon_meshes.append(mesh)
    elif mesh_file[len(self.name):] == "_body.uasset":
      self.body_mesh = mesh
    elif mesh_file[len(self.name):] == "_head_high.uasset":
      self.high_mesh = mesh
    elif mesh_file[len(self.name):] == "_head_low.uasset":
      self.low_mesh = mesh
    else:
      self.other_meshes.append(mesh)

class PackageManager:
  def __init__(self, umodel:Path, pak:Path, aes:Optional[str]=None):
    self.umodel = umodel.as_posix()
    self.std_ops = ['-game=ue4.25', f'-path={pak.as_posix()}']
    if aes is not None:
      self.std_ops.append(f'-aes={aes}')

  def buildCommand(self, cmd):
    return [self.umodel, f"-{cmd}"] + self.std_ops

  def getPackageObjects(self, obj:str) -> List[AssetFile]:
    options = self.buildCommand("list")
    options.append(obj)

    result = runProcess(options, True)
    stdout = result()
    if not result or stdout is None:
      raise Exception(GETPACK_MSG)
    
    return [ AssetFile(chunk) for chunk in stdout.split("\n\n") if chunk[0:5] == "/RED/" ]

  def getCharacterMeshes(self, char:str) -> List[str]:
    asset_list = self.getPackageObjects(f'{Constants.PAK_TOP}{char}{Constants.MESH_PATH}*.uasset')
    return [asset_file.path for asset_file in asset_list if asset_file.contains("SkeletalMesh")]

  def getCharacterInfo(self) -> Dict[str, CharManifest]:
    asset_list = self.getCharacterMeshes('*')
    results:Dict[str,CharManifest] = {}
    for asset_file in asset_list:
      char_name = asset_file.split("/")[4]
      if char_name not in results:
        results[char_name] = CharManifest(char_name)
      results[char_name].addMesh(asset_file)
    return results

  def dumpTarget(self, target:str):
    forward_options = [self.umodel, "-list"] + self.std_ops
    options = forward_options + [target]

    result = runProcess(options, True)
    stdout = result()
    if not result or stdout is None:
      raise Exception(EXPORT_MSG)

  def exportTarget(self, out:Path, target:str):
    forward_options = [self.umodel, "-export", "-png" f"-out={out.as_posix()}"] + self.std_ops
    options = forward_options + [target]

    result = runProcess(options, True)
    stdout = result()
    if not result or stdout is None:
      raise Exception(EXPORT_MSG)