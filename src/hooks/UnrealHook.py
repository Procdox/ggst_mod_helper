import unreal
import sys

try:
  py_args = sys.argv

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
  task.destination_path = "/Game/" + py_args[2]
  task.filename = py_args[1]
  task.options = fbx_options
  task.replace_existing = True
  task.save = True
  assetTools.import_asset_tasks([task])
  unreal.log_warning("Successfully exported")
except Exception as error:
  unreal.log_warning("FAIL: " + str(error))
