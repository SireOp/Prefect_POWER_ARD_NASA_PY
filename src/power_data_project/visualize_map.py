# src/power_data_project/visualize_map.py
from __future__ import annotations

import argparse
import os
from typing import Optional

import matplotlib.pyplot as plt
import xarray as xr

# cartopy is great, but optional
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    _HAS_CARTOPY = True
except Exception:
    _HAS_CARTOPY = False


# =========================== loaders & helpers ============================

def _open_netcdf_any(path: str) -> xr.Dataset:
    """
    Open a NetCDF file, trying multiple engines for robustness.
    Returns an xarray.Dataset or raises RuntimeError with collected errors.
    """
    errors = []
    for eng in ("netcdf4", "h5netcdf", "scipy"):
        try:
            return xr.open_dataset(path, engine=eng)
        except Exception as e:
            errors.append(f"{eng}: {type(e).__name__}: {e}")
    raise RuntimeError(
        "Failed to open NetCDF with engines netcdf4/h5netcdf/scipy.\n" +
        "\n".join(errors)
    )


def _load_dataset(path: str, var_name: str) -> xr.DataArray:
    """
    Load data from NetCDF or CSV into a DataArray with dims (time?, lat, lon).
    CSV must have columns: time, lat, lon, <var_name>
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in (".nc", ".nc4", ".cdf"):
        # Absolute path avoids cwd confusion
        path = os.path.abspath(path)
        ds = _open_netcdf_any(path)

        if var_name not in ds:
            available = ", ".join(ds.data_vars)
            raise KeyError(f"Variable '{var_name}' not in dataset. Available: {available}")

        da = ds[var_name]

        # Normalize coord names if needed
        rename_map = {}
        for cand, std in (
            ("latitude", "lat"),
            ("Latitude", "lat"),
            ("LATITUDE", "lat"),
            ("longitude", "lon"),
            ("Longitude", "lon"),
            ("LONGITUDE", "lon"),
        ):
            if cand in da.coords and std not in da.coords:
                rename_map[cand] = std
        if rename_map:
            da = da.rename(rename_map)
        return da

    elif ext == ".csv":
        import pandas as pd  # local import to keep hard dep optional
        path = os.path.abspath(path)
        df = pd.read_csv(path)

        cols_lower = {c.lower(): c for c in df.columns}
        want = var_name.lower()
        if want not in cols_lower:
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

        df["time"] = pd.to_datetime(df[cols_lower["time"]])
        df = df.rename(columns={
            cols_lower["lat"]: "lat",
            cols_lower["lon"]: "lon",
            vcol: var_name,
        })

        ds = df.set_index(["time", "lat", "lon"]).to_xarray()
        return ds[var_name]

    else:
        raise ValueError(f"Unsupported file type '{ext}'. Use .nc or .csv")


def infer_extent(da: xr.DataArray):
    """Return (min_lon, max_lon, min_lat, max_lat) from a DataArray."""
    lats = da["lat"].values
    lons = da["lon"].values
    return float(lons.min()), float(lons.max()), float(lats.min()), float(lats.max())


def add_base_layers(ax, extent=None, with_states: bool = True) -> None:
    """Coastlines, borders, states/provinces, and labeled gridlines."""
    if not _HAS_CARTOPY:
        return
    if extent:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.coastlines(linewidth=0.8)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.6)
    if with_states:
        # Natural Earth admin_1 (state/province) lines
        states = cfeature.NaturalEarthFeature(
            category="cultural",
            name="admin_1_states_provinces_lines",
            scale="50m",
            facecolor="none",
        )
        ax.add_feature(states, edgecolor="gray", linewidth=0.4)

    gl = ax.gridlines(draw_labels=True, linestyle=":", alpha=0.6)
    gl.right_labels = False
    gl.top_labels = False


# ================================ plotting ================================

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

    da = da.squeeze()

    title = (
        f"{var_name} — Mean Surface Radiation"
        if "time" not in da.dims or mean_over_time
        else f"{var_name} — First timestep"
    )

    if _HAS_CARTOPY:
        fig = plt.figure(figsize=(9, 6))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # infer extent from data
        try:
            extent = infer_extent(da)
        except Exception:
            extent = None

        da.plot(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap="viridis",
            cbar_kwargs={"label": f"{var_name} (W/m²)"},
        )

        add_base_layers(ax, extent)
        ax.set_title(title)
    else:
        # Fallback: regular axes (requires 2D lat/lon grids or 1D lat/lon coords)
        fig = plt.figure(figsize=(9, 6))
        ax = plt.gca()
        da.plot(
            ax=ax,
            cmap="viridis",
            cbar_kwargs={"label": f"{var_name} (W/m²)"},
        )
        ax.set_title(title + " (no cartopy)")

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Saved figure -> {save_path}")

    plt.show()


def plot_two_maps(
    lw_path: str,
    lw_var: str,
    sw_path: str,
    sw_var: str,
    mean_over_time: bool = True,
    save_path: Optional[str] = "../data/output/radiation_maps.png",
) -> None:
    """Render LW and SW side-by-side in one figure and save to PNG."""
    da_lw = _load_dataset(lw_path, lw_var)
    da_sw = _load_dataset(sw_path, sw_var)

    if mean_over_time and "time" in da_lw.dims:
        da_lw = da_lw.mean("time")
    if mean_over_time and "time" in da_sw.dims:
        da_sw = da_sw.mean("time")

    if _HAS_CARTOPY:
        fig, axes = plt.subplots(
            ncols=2,
            figsize=(14, 6),
            subplot_kw={"projection": ccrs.PlateCarree()},
        )
        # combined extent for consistent view
        try:
            e1 = infer_extent(da_lw)
            e2 = infer_extent(da_sw)
            extent = (
                min(e1[0], e2[0]), max(e1[1], e2[1]),
                min(e1[2], e2[2]), max(e1[3], e2[3]),
            )
        except Exception:
            extent = None

        da_lw.plot(
            ax=axes[0],
            transform=ccrs.PlateCarree(),
            cmap="viridis",
            cbar_kwargs={"label": f"{lw_var} (W/m²)"},
        )
        add_base_layers(axes[0], extent)
        axes[0].set_title(f"{lw_var} — Mean Surface Radiation")

        da_sw.plot(
            ax=axes[1],
            transform=ccrs.PlateCarree(),
            cmap="viridis",
            cbar_kwargs={"label": f"{sw_var} (W/m²)"},
        )
        add_base_layers(axes[1], extent)
        axes[1].set_title(f"{sw_var} — Mean Surface Radiation")

        plt.tight_layout()
    else:
        fig, axes = plt.subplots(ncols=2, figsize=(14, 6))
        da_lw.plot(ax=axes[0], cmap="viridis", cbar_kwargs={"label": f"{lw_var} (W/m²)"})
        axes[0].set_title(f"{lw_var} — Mean Surface Radiation (no cartopy)")
        da_sw.plot(ax=axes[1], cmap="viridis", cbar_kwargs={"label": f"{sw_var} (W/m²)"})
        axes[1].set_title(f"{sw_var} — Mean Surface Radiation (no cartopy)")
        plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Saved duo map -> {save_path}")

    plt.show()


def _print_available_vars(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".nc", ".nc4", ".cdf"):
        ds = _open_netcdf_any(os.path.abspath(path))
        print("Available variables:", ", ".join(ds.data_vars))
    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(os.path.abspath(path), nrows=1)
        value_cols = [c for c in df.columns if c.lower() not in {"time", "lat", "lon"}]
        print("CSV value columns:", ", ".join(value_cols))
    else:
        print("Unknown file type; cannot list variables.")


# ================================= CLI ===================================

if __name__ == "__main__":
    # Headless-safe backend
    if not os.environ.get("DISPLAY"):
        import matplotlib
        matplotlib.use("Agg")

    parser = argparse.ArgumentParser(description="Plot radiation map(s) from NetCDF or CSV.")

    # single-plot options
    parser.add_argument(
        "--path",
        default="../data/output/power_long_wave_radiation.nc",
        help="Path to .nc or .csv for single plot (LW by default).",
    )
    parser.add_argument(
        "--var",
        default="ALLSKY_SFC_LW_DWN",
        help="Variable/column name to plot for single plot.",
    )
    parser.add_argument(
        "--no-mean",
        action="store_true",
        help="Do NOT average over time.",
    )
    parser.add_argument(
        "--save",
        default="../data/output/auto_radiation_map.png",
        help="Output image path for single plot.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List variables/columns in the given --path and exit.",
    )

    # duo-plot options
    parser.add_argument(
        "--both",
        action="store_true",
        help="Render LW and SW side-by-side.",
    )
    parser.add_argument(
        "--lw",
        default="../data/output/power_long_wave_radiation.nc",
        help="LW dataset path (used with --both).",
    )
    parser.add_argument(
        "--lw-var",
        default="ALLSKY_SFC_LW_DWN",
        help="LW variable name (used with --both).",
    )
    parser.add_argument(
        "--sw",
        default="../data/output/power_short_wave_radiation.nc",
        help="SW dataset path (used with --both).",
    )
    parser.add_argument(
        "--sw-var",
        default="ALLSKY_SFC_SW_DWN",
        help="SW variable name (used with --both).",
    )
    parser.add_argument(
        "--save-both",
        default="../data/output/radiation_maps.png",
        help="Output image path when using --both.",
    )

    args = parser.parse_args()

    if args.list:
        _print_available_vars(args.path)
    elif args.both:
        print(f"\n  LW: {args.lw}  ({args.lw_var})")
        print(f"  SW: {args.sw}  ({args.sw_var})")
        print(f"  Out: {args.save_both}\n")
        plot_two_maps(
            lw_path=args.lw,
            lw_var=args.lw_var,
            sw_path=args.sw,
            sw_var=args.sw_var,
            mean_over_time=not args.no_mean,
            save_path=args.save_both,
        )
        print(f" Duo visualization saved at: {args.save_both}")
    else:
        print(f"\n  Path: {args.path}")
        print(f"  Var : {args.var}")
        print(f"  Out : {args.save}\n")
        plot_radiation_map(
            data_path=args.path,
            var_name=args.var,
            mean_over_time=not args.no_mean,
            save_path=args.save,
        )
        print(f"Visualization saved at: {args.save}")