import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.warp import reproject, Resampling
from rasterio.plot import show
from skimage.draw import line
from rasterio import open as rio_open
from scipy.signal import savgol_filter
from PIL import Image
import pandas as pd
import matplotlib as mpl





# Function to read the image using rasterio
def read_image(tif_path):
    #with rasterio.open(image_path) as dataset:
    with rasterio.open(tif_path) as src:
        image = src.read(1)
        transform = src.transform  # Get geotransform
        crs = src.crs  # Get coordinate reference system
        bounds = src.bounds  # Get bounding box
    return image, transform, crs, bounds


def extract_line_profile(tif_path, start_point_geo, end_point_geo, plot_line=True):
    """
    Extract the profile line from a TIFF file and optionally plot the line on the image.
    
    Parameters:
        tif_path (str): Path to the TIFF file.
        start_point_geo (tuple): Starting point in georeferenced coordinates (easting, northing).
        end_point_geo (tuple): Ending point in georeferenced coordinates (easting, northing).
        plot_line (bool): Whether to plot the line on the image. Default is True.
    
    Returns:
        numpy.ndarray: Pixel values along the profile line.
    """
    with rasterio.open(tif_path) as src:
        band = src.read(1)  # Read the first (or only) band
        transform = src.transform  # Get geotransform
        crs = src.crs  # Get coordinate reference system

    # Convert georeferenced coordinates to pixel coordinates
    start_point_pixel = ~transform * start_point_geo  # (col, row)
    end_point_pixel = ~transform * end_point_geo  # (col, row)
    """
    # Round to nearest integer for pixel indices
    #Rounding to the nearest integer is a critical step when converting 
    georeferenced coordinates to pixel indices. It ensures that:

    # The indices are valid integers.
    
    # The correct pixel is selected.
    
    # No IndexError is raised.
    """
    # Round to nearest integer for pixel indices
    start_point_pixel = (int(round(start_point_pixel[1])), int(round(start_point_pixel[0])))  # (row, col)
    end_point_pixel = (int(round(end_point_pixel[1])), int(round(end_point_pixel[0])))  # (row, col)

    # Get line indices
    rr, cc = line(start_point_pixel[0], start_point_pixel[1], end_point_pixel[0], end_point_pixel[1])

    # Extract pixel values along the line
    profile_values = band[rr, cc]
    return profile_values

# Function to normalize the image
def normalize(array):
    """
    Normalize an array to the range [0, 1].
    
    Parameters:
        array (numpy.ndarray): Input 2D array.
    
    Returns:
        numpy.ndarray: Normalized array.
    """
    array_min, array_max = array.min(), array.max()
    return (array - array_min) / (array_max - array_min)

# Function to extract profile line values from a raster
def extract_normlized_line_profile(tif_path, start_point_geo, end_point_geo):
    with rasterio.open(tif_path) as src:
        band = src.read(1)  # Read the first (or only) band
        band_norm = 1- normalize(band)
        transform = src.transform  # Get geotransform
        crs = src.crs  # Get coordinate reference system
    # Convert georeferenced coordinates to pixel coordinates
    start_point_pixel = ~transform * start_point_geo  # (col, row)
    end_point_pixel = ~transform * end_point_geo  # (col, row)

    # Round to nearest integer for pixel indices
    start_point_pixel = (int(round(start_point_pixel[1])), int(round(start_point_pixel[0])))  # (row, col)
    end_point_pixel = (int(round(end_point_pixel[1])), int(round(end_point_pixel[0])))  # (row, col)

    # Get line indices
    rr, cc = line(start_point_pixel[0], start_point_pixel[1], end_point_pixel[0], end_point_pixel[1])

    # Extract pixel values along the line
    profile_values = band_norm[rr, cc]
    return profile_values


def smooth_data(data, window_size=101, polyorder=2): 
    return savgol_filter(data, window_size, polyorder)


def process_tif_paths(tif_path, start_point, end_point):
    """
    Processes a list of TIF file paths to extract, invert, smooth,
    and return the line profile data.

    Args:
        tif_paths (list): List of file paths to TIF files.
        start_point (tuple): Starting point for line profile extraction.
        end_point (tuple): Ending point for line profile extraction.

    Returns:
        list: A list of smoothed and inverted line profile values.
    """
     # Extract line profile data
    values = extract_normlized_line_profile(tif_path, start_point, end_point)
    inverted_values = values  # Reverse convexity
    smoothed_values = smooth_data(inverted_values)  # Smooth the data
    return smoothed_values




