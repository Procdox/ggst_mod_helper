import sys
import bpy
import addon_utils
from pathlib import Path
from typing import List

#for mod in addon_utils.modules():
#  print(mod) #.bl_infomod.bl_info.get('version', (-1, -1, -1)))

try:
  print("Starting Python Export Hook")
  # we have to insert our file into the path to include other src files
  sys.path.insert(1, Path(__file__).parent.parent.as_posix())
  import Constants
  
  # arg parsing
  argv = sys.argv
  py_args = argv[argv.index("--") + 1:]  # get all args after "--"
  assert len(py_args) == 2, "arg count is wrong"
  work_dir = Path(py_args[0])
  asset_path = py_args[1]
  asset_name = asset_path.split("/")[-1]

  # load dumped info
  info_file = work_dir.joinpath(f"{Constants.DUMP_SUBDIR}{asset_path}{Constants.INFO_SFX}")
  slot_order = [dirty.strip() for dirty in open(info_file,'r').readlines()[0].split(":")[1].split(", ")]

  target_armature = None
  for armature in bpy.data.armatures:
    if armature.name == "Armature":
      target_armature = armature
      break

  if target_armature is None:
    print("FAIL: Failed to find an armature named 'Armature'")
    exit(0)

  mesh_list:List[bpy.types.Object] = []
  for obj in bpy.data.objects:
    if obj.type == "MESH" and obj.parent is not None:
      print(obj.name, obj, obj.parent, obj.parent.data)
      if obj.parent.data == target_armature:
        mesh_list.append(obj)

  if len(mesh_list) != 1:
    print(f"FAIL: Expected to find one child mesh on Armature, found {len(mesh_list)}")
    exit(0)

  target_mesh = mesh_list[0].data
  assert isinstance(target_mesh, bpy.types.Mesh), "Mesh is not a Mesh?"
  slots_match = True
  for idx, (ref, test) in enumerate(zip(slot_order, target_mesh.materials)):
    if ref.lower() != test.name.lower():
      print(f"FAIL: Material slot {idx} is named {test.name}, not matching the target asset {ref}")
      slots_match = False

  if not slots_match:
    exit(0)

  for obj in bpy.context.selected_objects:
    obj.select_set(False)

  mesh_list[0].select_set(True)
  mesh_list[0].parent.select_set(True)
  
  addon_utils.enable("io_scene_fbx", default_set=True, persistent=False, handle_error=None)

  export_path = work_dir.joinpath(Constants.FAST_BLENDER_OUT)
  export_path.mkdir(exist_ok=True)
  export_path = export_path.joinpath(f"{asset_name}.fbx")
  bpy.ops.export_scene.fbx(filepath=export_path.as_posix(), check_existing=False, use_selection=True, bake_anim=False)

  exit(0)
except Exception as e:
  print("FAIL: unknown exception, check error.log")
  print(e)
  exit(1)