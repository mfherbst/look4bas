#!/usr/bin/env python3

from . import basis_format
import os


def normalise_name(name):
    """Normalise a basis set name to yield a valid filename"""
    return name.lower().replace("/", "I").replace(" ", "_")


def save_basisset(bset, fmts, destination="."):
    """
    Save the provided basis set in the given formats
    to the provided destination directory.
    """
    kwargs = {"name": bset["name"], }
    if "description" in bset:
        kwargs["description"] = bset["description"]

    for fmt in fmts:
        data = basis_format.dumps(fmt, bset["atoms"], **kwargs)
        path = (destination + "/" + normalise_name(bset["name"])
                + "." + basis_format.extension[fmt])
        if os.path.exists(path):
            print("   Warn: Skipping " + path + " since file already exists")
        else:
            print("   Saving to ", path)
            with open(path, "w") as f:
                f.write(data)
