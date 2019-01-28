#!/usr/bin/env python3

from . import gaussian94, orca
import os

""" Dictionary of the basis set formats supported by this script,
    mapped to the default file extension used.
"""
formats = {
    "Gaussian94": "g94",
    "Orca": "orca",
}


def normalise_name(name):
    """Normalise a basis set name to yield a valid filename"""
    return name.lower().replace("/", "I").replace(" ", "_")


def save_basisset(bset, fmts, destination="."):
    """
    Save the provided basis set in the given formats
    to the provided destination directory.
    """
    dump_function = {
        "Gaussian94": gaussian94.dumps,
        "Orca": orca.dumps,
    }

    for fmt in fmts:
        if fmt not in dump_function:
            raise NotImplementedError("Format {} not implemented.".format(fmt))

        data = dump_function[fmt](bset["atoms"])
        path = destination + "/" + normalise_name(bset["name"]) + "." + formats[fmt]
        if os.path.exists(path):
            print("   Warn: Skipping " + path + " since file already exists")
        else:
            print("   Saving to ", path)
            with open(path, "w") as f:
                f.write(data)