#### Wrapped Phase ifg Images 


# # Read the images
tif_paths = [
    "Phase_ifg_HH_18Jul2024_09Aug2024_27N.tif",
    "Phase_ifg_HH_31Aug2024_03Oct2024_27N.tif",
    "Phase_ifg_HH_31Aug2024_05Nov2024_27N.tif"
]

titles = [
     "Phase_ifg_18Jul2024_09Aug2024",
     "Phase_ifg_31Aug2024_03Oct2024",
     "Phase_ifg_31Aug2024_05Nov2024"
]


# Read the images
images = [read_image(path) for path in tif_paths]

# Create subplots
fig, axes = plt.subplots(2, 2, figsize=(18, 18))  # Adjust figsize as needed
axes = axes.flatten()

# Plot each image with georeferencing
for i, (ax, (image, transform, crs, bounds)) in enumerate(zip(axes, images)):
    # Plot the image with georeferencing
    show(image, transform=transform, ax=ax, cmap="Spectral")
    ax.set_title(titles[i])

    # Set axis labels based on CRS
    if crs.is_geographic:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    else:
        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")

    # Add gridlines
    ax.grid(color='red', linestyle='--', linewidth=0.5)

# # Add a global colorbar for all images
cbar_ax = fig.add_axes([0.97, 0.15, 0.02, 0.7])  # Position for the second colorbar
global_cbar = fig.colorbar(plt.cm.ScalarMappable(cmap="Spectral", norm=plt.Normalize(vmin=-np.pi, vmax=np.pi)), cax=cbar_ax, orientation='vertical')
# Define the ticks and tick labels
ticks = [-np.pi, 0, np.pi]  # Only three ticks: -π, 0, π
tick_labels = [r'$-\pi$', r'$0$', r'$\pi$']  # Corresponding labels

# Set the ticks and tick labels for the colorbar
global_cbar.set_ticks(ticks)
global_cbar.set_ticklabels(tick_labels)
global_cbar.set_label("Line of Sight Phase (radians)")

image9 = Image.open("phase+fault.png")

plt.subplot(2, 2, 4)
plt.imshow(image9)  # Keep original colors for the maps
plt.title("Phase_ifg_HH_31Aug2024_03Oct2024 with faults")
plt.xlabel("Column Index")
plt.ylabel("Row Index")
plt.grid(color='red', linestyle='--', linewidth=0.5)

#Remove the last empty subplot
#fig.delaxes(axes[-1])

# Adjust layout
plt.tight_layout(rect=[0, 0, 0.9, 0.95])

# Add a main title
fig.suptitle("Wrapped Phase ifg Images Track 102 ASC (18Jul_05Nov2024)", fontsize=16, fontweight='bold')

# Save the figure
#fig.savefig("Wrapped Phase ifg Images Track 102 ASC_18Jul_05Nov2024.png", dpi=300, bbox_inches="tight")

plt.show()




#### Normalized Unwrapped Phase ifg Images with profile line 


# Read the images
tif_paths = [
    "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024_27N.tif",
    "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024_27N.tif",
    "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024_27N.tif"
]
titles = [
    "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024",
    "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024",
    "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024" 
]

# Read the images
images = [read_image(path) for path in tif_paths]


# Define start and end points in georeferenced coordinates (easting, northing)
start_point_geo = (424500, 7086500)  # Example: (easting, northing)
end_point_geo = (429000, 7079800)  # Example: (easting, northing)

# Extract row and column coordinates
rows = [start_point_geo[0], end_point_geo[0]]
cols = [start_point_geo[1], end_point_geo[1]]


print(f"Start Point (Easting, Northing): {start_point_geo}")
print(f"End Point (Easting, Northing): {end_point_geo}")

# Create subplots
fig, axes = plt.subplots(3, 2, figsize=(18, 18))  # Adjust figsize as needed
axes = axes.flatten()

