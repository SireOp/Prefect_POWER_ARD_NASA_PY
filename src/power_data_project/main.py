# src/power_data_project/main.py
"""
Entry point for the NASA POWER ARD data workflow.
Connects to the dataset, slices by region/time, and saves outputs.
"""

from power_data_project.connection import open_power_dataset, DEFAULT_URL
from power_data_project.data_download import slice_and_save

# -----------------------------------------------------------------------------
# User-configurable parameters
# -----------------------------------------------------------------------------
URL = DEFAULT_URL  # can be replaced with another POWER Zarr dataset

# Example bounding box & time window
LAT_SLICE = (35.0, 45.0)     # latitude range (south, north)
LON_SLICE = (-85.0, -75.0)   # longitude range (west, east)
TIME_RANGE = ("2019-12-31", "2020-12-31")

# Target variable
VARIABLE = "ALLSKY_SFC_LW_DWN"  # longwave downward radiation (W/m²)

# Output directory & file base name
OUTPUT_DIR = "data/output"
BASENAME = "power_region_example"

# -----------------------------------------------------------------------------
# Workflow
# -----------------------------------------------------------------------------
def main():
    print(" Connecting to NASA POWER dataset...")
    ds = open_power_dataset(URL)

    print(f" Dataset opened successfully with {len(ds.data_vars)} variables.")
    print(f"   Variables available: {list(ds.data_vars)[:5]}...")

    print(f"\n Slicing variable '{VARIABLE}' for lat={LAT_SLICE}, lon={LON_SLICE}, time={TIME_RANGE}")
    da, paths = slice_and_save(
        ds,
        var=VARIABLE,
        lat=LAT_SLICE,
        lon=LON_SLICE,
        time=TIME_RANGE,
        out_dir=OUTPUT_DIR,
        basename=BASENAME,
        load=False,
    )

    print("\n Processing complete!")
    print(f"   NetCDF saved to: {paths[0]}")
    print(f"   CSV saved to:    {paths[1]}")
    print(f"   DataArray shape: {da.shape}")
    print("-------------------------------------------------------------")


if __name__ == "__main__":
    main()