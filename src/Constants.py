from pathlib import Path

WINDOW_TITLE="GGST Mod Helper"

PAK_LOC = "RED/Content/Paks"
PAK_TOP = "/RED/Content/Chara/"
MESH_PATH = "/Costume01/Mesh/"

DUMP_SUBDIR = "dump/"
INFO_SFX="_details.txt"

FAST_BLENDER_OUT="Blender_Fast_Build"
FAST_UE_OUT="Unreal_Fast_Build"

BLENDER_VERSION="Blender 3.0.0"
BLENDER_HOOK=Path(__file__).parent.joinpath("hooks/BlenderHook.py").as_posix()

UNREAL_VERSION=""
UNREAL_HOOK=Path(__file__).parent.joinpath("hooks/UnrealHook.py").as_posix()