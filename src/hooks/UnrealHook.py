import unreal
import sys

def buildImportOptions():
  fbx_options = unreal.FbxImportUI()
  skel_options = unreal.FbxSkeletalMeshImportData()
  fbx_options.set_editor_property('automated_import_should_detect_type', False)
  fbx_options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
  fbx_options.set_editor_property('skeletal_mesh_import_data', skel_options)
  
  
  # properties are ordered in the same order as they appear in the editor
  fbx_options.set_editor_property('import_mesh', True)
  fbx_options.set_editor_property('import_as_skeletal', True)
  skel_options.set_editor_property('import_content_type', unreal.FBXImportContentType.FBXICT_ALL)
  fbx_options.set_editor_property('skeleton', None)

  skel_options.set_editor_property('vertex_color_import_option', unreal.VertexColorImportOption.REPLACE)
  skel_options.set_editor_property('update_skeleton_reference_pose', False)
  skel_options.set_editor_property('use_t0_as_ref_pose', False)
  skel_options.set_editor_property('preserve_smoothing_groups', True)
  skel_options.set_editor_property('import_meshes_in_bone_hierarchy', True)
  skel_options.set_editor_property('import_morph_targets', False)
  skel_options.set_editor_property('import_mesh_lo_ds', False)
  skel_options.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
  skel_options.set_editor_property('normal_generation_method', unreal.FBXNormalGenerationMethod.BUILT_IN)
  skel_options.set_editor_property('compute_weighted_normals', True)
  fbx_options.set_editor_property('create_physics_asset', True)
  fbx_options.set_editor_property('physics_asset', None)

  fbx_options.set_editor_property('import_animations', False)

  skel_options.set_editor_property('convert_scene', True)
  skel_options.set_editor_property('force_front_x_axis', False)
  skel_options.set_editor_property('convert_scene_unit', False)

  fbx_options.set_editor_property('import_materials', False)
  fbx_options.set_editor_property('import_textures', False)
  
  return fbx_options

def ImportAssets(src_path, dest_path):
  assetTools = unreal.AssetToolsHelpers.get_asset_tools()

  options = buildImportOptions()

  task = unreal.AssetImportTask()
  task.automated = True
  task.destination_path = dest_path
  task.filename = src_path
  task.options = options
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