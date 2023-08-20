import bpy, bmesh, sys, addon_utils
from pathlib import Path
from typing import List, Set

# These need to match Constants, but packaging makes that annoying
DUMP_SUBDIR="dump/"
FAST_BLENDER_OUT="Blender_Fast_Build"
INFO_SFX="_details.txt"

def getMesh() -> bpy.types.Object:
  all_aramatures:List[bpy.types.Object] = []
  for obj in bpy.data.objects:
    if obj.type == "ARMATURE":
      all_aramatures.append(obj)

  if len(all_aramatures) == 0:
    print("FAIL: Target project contains 0 armatures")
    exit(0)

  target_armature = None
  
  if len(all_aramatures) > 1:
    for armature in all_aramatures:
      if armature.name == "Armature":
        target_armature = armature
        break

    if target_armature is None:
      print("FAIL: Multiple armatures, can't disambiguate based on name 'Armature'")
      exit(0)
  else:
    target_armature = all_aramatures[0]
    target_armature.name = "Armature"


  mesh_list:List[bpy.types.Object] = []
  for obj in bpy.data.objects:
    if obj.type == "MESH" and obj.parent is not None:
      if obj.parent == target_armature:
        mesh_list.append(obj)

  if len(mesh_list) != 1:
    print(f"FAIL: Expected to find one child mesh on Armature, found {len(mesh_list)}")
    exit(0)
  
  return mesh_list[0]

def matchesReal(old_name:str, real_name:str):
  low_old = old_name.lower()
  low_real = real_name.lower()
  if low_old == low_real: return True # direct match
  compare = low_real + "."
  return low_old[:len(compare)] == compare # chunked model slot

BoneAss = List[List[int]]
VertAss = List[List[bpy.types.MeshVertex]]

def getBonesPerGroup(target:bpy.types.Object):
  mesh_data = target.data
  assert isinstance(mesh_data, bpy.types.Mesh)
  all_bones:BoneAss = []
  all_verts:VertAss = []
  for slot_idx in range(0,len(target.material_slots)):
    bpy.ops.object.mode_set_with_submode(mode='EDIT',mesh_select_mode=set(['VERT']))
    target.active_material_index = slot_idx
    bpy.ops.object.material_slot_select()
    bpy.ops.object.mode_set_with_submode()

    verts = [v for v in mesh_data.vertices if v.select]
    bones = set( g.group for v in verts for g in v.groups if target.vertex_groups[g.group].name[:2] == "G_" )

    all_verts.append(verts)
    all_bones.append(list(bones))

    bpy.ops.object.mode_set_with_submode(mode='EDIT',mesh_select_mode=set(['VERT']))
    bpy.ops.object.material_slot_deselect()
  
  return all_verts, all_bones

def guessChunks(target:bpy.types.Object):
  print("Calculating Chunks")
  mesh_data = target.data
  assert isinstance(mesh_data, bpy.types.Mesh)

  all_verts, all_bones = getBonesPerGroup(target)

  chunks_needed = []

  mesh = bmesh.new()
  mesh.from_mesh(mesh_data)

  for idx, (verts,bones) in enumerate(zip(all_verts,all_bones)):
    if len(bones) < 256:
      chunks_needed.append(1)
      continue
    print(f"Calculating: {idx}")
    vert_nums = [v.index for v in verts]

    chunks:List[Set[int]] = []

    relevant_faces = [face for face in mesh.faces if all(v.index in vert_nums for v in face.verts)]
    print(f"  Faces: {len(relevant_faces)}")

    for face in relevant_faces:
      face:bmesh.types.BMFace
      face_bones = set(g.group for v in face.verts for g in mesh_data.vertices[v.index].groups)

      target_chunk = None
      added:Set[int] = set()
      added_count = len(target.vertex_groups) + 10

      for chunk in chunks:
        wouldbe = face_bones.difference(chunk)
        woudbe_count = len(wouldbe)
        if woudbe_count < added_count and len(chunk) + woudbe_count <= 256:
          added_count = woudbe_count
          added = wouldbe
          target_chunk = chunk
          if added_count == 0:
            break

      if target_chunk is None:
        print(f"  Adding Chunk {len(chunks)}")
        chunks.append(face_bones)
      else:
        target_chunk |= added

    chunks_needed.append(len(chunks))

  return chunks_needed

