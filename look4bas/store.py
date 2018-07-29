#!/usr/bin/env python3

from . import gaussian94
import os

""" Dictionary of the basis set formats supported by this script,
    mapped to the default file extension used.
"""
formats = {
    "Gaussian94": "g94",
}


def normalise_name(name):
    """Normalise a basis set name to yield a valid filename"""
    return "".join(["I" if c == "/" else c for c in name.lower()])


def save_basisset(bset, fmts, destination="."):
    """
    Save the provided basis set in the given formats
    to the provided destination directory.
    """

    for fmt in fmts:
        if fmt == "Gaussian94":
            data = gaussian94.dumps(bset["atoms"])
        else:
            raise NotImplementedError("Format {} not implemented.".format(fmt))

        path = destination + "/" + normalise_name(bset["name"]) + "." + formats[fmt]
        if os.path.exists(path):
            print("   Warn: Skipping " + path + " since file already exists")
        else:
            print("   ", bset["name"], " to ", path)
            with open(path, "w") as f:
                f.write(data)
