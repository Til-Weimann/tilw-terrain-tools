# Enhanced Maps Tool
This tool allows Arma Reforger modders to **easily create much improved paper maps** for their terrains.

> [!NOTE]
> If this tool helped you, please link it in your mod description, so other modders can find out about it.
>
> **Example:** Paper Map created using the [Enhanced Maps](https://github.com/Til-Weimann/EnhancedMaps/) tool

![t](https://github.com/user-attachments/assets/78a4a97c-17d9-493c-a73e-16b32de27c2c)

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
11. Run the requirements.bat file, it will make sure you have all necessary Python dependencies (you need of course need Python if you don't have it yet).
12. You should now be good to run the generate.py script from the main folder. It will create a result.png file, which is the map - you can rename it to something else, like the name of your terrain.
13. Import the PNG into the WB, the standard path is UI/Textures/Map/worlds.
14. Open the imported EDDS texture, go into the import settings on the right and change "Color Space" to "To SRGB", then hit "Reimport Resource (PC)" in the top.
15. Back in your terrain world, find your MapEntity prefab and set "Satellite background texture" to the texture.

# Q&A

> My trees were not plotted correctly, or the water level is weird.

Make sure your terrain is located at the 0 0 0 coordinate. If it's not, either fix that or use the terrain-coords option in the config.

> Can I customize the map somehow?

Yes, the conf.yml file has extra parameters that allow you to make some adjustments.

> The python script doesn't run correctly, but automatically closes before I can see what's wrong.

In the folder, click the top bar like when copying the file path, type "cmd", press enter. Now enter "generate.py" to run the script. This way, the window will always stay open and allow you to read any errors.

> I need help with my general Python setup, I can't get it to work.

I'll gladly help with things related to the actual script, but I will not help you with installing Python, use your favorite search engine for this.

> I don't have QGIS and don't want to install it. Is there another way?

You do need the gdaldem.exe application, however you can also install gdal / gdaldem via the [OSGeo4W installer](https://trac.osgeo.org/osgeo4w/) (or from [other distributors](https://gdal.org/en/stable/download.html#binaries)) if you don't want QGIS.

> I have a question, how do I best contact you?

On Discord, my name is tilw. I am active on the ARMA discord.