# Plot each image with georeferencing
for i, (ax, (image, transform, crs, bounds)) in enumerate(zip(axes, images)):
    # Plot the image with georeferencing
    show(image, transform=transform, ax=ax, cmap="Spectral")
    ax.set_title(titles[i])
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    # # Set axis labels based on CRS
    # if crs.is_geographic:
    #     ax.set_xlabel("Longitude")
    #     ax.set_ylabel("Latitude")
    # else:
    #     ax.set_xlabel("Easting (m)")
    #     ax.set_ylabel("Northing (m)")

    # Add gridlines
    ax.grid(color='red', linestyle='--', linewidth=0.5)

    # Plot the line between start and end points
    ax.plot([start_point_geo[0], end_point_geo[0]],[start_point_geo[1], end_point_geo[1]], 'r-', linewidth=3, label="Line")
    # Add markers at start and end points
    ax.plot(start_point_geo[0], start_point_geo[1],'b*', markersize=8, label="Start") # Blue marker
    ax.plot(end_point_geo[0], end_point_geo[1],'g*', markersize=8, label="End") # Green marker
    ax.legend(loc='lower right')

# Add a global colorbar for all images
cbar_ax1 = fig.add_axes([0.90, 0.15, 0.02, 0.7])  # Position for the first colorbar
global_cbar1 = fig.colorbar(plt.cm.ScalarMappable(cmap="Spectral", norm=plt.Normalize(vmin=-np.pi, vmax=np.pi)), cax=cbar_ax1, orientation='vertical')
# Define the ticks and tick labels
ticks = [-np.pi, 0, np.pi]  # Only three ticks: -π, 0, π
tick_labels = [r'$-\pi$', r'$0$', r'$\pi$']  # Corresponding labels
# Set the ticks and tick labels for the colorbar
global_cbar1.set_ticks(ticks)
global_cbar1.set_ticklabels(tick_labels)
global_cbar1.set_label("Line of Sight Phase (radians)")

# # Add a second colorbar for normalized data (0 to 1)
cbar_ax2 = fig.add_axes([0.97, 0.15, 0.02, 0.7])  # Position for the second colorbar
global_cbar2 = fig.colorbar(plt.cm.ScalarMappable(cmap="Spectral", norm=plt.Normalize(0, 1)), cax=cbar_ax2, orientation='vertical')
global_cbar2.set_label("Normalized Data (0 to 1)")


#Remove the last empty subplot
#fig.delaxes(axes[-1])

# Add a main title
fig.suptitle("Normalized Unwrapped Phase ifg Images tarck 102 ASC (18Jul_05Nov2024)", fontsize=16, fontweight='bold')

image3 = Image.open("unw+fault.png")

plt.subplot(3, 2, 4)
plt.imshow(image3)  # Keep original colors for the maps
plt.title("Normalized_Unw_Phase_Ifg_31Aug_\n3Oct2024_with_Coh_Mask_and_Faults")
plt.xlabel("Column Index")
plt.ylabel("Row Index")
plt.grid(color='red', linestyle='--', linewidth=0.5)
# Adjust layout
plt.tight_layout(rect=[0, 0, 0.9, 0.95])


tif_path_1= "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024_27N.tif"
tif_path_2 = "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024_27N.tif"
tif_path_3 = "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024_27N.tif"

# Extract profile lines from the normalized images
line_values_1 = extract_normlized_line_profile(tif_path_1, start_point_geo, end_point_geo)
line_values_2 = extract_normlized_line_profile(tif_path_2, start_point_geo, end_point_geo)
line_values_3 = extract_normlized_line_profile(tif_path_3, start_point_geo, end_point_geo)

# Plot the profile lines
#plt.figure(figsize=(18, 6))
plt.subplot(3, 2,(5,6))
plt.plot(range(len(line_values_1)), line_values_1, color='cyan', label= "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024")
plt.plot(range(len(line_values_2)), line_values_2, color='orange', label= "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024")
plt.plot(range(len(line_values_3)), line_values_3, color='m', label= "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024")
plt.xlabel('Path in Meters')
plt.ylabel('Normalized Value')
plt.title('Profile Plot for Unw Phase ifg track 102 ASC (18Jul_05Nov2024)', fontsize=16, fontweight='bold')
plt.grid(True)
plt.legend()

# Add the legend with title
legend = plt.legend(loc='lower center', title=f"start_point_geo={start_point_geo}, end_point_geo={end_point_geo}")
#legend._legend_box.align = "left"  # Align the legend title to the left for better readability


# Save the figure
#fig.savefig("Normalized_Unwrapped_Phase_Images_Track_102_ASC(31Aug_03Oct2024)_map.png", dpi=300, bbox_inches="tight")

plt.show()