def fixMaterialOrdering(target:bpy.types.Object, real_name_order:List[str]):
  mesh_data = target.data
  assert isinstance(mesh_data, bpy.types.Mesh)
  print(target)

  bpy.ops.object.mode_set_with_submode()
  for obj in bpy.context.selected_objects:
    obj.select_set(False)
  bpy.context.view_layer.objects.active = target

  bpy.ops.object.mode_set_with_submode(mode='EDIT',mesh_select_mode=set(['VERT']))
  for old_idx in range(0,len(target.material_slots)):
    target.active_material_index = old_idx
    bpy.ops.object.material_slot_deselect()

  old_name_order:List[str] = [ mat.name for mat in mesh_data.materials ]
  print("Old Materials:", old_name_order)
  print("New Materials:", real_name_order)

  bpy.ops.object.mode_set_with_submode(mode='EDIT',mesh_select_mode=set(['FACE']))

  # short circuit the reorder work if the materials are already correct ordering
  if len(old_name_order) != len(real_name_order) or not all(matchesReal(old_name, real_name) for old_name, real_name in zip(old_name_order, real_name_order)):

    # validate that all present materials are known and associate them with their real material names/order
    all_matches:List[List[int]] = [[] for _ in real_name_order]
    for old_idx, old_name in enumerate(old_name_order):
      found = False
      for real_idx, real_name in enumerate(real_name_order):
        if matchesReal(old_name, real_name):
          print(f"Assigning {old_idx}:{old_name} to {real_idx}:{real_name}")
          found = True
          all_matches[real_idx].append(old_idx)
          break
      if not found:
        print(f"FAIL: Unknown material name '{old_name}', valid names are: {' '.join(real_name_order)}")
        exit(0)

    # migrate all material assignments into the new properly ordered materials
    for real_idx, real_name in enumerate(real_name_order):
      matches = all_matches[real_idx]

      temp_name = real_name + "_temp"
      added_idx = len(mesh_data.materials)
      print(f"Creating {real_idx}:{real_name} as {added_idx}:{temp_name}")
      m = bpy.data.materials.new(temp_name)
      mesh_data.materials.append(m)

      print(target.material_slots)

      for old_idx in matches:
        print(f"Moving {old_idx} to {added_idx}")
        target.active_material_index = old_idx
        bpy.ops.object.material_slot_select()
        target.active_material_index = added_idx
        bpy.ops.object.material_slot_assign()
        bpy.ops.object.material_slot_deselect()

    # shift slots down
    for real_idx in range(0,len(real_name_order)):
      offset_idx = real_idx + len(old_name_order)
      print(f"Moving {real_idx} to {real_idx}")
      target.active_material_index = offset_idx
      bpy.ops.object.material_slot_select()
      target.active_material_index = real_idx
      bpy.ops.object.material_slot_assign()
      bpy.ops.object.material_slot_deselect()

    # remove old materials
    for _ in old_name_order:
      print(f"Removing {mesh_data.materials[0].name}")
      mesh_data.materials.pop(index=0)

  # re-assign correct names to the materials
  for real_idx, real_name in enumerate(real_name_order):
    print(f"Renaming {real_idx}:{mesh_data.materials[real_idx].name} to {real_name}")
    mesh_data.materials[real_idx].name = real_name

  print("Final Materials:")
  assert len(mesh_data.materials) == len(real_name_order)
  for actual_idx, mat in enumerate(mesh_data.materials):
    print(mat.name)
    assert mat.name == real_name_order[actual_idx]

  chunks_needed = guessChunks(target)
  print(f"CHUNKING:" + ",".join(str(chunk) for chunk in chunks_needed))

  return True

  return True
def selectMesh(target:bpy.types.Object):
  bpy.ops.object.mode_set(mode='OBJECT')
  for obj in bpy.context.selected_objects:
    obj.select_set(False)

  target.hide_set(False)
  target.parent.hide_set(False)
  target.select_set(True)
  target.parent.select_set(True)

def main():
  print("Starting Python Export Hook")

  # arg parsing
  argv = sys.argv
  py_args = argv[argv.index("--") + 1:]  # get all args after "--"
  assert len(py_args) == 2, "arg count is wrong"
  work_dir = Path(py_args[0])
  asset_path = py_args[1]
  asset_name = asset_path.split("/")[-1]

  # load dumped info
  info_file = work_dir.joinpath(f"{DUMP_SUBDIR}{asset_path}{INFO_SFX}")
  slot_order = [dirty.strip() for dirty in open(info_file,'r').readlines()[0].split(",")]

  target = getMesh()
  target.hide_set(False)
  target.parent.hide_set(False)

  fixMaterialOrdering(target, slot_order)

  selectMesh(target)
  
  # do export
  addon_utils.enable("io_scene_fbx", default_set=True, persistent=False, handle_error=None)
  export_path = work_dir.joinpath(FAST_BLENDER_OUT)
  export_path.mkdir(exist_ok=True)
  export_path = export_path.joinpath(f"{asset_name}.fbx")
  bpy.ops.export_scene.fbx(filepath=export_path.as_posix(), check_existing=False, use_selection=True, bake_anim=False)

  exit(0)

try:
  main()
  exit(0)
except Exception as e:
  print("FAIL: unknown exception, check error.log")
  print(e)
  exit(1)