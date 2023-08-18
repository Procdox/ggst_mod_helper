import unreal

DEBUG = True

if DEBUG:
  dest_path = "/Game/Chara/RAM/Costume01/Mesh"
  src_path = "C:/Users/Andrew/Documents/projects/ggst_modding/testing/Blender_Fast_Build/ram_body.fbx"
else:
  import sys
  py_args = sys.argv
  dest_path = "/Game/" + py_args[2]
  src_path = py_args[1]

try:
  assetTools = unreal.AssetToolsHelpers.get_asset_tools()

  mesh_options = unreal.FbxStaticMeshImportData()
  mesh_options.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS

  fbx_options = unreal.FbxImportUI()
  fbx_options.import_mesh = True
  fbx_options.import_textures = False
  fbx_options.import_materials = False
  fbx_options.import_as_skeletal = False
  fbx_options.static_mesh_import_data = mesh_options

  task = unreal.AssetImportTask()
  task.automated = True
  task.destination_path = dest_path
  task.filename = src_path
  task.options = fbx_options
  task.replace_existing = True
  task.save = True
  assetTools.import_asset_tasks([task])
  unreal.log_warning("Successfully exported")

  EAL = unreal.EditorAssetLibrary()
  for assetPath in EAL.list_assets(dest_path):
    unreal.EditorAssetLibrary.save_asset(assetPath)

except Exception as error:
  unreal.log_warning("FAIL: " + str(error))
