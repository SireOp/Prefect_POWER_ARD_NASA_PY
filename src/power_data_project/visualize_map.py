# src/power_data_project/visualize_map.py
import argparse
import os
from typing import Optional

import matplotlib.pyplot as plt
import xarray as xr

# cartopy is great, but optional
try:
    import cartopy.crs as ccrs
    _HAS_CARTOPY = True
except Exception:
    _HAS_CARTOPY = False


def _load_dataset(path: str, var_name: str) -> xr.DataArray:
    """
    Load data from NetCDF or CSV into a DataArray with dims (time?, lat, lon).
    CSV must have columns: time, lat, lon, <var_name>
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".nc", ".nc4", ".cdf"):
        ds = xr.open_dataset(path)
        if var_name not in ds:
            # helpful hint if the user guessed the wrong case/name
            available = ", ".join(ds.data_vars)
            raise KeyError(f"Variable '{var_name}' not in dataset. Available: {available}")
        da = ds[var_name]
        # Ensure lat/lon are named consistently
        rename_map = {}
        for cand, std in (("latitude", "lat"), ("Longitude", "lon"), ("Latitude", "lat"),
                          ("LONGITUDE", "lon"), ("LATITUDE", "lat")):
            if cand in da.coords and std not in da.coords:
                rename_map[cand] = std
        if rename_map:
            da = da.rename(rename_map)
        return da

    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(path)
        # Find the variable column (case-insensitive match if needed)
        cols_lower = {c.lower(): c for c in df.columns}
        want = var_name.lower()
        if want not in cols_lower:
            # show best guess list
            guesses = [c for c in df.columns if c.lower() not in {"time", "lat", "lon"}]
            raise KeyError(
                f"Column '{var_name}' not found in CSV. "
                f"Found value columns: {guesses}"
            )
        vcol = cols_lower[want]

        # Basic validation
        for req in ("time", "lat", "lon"):
            if req not in cols_lower:
                raise KeyError(f"CSV is missing required column '{req}'.")

        # Build a 3D DataArray via xarray
        df["time"] = pd.to_datetime(df[cols_lower["time"]])
        df = df.rename(columns={
            cols_lower["lat"]: "lat",
            cols_lower["lon"]: "lon",
            vcol: var_name
        })
        ds = (
            df.set_index(["time", "lat", "lon"])
              .to_xarray()
        )
        da = ds[var_name]
        return da

    else:
        raise ValueError(f"Unsupported file type '{ext}'. Use .nc or .csv")


def plot_radiation_map(
    data_path: str,
    var_name: str,
    mean_over_time: bool = True,
    save_path: Optional[str] = None,
) -> None:
    """
    Plot a lat/lon heatmap for var_name from NetCDF or CSV.

    - If mean_over_time is True and 'time' exists, averages over time.
    - If cartopy is available, draws on a geo projection; otherwise uses plain axes.
    """
    da = _load_dataset(data_path, var_name)

    # Average over time if requested and available
    if mean_over_time and "time" in da.dims:
        da = da.mean("time")

    # Squeeze singletons to be safe
    da = da.squeeze()

    title = f"{var_name} — Mean Surface Radiation" if "time" not in da.dims or mean_over_time \
        else f"{var_name} — First timestep"

    if _HAS_CARTOPY:
        fig = plt.figure(figsize=(9, 6))
        ax = plt.axes(projection=ccrs.PlateCarree())
        mesh = da.plot(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap="viridis",
            cbar_kwargs={"label": f"{var_name} (W/m²)"}
        )
        ax.coastlines()
        try:
            gl = ax.gridlines(draw_labels=True, linestyle=":")
            gl.right_labels = False
            gl.top_labels = False
        except Exception:
            pass
        ax.set_title(title)
    else:
        # Fallback: regular axes (requires 2D lat/lon grids or 1D lat/lon coords)
        fig = plt.figure(figsize=(9, 6))
        ax = plt.gca()
        # xarray .plot() handles 2D/1D lat/lon nicely even without cartopy
        mesh = da.plot(
            ax=ax,
            cmap="viridis",
            cbar_kwargs={"label": f"{var_name} (W/m²)"}
        )
        ax.set_title(title + " (no cartopy)")

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Saved figure -> {save_path}")

    plt.show()


def _print_available_vars(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".nc", ".nc4", ".cdf"):
        ds = xr.open_dataset(path)
        print("Available variables:", ", ".join(ds.data_vars))
    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(path, nrows=1)
        value_cols = [c for c in df.columns if c.lower() not in {"time", "lat", "lon"}]
        print("CSV value columns:", ", ".join(value_cols))
    else:
        print("Unknown file type; cannot list variables.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot radiation map from NetCDF or CSV.")
    parser.add_argument(
        "--path",
        required=False,
        default="../data/output/power_long_wave_radiation.nc",
        help="Path to .nc or .csv (relative to src/)."
    )
    parser.add_argument(
        "--var",
        required=False,
        default="ALLSKY_SFC_LW_DWN",
        help="Variable/column name to plot."
    )
    parser.add_argument(
        "--no-mean",
        action="store_true",
        help="Do NOT average over time (plot a single timestep)."
    )
    parser.add_argument(
        "--save",
        default=None,
        help="Optional output image path (e.g., ../data/output/radiation_map.png)."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List variables/columns in the file and exit."
    )
    args = parser.parse_args()

    if args.list:
        _print_available_vars(args.path)
    else:
        plot_radiation_map(
            data_path=args.path,
            var_name=args.var,
            mean_over_time=not args.no-mean,
            save_path=args.save,
        )