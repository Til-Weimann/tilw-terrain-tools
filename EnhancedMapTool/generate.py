import yaml
import os
from PIL import Image, ImageFilter
import numpy as np
from scipy.ndimage import binary_dilation
import shutil
import time
import traceback

try:
    Image.MAX_IMAGE_PIXELS = None

    start_time = time.time()

    wdir = os.getcwd()
    tempdir = os.path.join(wdir, "temp")
    datadir = os.path.join(wdir, "data")

    # Read config
    with open(os.path.join(wdir, 'conf.yml'), 'r') as conf_file:
        conf = yaml.safe_load(conf_file)

    # Phase 1 - Verify setup
    print("Phase 1: Verifying setup...", flush=True)

    if not os.path.exists(conf["gdaldem-path"]):
        print("Generation failed: GDAL not found, make sure the path is correct!", flush=True)
        input("Press ENTER to close...")

    if not os.path.exists(os.path.join(datadir, "hm.png")):
        print("Generation failed: Heightmap (.../data/hm.png) not found, make sure you saved it to that folder with the right name!", flush=True)
        input("Press ENTER to close...")

    if not os.path.exists(tempdir):
        os.makedirs(tempdir)

    # Phase 2 - Generate relief

    print("Phase 2: Generating relief...", flush=True)

    hm = Image.open(os.path.join(datadir, "hm.png")).convert("I")
    hm = hm.resize((hm.size[0]-1, hm.size[1]-1))
    if conf["cell-size"] != 2.0:
        hm = hm.resize(tuple([int((conf["cell-size"] / 2.0)*x) for x in hm.size]))
    hm.save(os.path.join(tempdir, "hm.png"))

    hm_size = hm.size

    scale = conf["relief-strength"] * 15 * 2048 / ( conf["height-range-max"] - conf["height-range-min"] )
    cmd = '"' + conf["gdaldem-path"] + '" hillshade ' + os.path.join(tempdir, "hm.png") + " " + os.path.join(tempdir, "rm.png") + " -igor -s " + str(scale)
    os.system(cmd)

    # Phase 3 - Create ocean
    print("Phase 3: Creating ocean...", flush=True)

    hdata = np.array(hm)
    del hm

    # Create ocean mask
    y_offset = float(conf["terrain-coords"].split(" ")[1])
    ocean_threshold = max(0, (-conf["height-range-min"] - y_offset) / (conf["height-range-max"] - conf["height-range-min"]))
    oceanmask = np.where((hdata < ocean_threshold * 65535), 255, 0).astype(np.uint8)

    c = (hdata / hdata.max() * 255).astype(np.uint8)
    rgba_array = np.stack((c, c, c, oceanmask), axis=-1)
    del oceanmask

    # Colorize ocean
    ocean_colors = str(conf["ocean-color"]).split(" ")
    ocean_darkness = 1.75 * 255.0 * float(conf["ocean-darkness"]) * 10 * ocean_threshold
    oc_r = float(ocean_colors[0]) / ocean_darkness
    oc_g = float(ocean_colors[1]) / ocean_darkness
    oc_b = float(ocean_colors[2]) / ocean_darkness

    rgba_array[..., 0] = np.clip(rgba_array[..., 0] * oc_r, 0, 255)
    rgba_array[..., 1] = np.clip(rgba_array[..., 1] * oc_g, 0, 255)
    rgba_array[..., 2] = np.clip(rgba_array[..., 2] * oc_b, 0, 255)

    ocean_final = Image.fromarray(rgba_array, mode="RGBA")
    del rgba_array

    # Add sub surface relief
    rm = Image.open(os.path.join(tempdir, "rm.png")).convert("RGBA")
    orm = rm.copy()
    orm.putalpha(int(float(conf["ocean-relief-strength"]) * 12.5))
    ocean_final.alpha_composite(orm)
    del orm

    # Phase 4 - Plot foliage
    print("Phase 4: Plotting foliage...", flush=True)

    def plot_foliage(size, color, dil, offset, paths):

        supermap = Image.new('RGBA', size, (0, 0, 0, 0))

        colors = color.split(" ")
        color_tuple = (int(colors[0]), int(colors[1]), int(colors[2]), int(colors[3]))

        offset_coords = offset.split(" ")
        offset_tuple =  (float(offset_coords[0]), float(offset_coords[2]))

        for path in paths:
            print("Plotting " + path, flush=True)
            img = Image.new('RGBA', size, (0, 0, 0, 0))

            if not os.path.exists(path):
                continue
            
            # Plot
            for line in open(path):
                params = line.split(" ")
                posX = round((float(params[0])-offset_tuple[0]) / 2)
                posY = round(size[1] - (float(params[1])-offset_tuple[1]) / 2)
                if 0 <= posX <= size[0]-1 and 0 <= posY <= size[1]-1:
                    img.putpixel((posX, posY), color_tuple)

            supermap.alpha_composite(img) # stack on top of supermap

        # Dilate
        if dil > 0:
            image_array = np.array(supermap)
            binary_mask = (image_array[..., 3] > 0).astype(np.uint8)
            dilated_mask = binary_dilation(binary_mask, iterations=dil).astype(np.uint8)
            dilated_image = np.zeros_like(image_array, dtype=np.uint8)
            dilated_image[dilated_mask == 1] = color_tuple
            supermap = Image.fromarray(dilated_image)

        return supermap


    veg_tex = Image.new('RGBA', (hm_size[0], hm_size[1]), (0, 0, 0, 0))

    # Plot foliage files
    veg_tex.alpha_composite(plot_foliage(size=hm_size, dil=0, color=conf["veg-color-bush"], offset=conf["terrain-coords"], paths=[os.path.join(datadir, "Bush.txt"), os.path.join(datadir, "Bush_Leafy.txt")]))
    veg_tex.alpha_composite(plot_foliage(size=hm_size, dil=0, color=conf["veg-color-reed"], offset=conf["terrain-coords"], paths=[os.path.join(datadir, "Bush_Reed.txt")]))
    veg_tex.alpha_composite(plot_foliage(size=hm_size, dil=0, color=conf["veg-color-dead"], offset=conf["terrain-coords"], paths=[os.path.join(datadir, "Withered.txt")]))
    veg_tex.alpha_composite(plot_foliage(size=hm_size, dil=1, color=conf["veg-color-deci"], offset=conf["terrain-coords"], paths=[os.path.join(datadir, "Leafy.txt")]))
    veg_tex.alpha_composite(plot_foliage(size=hm_size, dil=1, color=conf["veg-color-coni"], offset=conf["terrain-coords"], paths=[os.path.join(datadir, "Conifer.txt")]))

    veg_tex = veg_tex.filter(ImageFilter.GaussianBlur(0.6 * conf["veg-blur-size"]))

    # Phase 5 - Finish up
    print("Phase 5: Finishing up...", flush=True)

    result = Image.alpha_composite(rm, ocean_final)
    result = result.filter(ImageFilter.GaussianBlur(0.75))

    result.alpha_composite(veg_tex)
    del veg_tex

    #result.show()
    result.save(os.path.join(wdir, "RESULT.png"))
    del result

    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)

    print("Generation complete, it took " + str(round(time.time() - start_time, 2)) + " seconds!", flush=True)
    input("Press ENTER to close...")

except Exception as ex:
    print("FATAL ERROR - Exception occured during generation!", flush=True)
    traceback.print_exc()
    input("Press ENTER to close...")