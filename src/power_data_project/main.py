# src/power_data_project/main.py
from power_data_project.connection import open_power_dataset, DEFAULT_URL
from power_data_project.data_download import slice_and_save

URL = DEFAULT_URL
LAT_SLICE = (35.0, 45.0)
LON_SLICE = (-85.0, -75.0)
TIME_RANGE = ("2019-12-31", "2020-12-31")

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