####Coherence map with profile line

# Read the images
tif_paths = [
    "coh_HH_18Jul2024_09Aug2024_27N.tif",
    "coh_HH_31Aug2024_03Oct2024_27N.tif",
    "coh_HH_31Aug2024_05Nov2024_27N.tif"
]
titles = [
    "Coherence_ifg_18Jul2024_09Aug2024",
    "Coherence_ifg_31Aug2024_03Oct2024",
    "Coherence_ifg_31Aug2024_05Nov2024" 
]

# Read the images
images = [read_image(path) for path in tif_paths]

# Define start and end points in georeferenced coordinates (easting, northing)
start_point_geo = (424500, 7086500)  # Example: (easting, northing)
end_point_geo = (429000, 7079800)  # Example: (easting, northing)

# Extract row and column coordinates
rows = [start_point_geo[0], end_point_geo[0]]
cols = [start_point_geo[1], end_point_geo[1]]


print(f"Start Point (Easting, Northing): {start_point_geo}")
print(f"End Point (Easting, Northing): {end_point_geo}")

# Create subplots
fig, axes = plt.subplots(3, 3, figsize=(20, 20))  # Adjust figsize as needed
axes = axes.flatten()

# Plot each image with georeferencing
for i, (ax, (image, transform, crs, bounds)) in enumerate(zip(axes, images)):
    # Plot the image with georeferencing
    show(image, transform=transform, ax=ax, cmap="gray")
    ax.set_title(titles[i])
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    # # Set axis labels based on CRS
    # if crs.is_geographic:
    #     ax.set_xlabel("Longitude")
    #     ax.set_ylabel("Latitude")
    # else:
    #     ax.set_xlabel("Easting (m)")
    #     ax.set_ylabel("Northing (m)")

    # Add gridlines
    ax.grid(color='red', linestyle='--', linewidth=0.5)

    # Plot the line between start and end points
    ax.plot([start_point_geo[0], end_point_geo[0]],[start_point_geo[1], end_point_geo[1]], 'r-', linewidth=3, label="Line")
    # Add markers at start and end points
    ax.plot(start_point_geo[0], start_point_geo[1],'b*', markersize=8, label="Start") # Blue marker
    ax.plot(end_point_geo[0], end_point_geo[1],'g*', markersize=8, label="End") # Green marker
    ax.legend(loc='lower right')

# Add a global colorbar for all images
cbar_ax1 = fig.add_axes([0.97, 0.15, 0.02, 0.7])  # Position for the second colorbar
global_cbar1 = fig.colorbar(plt.cm.ScalarMappable(cmap="gray", norm=plt.Normalize(0, 1)), cax=cbar_ax1, orientation='vertical')
global_cbar1.set_label("Coherence Value (0 to 1)")

#Remove the last empty subplot
#fig.delaxes(axes[-1])

# Add a main title
fig.suptitle("Coherence ifg images tarck 102 ASC (18Jul_05Nov2024)", fontsize=16, fontweight='bold')


tif_path_1= "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024_27N.tif"
tif_path_2 = "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024_27N.tif"
tif_path_3 = "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024_27N.tif"

# Extract profile lines from the normalized images
line_values_1 = extract_normlized_line_profile(tif_path_1, start_point_geo, end_point_geo)
line_values_2 = extract_normlized_line_profile(tif_path_2, start_point_geo, end_point_geo)
line_values_3 = extract_normlized_line_profile(tif_path_3, start_point_geo, end_point_geo)

# Plot the profile lines
#plt.figure(figsize=(18, 6))
plt.subplot(3, 3,(4,6))
plt.plot(range(len(line_values_1)), line_values_1, color='green', label= "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024")
plt.plot(range(len(line_values_2)), line_values_2, color='orange', label= "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024")
plt.plot(range(len(line_values_3)), line_values_3, color='m', label= "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024")
plt.xlabel('Path in Meters')
plt.ylabel('Normalized Value')
plt.title('Profile Plot for Unw Phase ifg track 102 ASC (18Jul_05Nov2024)', fontsize=16, fontweight='bold')
plt.grid(True)
plt.legend()

tif_path_4 = "Normalized_coh_HH_18Jul2024_09Aug2024.tif"
tif_path_5 = "Normalized_coh_HH_31Aug2024_03Oct2024.tif"
tif_path_6 = "Normalized_coh_HH_31Aug2024_05Nov2024.tif"

