#!/usr/bin/env python3

from . import config, emsl, ccrepo
import datetime
import os
import yaml


def get_basisset_list(source="emsl", force_update=False):
    """Check whether the cached list file is recent enough
    and update it if not"""

    download_fctn = {
        "emsl": emsl.download_basisset_list,
        "ccrepo": ccrepo.download_basisset_list,
    }

    cache = os.path.join(config.cache_folder, source + ".yaml")
    if os.path.exists(cache) and not force_update:
        with open(cache, "r") as f:
            data = yaml.safe_load(f)
            isoformat = "%Y-%m-%dT%H:%M:%S.%f"
            timestamp = datetime.datetime.strptime(data["meta"]["timestamp"], isoformat)

            # Only use the cache if the age of the cached data is
            # less than the value the config wants:
            age = datetime.datetime.utcnow() - timestamp
            if age < config.cache_maxage:
                return data["list"]

            # TODO Still use old list if we have a network error.

    data = {
        "list": download_fctn[source](),
        "meta": {
            # UTC timestamp
            "timestamp": datetime.datetime.utcnow().isoformat(),
            # yaml format version:
            "version": "0.0.0",
        }
    }

    os.makedirs(config.cache_folder, exist_ok=True)
    with open(cache, "w") as f:
        yaml.safe_dump(data, f)
    return data["list"]
