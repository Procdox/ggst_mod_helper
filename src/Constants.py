from pathlib import Path
import sys

WINDOW_TITLE="GGST Mod Helper"

PAK_LOC = "RED/Content/Paks"
PAK_TOP = "/RED/Content/Chara/"
MESH_PATH = "/Costume01/Mesh/"

DUMP_SUBDIR = "dump/"
INFO_SFX="_details.txt"

FAST_BLENDER_OUT="Blender_Fast_Build"
FAST_UE_OUT="Unreal_Fast_Build"

BLENDER_VERSION="Blender 3.4.0"
UNREAL_VERSION=""

if getattr(sys, 'frozen', False):
  BLENDER_HOOK=Path(sys._MEIPASS).joinpath("hooks/BlenderHook.py").as_posix()
  UNREAL_HOOK=Path(sys._MEIPASS).joinpath("hooks/UnrealHook.py").as_posix()
  UNREAL_TEMPLATE=Path(sys._MEIPASS).joinpath("hooks/uproject.txt")
elif __file__:
  BLENDER_HOOK=Path(__file__).parent.joinpath("hooks/BlenderHook.py").as_posix()
  UNREAL_HOOK=Path(__file__).parent.joinpath("hooks/UnrealHook.py").as_posix()
  UNREAL_TEMPLATE=Path(__file__).parent.joinpath("uproject.txt")