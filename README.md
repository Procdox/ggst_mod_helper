# ggst_mod_helper
 
## Installation:
This tool requires
- A valid GGST installation
- Umodel installation (modified preferred)
- Noesis
- UE Packer
- Blender 3.0.0
- Unreal 4.25 (modified preferred)

With all this, installation can be done by
1: installing Python (tested with 3.8.10)
2: python -m venv env
3: ./env/Scripts/python.exe -m pip install -r requirements.txt

Then launched with 
- ./env/Scripts/python.exe ggst_mod_helper.py

## Configuration
The first tab of the tool will present you with a bunch op options, fill these out with the paths to the respective tools.
It also includes an option for "Working Dir" this is the directory that the tool will use for all of its processes, set it to a new folder wherever you like.
Keep in mind: anything in this folder is volatile, the tool may delete or replace files in it during its work.
Lastly is the AES key for GGST, I will not be distributing this or telling you how to obtain it.

## Dump From Game
The second tab is effectively a wrapper for Umodel and Noesis, letting you export character models quickly. It also dumps some information from the assets for validation purposes.
"Scan Game Files" will do just as it says, then display a list of all characters found. You can then select any characters and mesh types and hit "Export".
The extracted game assets be under the /dump/ subdirectory of the working directory.
The converted fbx models will be under /models/

## Fast Package Blender
This is currently the powerhouse of the tool. This lets you quickly convert character models from Blender to .pak files.
The Target file should be a .blend file.
The Target Asset should be the game asset you want to export to, e.g. "Chara/RAM/Costume01/Mesh/ram_body"
The Target Mod is the name of the mod you want to export to.
The resulting pak file will be in the /paks/ subdirectory of the working directory.

## Working Directory Contents
Blender_Fast_Build: This is where converted FBX's are stored during the fast package process.
dump: This is where game assets are extracted to.
moved_mods: If the tool detects mods, and you choose to move them, they will be placed here. Its not very smart about this, you should probably just Unverum to re-enable mods.
paks: This is where mod directory structures and final .pak are output during the fast package process.
Unreal_Fast_Build: This is an Unreal project that is used for converting and cooking FBX's during the fast package process.

