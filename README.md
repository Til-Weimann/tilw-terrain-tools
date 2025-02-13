# Enhanced Maps Tool
'Enhanced Maps' custom map generation tool for Arma Reforger.

This tool allows Arma Reforger modders to **easily create much improved paper maps** for their terrains.

> [!NOTE]
> If this tool helped you, please link this repository in your mod description, so other modders can find out about it.
>
> **Example:** Paper Map created using the [Enhanced Maps](https://github.com/Til-Weimann/EnhancedMaps/) tool

# Usage

1. Download the newest ZIP file from [Releases](https://github.com/Til-Weimann/EnhancedMaps/releases).
2. Extract ZIP contents to a place of your liking.
3. The tool needs the GDALDEM application to work, it is included in QGIS. Download it if you don't have it yet.
4. Open conf.yml from the folder with a text editor, and paste the path to gdaldem.exe so the tool can find it.
5. Download the [Enhanced Maps](https://reforger.armaplatform.com/workshop/644B042109700804-EnhancedMaps) mod from the Workshop.
6. Add the mod as a project to the Workbench launcher. Right click your terrain mod, select "Open with addons", choose Enhanced Maps and open.
> [!TIP]
> Enhanced Maps **does not** need to be a dependency of your mod.
6. Open your terrain world, switch to the Terrain Tools "Info & Diags" tab.
7. Again open **conf.yml**, this time entering cell-size (planar resolution), height-range-min and height-range-max from the Info & Diags tab, if they differ.
8. Switch back the the Terrain Tools main tab, and click Export Heightmap after selecting the modified instead of base version. Save it specifically as "hm.png" in the data subfolder of the download folder.
9. Go into the data subfolder using the Explorer, click into the file path bar in the top and copy the folder path.
10. Switch back to the Workbench and find the Tree Export tool, it has a pine tree icon. Paste the copied data path into the tool options, and click Export in the bottom.
11. You should now be good to run the Python script from the main folder. It will created an EhM.png file, which is your map - you can rename it to something else, like the name of your terrain.
12. Import the PNG into the WB, the standard path is UI/Textures/Map/worlds.
13. Open the imported EDDS texture, go into the import settings on the right and change "Color Space" to "To SRGB", then hit "Reimport Resource (PC)" in the top.
14. Back in your terrain world, find your MapEntity prefab and set "Satellite background texture" to the texture.
