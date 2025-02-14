import os
from PIL import Image
import numpy as np
import time
from pathlib import Path
import math

print("Unnamed Satmap Generation Tool by TilW")

size_input = input("Enter terrain size in meters, separated by an x - e. g. 4096x4096: ")
nums = size_input.split("x")
terrain_size = (round(float(nums[0])), round(float(nums[1])))

wdir = os.getcwd()
masks_dir = os.path.join(wdir, "masks")
mat_dir = os.path.join(wdir, "Surfaces")

# Required functions

def get_mat_param(mat_name, param_name):
    # Search for the mat_name file
    for mp in Path(mat_dir).rglob(mat_name + '.emat'):
        result = search_mat_file(mp, param_name) # Search for parameter
        if result != None:
            return result
        
        parent = search_mat_file(mp, "TerrainMaterial :") # Search for parent material
        if parent != None:
            return get_mat_param(extract_fn_from_rn(parent), param_name) # Look in parent material instead
            # "{F4587E72B95D842B}Terrains/Common/Surfaces/Pebbles_02.emat" {
        
        # If there is no parent material, return none
        match param_name:
            case "Color":
                return "1 1 1 1"
            case "MiddleColor":
                return "1 1 1 1"
            case "BCRMiddleMap":
                return None
            case "MiddleScaleUV":
                return "100"
        return None
    return None

def search_mat_file(mat_fp, param_name):
    if os.path.exists(mat_fp):
        with open(mat_fp) as file:
            for line in file:
                words = line.split(param_name + " ")
                if len(words) == 1:
                    continue
                return words[1].removesuffix("\n")
    
    return None

def extract_fn_from_rn(rn):
    return rn.split('.')[-2].split('/')[-1]

def get_fp_from_dir(fn, dir):
    for fp in Path(dir).rglob(fn):
        return fp
    
def blend_images_with_masks(images, masks):
    # Ensure the images and masks are all the same size
    size = images[0].size
    images = [img.convert("RGBA").resize(size) for img in images]
    masks = [mask.convert("L").resize(size) for mask in masks]
    
    # Normalize masks so they add up to 1 at every pixel
    masks_np = [np.array(mask, dtype=np.float32) / 255.0 for mask in masks]
    del masks
    total_mask = sum(masks_np)
    masks_np = [mask / total_mask for mask in masks_np]
    del total_mask
    
    # Convert images to numpy arrays
    images_np = [np.array(img, dtype=np.float32) for img in images]
    del images
    
    # Blend images using the masks
    blended = sum(img * mask[..., None] for img, mask in zip(images_np, masks_np))
    del masks_np
    
    # Convert back to PIL image
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    return Image.fromarray(blended, mode="RGBA")

def linear_to_srgb(color):
    def convert(c):
        return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return tuple(convert(c) for c in color)

# Generation

print("Starting generation...")
start_time = time.time()

images = []
masks = []

for mask_file in os.listdir(masks_dir):

    mask_name = os.fsdecode(mask_file).removesuffix('.png')
    print("Processing mask: " + mask_name)
    middle_scale = float(get_mat_param(mask_name, "MiddleScaleUV"))
    tile_size = (math.ceil(terrain_size[0] / middle_scale), math.ceil(terrain_size[1] / middle_scale)) # 4096 / 100 = 40,69
    
    mm_name = get_mat_param(mask_name, "BCRMiddleMap")
    if mm_name is None:
        print("ERROR - No material found for " + mask_name + ", skipping...")
        continue
    mm_fp = get_fp_from_dir(extract_fn_from_rn(mm_name) + ".png", mat_dir)
    if mm_fp is None:
        print("ERROR - No texture found for " + mm_name + ", skipping...")
        continue
    if not os.path.exists(mm_fp):
        print("ERROR - Texture " + mm_fp + " not found, skipping...")
        continue
    middle_map = Image.open(mm_fp)

    middle_map = middle_map.resize(tile_size) # 512x512

    layer = Image.new("RGBA", terrain_size)

    # tile

    for y in range(layer.size[1], 0, -middle_map.size[1]):
        for x in range(0, layer.size[0], middle_map.size[0]):
            tile_x = x
            tile_y = y - middle_map.size[1]

            tile = middle_map.crop((
                0,
                0 if tile_y >= 0 else -tile_y,  # Crop the top edge
                middle_map.size[0] if tile_x + middle_map.size[0] <= layer.size[0] else layer.size[0] - tile_x,  # Crop the right edge
                middle_map.size[1] if tile_y + middle_map.size[1] <= layer.size[1] else layer.size[1] - tile_y  # Crop the bottom edge
            ))

            layer.paste(tile, (max(tile_x, 0), max(tile_y, 0)))

    mask = Image.open(os.path.join(masks_dir, mask_file)).convert('L')
    mask = mask.resize(terrain_size)

    color_params = get_mat_param(mask_name, "MiddleColor").split(" ")
    color = np.array((float(color_params[0]), float(color_params[1]), float(color_params[2]), float(color_params[3])), np.float32)

    layer_np = np.array(layer, np.float32)
    layer_np *= linear_to_srgb(color)
    layer_np = np.clip(layer_np, 0, 255)
    layer = Image.fromarray(layer_np.astype(np.uint8), "RGBA")
    
    images.append(layer)
    masks.append(mask)

print("Blending layers...")
result = blend_images_with_masks(images, masks)
del layer, layer_np, middle_map
print("Saving result...")
result.save(os.path.join(wdir, "RESULT.png"))
del result
print("Generation completed in " + str(round(time.time() - start_time, 2)) + " seconds!")
input("Press ENTER to close...")