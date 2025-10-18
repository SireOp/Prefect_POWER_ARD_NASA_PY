'''
*Version: 1.0 Published: 2022/05/31* Source: [NASA POWER](https://power.larc.nasa.gov/)
POWER Remotely Connect to a POWER Zarr via Python
This is an overview of the process to remotely connect to a POWER Zarr-formatted Analysis Ready Dataset (ARD) via Python.
''' 
from typing import Optional
import fsspec
import xarray as xr

 

DEFAULT_URL = ("https://nasa-power.s3.amazonaws.com/syn1deg/temporal/power_syn1deg_monthly_temporal_lst.zarr")
__all__ = ["DEFAULT_URL", "open_power_dataset"]

def open_power_dataset(url: Optional[str] = None, *, consolidated: bool = True) -> xr.Dataset:
    """
    Open the NASA POWER monthly Zarr dataset via fsspec.

    Returns an xarray.Dataset (lazy-loaded).
    
    """
    target = url or DEFAULT_URL
    mapper = fsspec.get_mapper(target)

    ds = xr.open_zarr(store=mapper , consolidated=consolidated)
    return ds

if __name__ == "__main__":
    ds = open_power_dataset()
    print(ds)
