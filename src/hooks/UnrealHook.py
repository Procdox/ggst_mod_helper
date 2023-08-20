import unreal
import sys

def ImportAssets(src_path, dest_path):
  assetTools = unreal.AssetToolsHelpers.get_asset_tools()

  mesh_options = unreal.FbxStaticMeshImportData()
  mesh_options.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS

  fbx_options = unreal.FbxImportUI()
  fbx_options.import_mesh = True
  fbx_options.import_textures = False
  fbx_options.import_materials = False
  fbx_options.import_as_skeletal = True
  fbx_options.static_mesh_import_data = mesh_options

  task = unreal.AssetImportTask()
  task.automated = True
  task.destination_path = dest_path
  task.filename = src_path
  task.options = fbx_options
  task.replace_existing = True
  task.save = True
  assetTools.import_asset_tasks([task])

def SetOutline(dest_path, info_path, chunks_raw):
  parts = [ part.split(":") for part in open(info_path).readlines()[1].split(",") ]
  idx_assocs = { key.lower():int(val) for key,val in parts }
  chunks = [int(x) for x in chunks_raw.split(",")]

  unreal.log_warning(idx_assocs)
  unreal.log_warning(chunks)

  EAL = unreal.EditorAssetLibrary()
  for assetPath in EAL.list_assets(dest_path):
    asset = EAL.load_asset(assetPath)
    if isinstance(asset, unreal.SkeletalMesh):
      result = []
      materials = asset.materials
      for c, mat in zip(chunks, materials):
        mat_name = mat.material_slot_name
        slot_type = idx_assocs[str(mat_name).lower()]
        result += [slot_type for _ in range(0,c)]

      unreal.log_warning(result)
      info = asset.get_editor_property("lod_info")[0]
      info.set_editor_property('outline_material_index', result)
      asset.set_editor_property("lod_info", [info])
      
    unreal.EditorAssetLibrary.save_asset(assetPath)

src_path = sys.argv[1]
dest_path = "/Game/" + sys.argv[2]
info_path = sys.argv[3]
chunks_raw = sys.argv[4]

try:
  ImportAssets(src_path, dest_path)
  SetOutline(dest_path, info_path, chunks_raw)
  unreal.log_warning("Successfully exported")
except Exception as error:
  unreal.log_warning("FAIL: " + str(error))