# Extract profile lines from the normalized images
line_values_4 = extract_normlized_line_profile(tif_path_4, start_point_geo, end_point_geo)
line_values_5 = extract_normlized_line_profile(tif_path_5, start_point_geo, end_point_geo)
line_values_6 = extract_normlized_line_profile(tif_path_6, start_point_geo, end_point_geo)

plt.subplot(3, 3,(7,9))
plt.plot(range(len(line_values_4)), line_values_4, color='green', label= "Coherence_ifg_18Jul2024_09Aug2024")
plt.plot(range(len(line_values_5)), line_values_5, color='orange', label= "Coherence_ifg_31Aug2024_03Oct2024")
plt.plot(range(len(line_values_6)), line_values_6, color='m', label= "Coherence_ifg_31Aug2024_05Nov2024")
plt.axhline(y=0.5, color='black', linestyle='--', linewidth=3)
#plt.text(x=10, y=0.52, s='Threshold = 0.5', ha='center')
# Add text outside the plot area (axes coordinates go from 0 to 1)
plt.text(
    1, 0.5,                      # X, Y in axes coordinates (X > 1 = outside to the right)
    'Threshold = 0.5',             # Text content
    transform=plt.gca().transAxes, # Use axes coordinates
    color='white',                 # Text color
    fontsize=12,
    ha='left', va='center',        # Horizontal and vertical alignment
    bbox=dict(edgecolor='black', boxstyle='round,pad=0.3')
)
plt.xlabel('Path in Meters')
plt.ylabel('Normalized Value')
plt.title('Profile Plot for coherence ifg track 102 ASC (18Jul_05Nov2024)', fontsize=16, fontweight='bold')
plt.grid(True)
plt.legend()

# Add the legend with title
# legend = plt.legend(loc='lower center',fontsize='small', title_fontsize='medium',
#     frameon=True ,title=f"start_point_geo={start_point_geo}, end_point_geo={end_point_geo}")
# #legend._legend_box.align = "left"  # Align the legend title to the left for better readability

plt.legend(
    loc='upper center',
    title=f"start_point_geo={start_point_geo}, end_point_geo={end_point_geo}",
    bbox_to_anchor=(0.5, -0.15),  # X center, Y below the figure
    ncol=3                       # Spread legend into 3 columns
)

plt.subplots_adjust(top=0.95)  # Default is typically around 0.9

# Save the figure
#fig.savefig("Coherence with Normalized_Unwrapped_Phase_Images_Track_102_ASC(31Aug_03Oct2024)_map.png", dpi=300, bbox_inches="tight")

plt.show()





####Normalized Unwrappied Phase ifg with smoothed profile line


# Read the images
tif_paths = [
    "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024_27N.tif",
    "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024_27N.tif",
    "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024_27N.tif"
]
titles = [
    "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024",
    "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024",
    "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024" 
]

# Read the images
images = [read_image(path) for path in tif_paths]

# Define start and end points
#start_point = (250, 100)  # (row, col)
#end_point = (800, 300)  # (row, col)

# Define start and end points in georeferenced coordinates (easting, northing)
start_point_geo = (424500, 7086500)  # Example: (easting, northing)
end_point_geo = (429000, 7079800)  # Example: (easting, northing)

# Extract row and column coordinates
rows = [start_point_geo[0], end_point_geo[0]]
cols = [start_point_geo[1], end_point_geo[1]]


print(f"Start Point (Easting, Northing): {start_point_geo}")
print(f"End Point (Easting, Northing): {end_point_geo}")

# Create subplots
fig, axes = plt.subplots(3, 2, figsize=(18, 18))  # Adjust figsize as needed
axes = axes.flatten()

# Plot each image with georeferencing
for i, (ax, (image, transform, crs, bounds)) in enumerate(zip(axes, images)):
    # Plot the image with georeferencing
    show(image, transform=transform, ax=ax, cmap="Spectral")
    ax.set_title(titles[i])
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    # # Set axis labels based on CRS
    # if crs.is_geographic:
    #     ax.set_xlabel("Longitude")
    #     ax.set_ylabel("Latitude")
    # else:
    #     ax.set_xlabel("Easting (m)")
    #     ax.set_ylabel("Northing (m)")

    # Add gridlines
    ax.grid(color='red', linestyle='--', linewidth=0.5)

    # Plot the line between start and end points
    ax.plot([start_point_geo[0], end_point_geo[0]],[start_point_geo[1], end_point_geo[1]], 'r-', linewidth=3, label="Line")
    # Add markers at start and end points
    ax.plot(start_point_geo[0], start_point_geo[1],'b*', markersize=8, label="Start") # Blue marker
    ax.plot(end_point_geo[0], end_point_geo[1],'g*', markersize=8, label="End") # Green marker
    ax.legend(loc='lower right')

