import os
from PIL import Image
import numpy as np
import time
from pathlib import Path
import traceback

try:

    Image.MAX_IMAGE_PIXELS = None

    print("Seamless Satmap Tool, by TilW", flush=True)

    size_input = input("Enter terrain size in meters, separated by an x - e. g. 4096x4096: ")
    nums = size_input.split("x")
    terrain_size = (round(float(nums[0])), round(float(nums[1])))

    wdir = os.path.dirname(os.path.realpath(__file__))
    masks_dir = os.path.join(wdir, "masks")
    data_dir = os.path.join(wdir, "data")

    # Utils -----------------------------------------------------------------------------------------------------------


    class IncrementalBlender:
        # Everyone please give a round of applause to ChatGPT for this blender thing, most of the rest I did myself though lol
        def __init__(self):
            """
            Initialize the blender with accumulators for the blended image and total mask.
            """
            self.blended_accumulator = None
            self.total_mask_accumulator = None

        def blend(self, image, mask):
            """
            Blend an image with a mask into the accumulated result.

            Args:
                image (PIL.Image): The RGBA image to blend.
                mask (PIL.Image): The grayscale mask corresponding to the image.

            Returns:
                self: The IncrementalBlender instance (for chaining).
            """
            # Convert image and mask to NumPy arrays
            img_np = np.array(image.convert("RGBA"), dtype=np.float32)
            mask_np = np.array(mask.convert("L"), dtype=np.float32) / 255.0  # Normalize mask to [0, 1]

            # If it's the first image, initialize the accumulators
            if self.blended_accumulator is None:
                self.blended_accumulator = np.zeros_like(img_np, dtype=np.float32)
                self.total_mask_accumulator = np.zeros(mask_np.shape, dtype=np.float32)

            # Accumulate the weighted blend and update the total mask
            self.blended_accumulator += img_np * mask_np[..., None]
            self.total_mask_accumulator += mask_np

            return self  # Enable method chaining

        def get_result(self):
            """
            Finalize the blended image by normalizing the accumulated values.

            Returns:
                PIL.Image: The blended RGBA image.
            """
            if self.blended_accumulator is None:
                raise ValueError("No images have been blended yet.")

            # Normalize the blended image by the total mask
            total_mask_accumulator = np.clip(self.total_mask_accumulator, 1e-6, None)  # Avoid division by zero
            result = self.blended_accumulator.copy()
            result[..., :3] /= total_mask_accumulator[..., None]  # Normalize RGB
            result[..., 3] = 255  # Set alpha channel to fully opaque

            # Convert back to a PIL image
            result = np.clip(result, 0, 255).astype(np.uint8)
            return Image.fromarray(result, mode="RGBA")


    def get_mat_param(mat_fp, param_name):
        result = search_mat_file(mat_fp, " " + param_name + " ") # Search for parameter
        if result != None:
            return result
        
        parent = search_mat_file(mat_fp, "TerrainMaterial : ") # Search for parent material
        if parent is not None:
            parent_fp = find_file_in_dir(data_dir, extract_fn_from_rn(parent).removesuffix(".emat"), ["emat"])
            if parent_fp is None:
                print("ERROR - Could not find " + mask_name + ".emat parent material in data folder, skipping...", flush=True)
                return None
            else:
                return get_mat_param(parent_fp, param_name) # Look in parent material instead
        else:
            # No parent material, use defaults
            match param_name:
                case "Color":
                    return "1 1 1 1"
                case "MiddleColor":
                    return "1 1 1 1"
                case "BCRMiddleMap":
                    return None
                case "MiddleScaleUV":
                    return "100"
                case "BCRMap":
                    return None
        return None

    def search_mat_file(mat_fp, param_name):
        if os.path.exists(mat_fp):
            with open(mat_fp) as file:
                for line in file:
                    words = line.split(param_name)
                    if len(words) == 1:
                        continue
                    return words[1].removesuffix("\n")
        return None

    def extract_fn_from_rn(rn):
        return rn.split('.')[-2].split('/')[-1]

    def find_file_in_dir(dir, name, extensions):
        for ext in extensions:
            pattern = f"{name}.{ext}"
            for fp in Path(dir).rglob(pattern):
                return fp
        print("ERROR - Failed to find file " + name + " " + str(extensions) + " in " + dir + " directory!", flush=True)

    def linear_to_srgb(color):
        def convert(c):
            return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
        return tuple(convert(c) for c in color)


    # Generation ----------------------------------------------------------------------------------------------------

    print("Starting generation...", flush=True)
    start_time = time.time()

    blender = IncrementalBlender()

    for mask_file in os.listdir(masks_dir):

        if not mask_file.endswith(".png"):
            continue
        mask_name = os.fsdecode(mask_file).removesuffix('.png')
        print("Processing mask: " + mask_name, flush=True)

        mat_fp = find_file_in_dir(data_dir, mask_name, ["emat"])
        if mat_fp is None:
            print("ERROR - Could not find " + mask_name + ".emat material in data folder, skipping...", flush=True)
            continue
        
        mm_name = get_mat_param(mat_fp, "BCRMiddleMap")
        if mm_name is None:
            print("WARNING - No middle map referenced in " + mask_name + ".emat, falling back on detail map...", flush=True)
            mm_name = get_mat_param(mat_fp, "BCRMap")
            if mm_name is None:
                print("ERROR - No detail map referenced in " + mask_name + ".emat either, skipping...", flush=True)
                continue

        mm_fp = find_file_in_dir(data_dir, extract_fn_from_rn(mm_name), ["png", "jpg"])
        if mm_fp is None:
            print("ERROR - No " + extract_fn_from_rn(mm_name) + " texture found in data folder, skipping...", flush=True)
            continue
        
        middle_map = Image.open(mm_fp)

        middle_scale = float(get_mat_param(mat_fp, "MiddleScaleUV"))
        tile_size = (round(middle_scale), round(middle_scale))
        middle_map = middle_map.resize(tile_size)

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

        color_params_m = get_mat_param(mat_fp, "MiddleColor").split(" ")
        color_params_d = get_mat_param(mat_fp, "Color").split(" ")
        color_m = np.array((float(color_params_m[0]), float(color_params_m[1]), float(color_params_m[2]), float(color_params_m[3])), np.float32)
        color_d = np.array((float(color_params_d[0]), float(color_params_d[1]), float(color_params_d[2]), float(color_params_d[3])), np.float32)
        color = linear_to_srgb(color_m * color_d)
        
        layer_np = np.array(layer, np.float32)
        layer_np *= color
        layer_np = np.clip(layer_np, 0, 255)
        layer = Image.fromarray(layer_np.astype(np.uint8), "RGBA")
        
        blender.blend(layer, mask)

    result = blender.get_result()
    del layer, layer_np, middle_map, mask
    print("Saving result...", flush=True)
    result.save(os.path.join(wdir, "RESULT.png"))
    del result
    print("Generation completed in " + str(round(time.time() - start_time, 2)) + " seconds!", flush=True)
    input("Press ENTER to close...")

except Exception as ex:
    print("FATAL ERROR - Exception occured during generation!", flush=True)
    traceback.print_exc()
    input("Press ENTER to close...")