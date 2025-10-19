# src/power_data_project/main.py
from power_data_project.connection import open_power_dataset, DEFAULT_URL
from power_data_project.data_download import slice_and_save

# -----------------------------------------------------------------------------
# User-configurable parameters
# -----------------------------------------------------------------------------
URL = DEFAULT_URL  # can be replaced with another POWER Zarr dataset

# Example bounding box & time window
LAT_SLICE = (35.0, 45.0)     # latitude range (south, north)
LON_SLICE = (-85.0, -75.0)   # longitude range (west, east)
TIME_RANGE = ("2024-10-19", "2025-10-19")

# POWER variable names
SHORTWAVE = "ALLSKY_SFC_SW_DWN"  # W/m²
LONGWAVE  = "ALLSKY_SFC_LW_DWN"  # W/m²

OUTPUT_DIR = "data/output"

def main():
    print("Connecting…")
    ds = open_power_dataset(URL)

    jobs = [
        (SHORTWAVE, "power_short_wave_radiation"),
        (LONGWAVE,  "power_long_wave_radiation"),
    ]

    for var, base in jobs:
        print(f"\n Slicing '{var}' …")
        da, (nc_path, csv_path) = slice_and_save(
            ds,
            var=var,
            lat=LAT_SLICE,
            lon=LON_SLICE,
            time=TIME_RANGE,
            out_dir=OUTPUT_DIR,
            basename=base,
            load=False,
        )
        print(f"Saved: {nc_path} and {csv_path} | shape={da.shape}")

if __name__ == "__main__":
    main()