# Add a global colorbar for all images
cbar_ax1 = fig.add_axes([0.90, 0.15, 0.02, 0.7])  # Position for the first colorbar
global_cbar1 = fig.colorbar(plt.cm.ScalarMappable(cmap="Spectral", norm=plt.Normalize(vmin=-np.pi, vmax=np.pi)), cax=cbar_ax1, orientation='vertical')
# Define the ticks and tick labels
ticks = [-np.pi, 0, np.pi]  # Only three ticks: -π, 0, π
tick_labels = [r'$-\pi$', r'$0$', r'$\pi$']  # Corresponding labels
# Set the ticks and tick labels for the colorbar
global_cbar1.set_ticks(ticks)
global_cbar1.set_ticklabels(tick_labels)
global_cbar1.set_label("Line of Sight Phase (radians)")

# # Add a second colorbar for normalized data (0 to 1)
cbar_ax2 = fig.add_axes([0.97, 0.15, 0.02, 0.7])  # Position for the second colorbar
global_cbar2 = fig.colorbar(plt.cm.ScalarMappable(cmap="Spectral", norm=plt.Normalize(0, 1)), cax=cbar_ax2, orientation='vertical')
global_cbar2.set_label("Normalized Data (0 to 1)")


#Remove the last empty subplot
#fig.delaxes(axes[-1])

# Add a main title
fig.suptitle("Normalized Unwrapped Phase ifg Images tarck 102 ASC (18Jul_05Nov2024)", fontsize=16, fontweight='bold')

image3 = Image.open("unw+fault.png")

plt.subplot(3, 2, 4)
plt.imshow(image3)  # Keep original colors for the maps
plt.title("Normalized_Unw_Phase_Ifg_31Aug_\n3Oct2024_with_Coh_Mask_and_Faults")
plt.xlabel("Column Index")
plt.ylabel("Row Index")
plt.grid(color='red', linestyle='--', linewidth=0.5)
# Adjust layout
plt.tight_layout(rect=[0, 0, 0.9, 0.95])


tif_path_1= "Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024_27N.tif"
tif_path_2 = "Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024_27N.tif"
tif_path_3 = "Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024_27N.tif"

# Extract profile lines from the normalized images
line_values_1 = process_tif_paths(tif_path_1, start_point_geo, end_point_geo)
line_values_2 = process_tif_paths(tif_path_2, start_point_geo, end_point_geo)
line_values_3 = process_tif_paths(tif_path_3, start_point_geo, end_point_geo)


# Plot the profile lines
#plt.figure(figsize=(18, 6))
plt.subplot(3, 2,(5,6))
plt.plot(range(len(line_values_1)), line_values_1, color='cyan', label= "Smoothed_Normalized_Unw_Phase_ifg_18Jul2024_09Aug2024")
plt.plot(range(len(line_values_2)), line_values_2, color='orange', label= "Smoothed_Normalized_Unw_Phase_ifg_31Aug2024_03Oct2024")
plt.plot(range(len(line_values_3)), line_values_3, color='m', label= "Smoothed_Normalized_Unw_Phase_ifg_31Aug2024_05Nov2024")
plt.xlabel('Path in Meters')
plt.ylabel('Normalized and Smoothed Value')
plt.title('Smoothed Profile Plot for Normalized Unw Phase ifg Track 102 ASC (18Jul_05Nov2024)')
plt.grid(True)
plt.legend()

# Add the legend with title
legend = plt.legend(loc='lower center', title=f"start_point_geo={start_point_geo}, end_point_geo={end_point_geo}")
#legend._legend_box.align = "left"  # Align the legend title to the left for better readability

plt.subplots_adjust(top=0.93)  # Default is typically around 0.9

# Save the figure
#fig.savefig("Smoothed Profile Plot Normalized_Unw_Phase_Images_Track_102_ASC(31Aug_03Oct2024)_map2.png", dpi=300, bbox_inches="tight")

plt.show()
