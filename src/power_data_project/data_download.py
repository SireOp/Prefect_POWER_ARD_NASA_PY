# src/power_data_project/data_download.py
"""
Slice & export helpers for NASA POWER xarray datasets.
- Works with point or regional slices
- Optional time window
- Exports to NetCDF and CSV
"""

from __future__ import annotations
from typing import Optional, Tuple, Union
import os
import pandas as pd
import xarray as xr

__all__ = ["slice_dataset", "save_outputs", "slice_and_save"]

Lat = Union[float, Tuple[float, float]]
Lon = Union[float, Tuple[float, float]]
TimeRange = Optional[Tuple[str, str]]  # e.g. ("2019-01-01","2020-12-31")


def slice_dataset(
    ds: xr.Dataset,
    var: str = "ALLSKY_SFC_LW_DWN",
    *,
    lat: Lat = (35.0, 45.0),
    lon: Lon = (-85.0, -75.0),
    time: TimeRange = None,
    nearest: bool = True,
) -> xr.DataArray:
    """
    Return a DataArray subset of `var` by lat/lon (point or box) and optional time range.

    Args:
        ds: xarray.Dataset from connection.open_power_dataset(...)
        var: Variable name in the dataset (e.g., "ALLSKY_SFC_LW_DWN")
        lat, lon:
            - float => select nearest point (default method='nearest' if nearest=True)
            - (min, max) tuple => select a box using slice(min, max)
        time: ("YYYY-MM-DD","YYYY-MM-DD") to slice inclusive range; None keeps all
        nearest: Use nearest neighbor when lat/lon are floats

    Returns:
        xr.DataArray subset (lazy unless you call .load()).
    """
    if var not in ds:
        raise KeyError(f"Variable '{var}' not found. Available: {list(ds.data_vars)}")

    da = ds[var]

    # Spatial
    if isinstance(lat, tuple) and isinstance(lon, tuple):
        da = da.sel(lat=slice(*lat), lon=slice(*lon))
    else:
        sel = {"lat": float(lat) if not isinstance(lat, tuple) else lat,
               "lon": float(lon) if not isinstance(lon, tuple) else lon}
        da = da.sel(**sel, method="nearest" if nearest else None)

    # Temporal
    if time:
        start, end = time
        da = da.sel(time=slice(start, end))

    return da


def save_outputs(
    da: xr.DataArray,
    out_dir: str = "data/output",
    basename: str = "region",
) -> Tuple[str, str]:
    """
    Save a DataArray to NetCDF and CSV. Returns (nc_path, csv_path).
    """
    os.makedirs(out_dir, exist_ok=True)

    # Ensure it has a name for NetCDF
    name = da.name or "value"
    ds_out = da.to_dataset(name=name)

    nc_path = os.path.join(out_dir, f"{basename}.nc")
    csv_path = os.path.join(out_dir, f"{basename}.csv")

    ds_out.to_netcdf(nc_path)
    (da.to_dataframe().reset_index()).to_csv(csv_path, index=False)

    print(f"Saved NetCDF: {nc_path}")
    print(f"Saved CSV   : {csv_path}")
    return nc_path, csv_path


def slice_and_save(
    ds: xr.Dataset,
    *,
    var: str = "ALLSKY_SFC_LW_DWN",
    lat: Lat = (35.0, 45.0),
    lon: Lon = (-85.0, -75.0),
    time: TimeRange = None,
    out_dir: str = "data/output",
    basename: str = "region",
    load: bool = False,
) -> Tuple[xr.DataArray, Tuple[str, str]]:
    """
    Convenience: slice first, optionally .load(), then save to disk.

    Returns:
        (subset_dataarray, (nc_path, csv_path))
    """
    da = slice_dataset(ds, var=var, lat=lat, lon=lon, time=time)
    if load:
        da = da.load()  # materialize if you plan heavy downstream ops
    paths = save_outputs(da, out_dir=out_dir, basename=basename)
    return da, paths


if __name__ == "__main__":
    # Example manual run (expects connection.open_power_dataset available)
    from power_data_project.connection import open_power_dataset, DEFAULT_URL

    ds = open_power_dataset(DEFAULT_URL)
    da, (nc, csv) = slice_and_save(
        ds,
        var="ALLSKY_SFC_LW_DWN",
        lat=(35, 45),
        lon=(-85, -75),
        time=("2019-12-31", "2020-12-31"),
        basename="example_region",
    )
    print(da)