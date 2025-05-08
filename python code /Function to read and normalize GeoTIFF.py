import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.warp import reproject, Resampling
from skimage.draw import line

# Define a function to read and normalize a GeoTIFF
def read_and_normalize_tif(file_path):
    with rasterio.open(file_path) as src:
        image = src.read(1).astype(float)  # Read the first band as float
        no_data_value = src.nodata  # Retrieve the no-data value from metadata
        profile = src.profile  # Get the profile for saving later

        # Normalize the image to [0, 1]
        min_val = np.nanmin(image)
        max_val = np.nanmax(image)
        normalized_image = (image - min_val) / (max_val - min_val)

        # Ensure values are within [0, 1]
        normalized_image = np.clip(normalized_image, 0, 1)
    
    return normalized_image, profile


input_file_path = "input the file path.tif"

# Read and normalize the image
normalized_image, profile = read_and_normalize_tif(input_file_path)

# Save the normalized result to a GeoTIFF
output_file_path = "output the file path.tif"

# Save the normalized image as a GeoTIFF
with rasterio.open(
    output_file_path,
    "w",
    driver="GTiff",
    height=normalized_image.shape[0],
    width=normalized_image.shape[1],
    count=1,  # Single band
    dtype="float32",  # Save as 32-bit floating point
    crs=profile['crs'],  # Use the CRS from the original image
    transform=profile['transform']  # Use the geotransform from the original image
) as dst:
    # Write the normalized result to the first band
    dst.write(normalized_image, 1)

print(f"Normalized image saved at: {output_file_path}")

# Check the min and max values of the normalized result
print(f"Normalized result range: {np.nanmin(normalized_image):.1f} to {np.nanmax(normalized_image):.1f}")
