#!/usr/bin/env python3

from . import gaussian94

""" Dictionary of the basis set formats supported by this script,
    mapped to the default file extension used.
"""
formats = {
    "Gaussian94": "g94",
}


def normalise_name(name):
    """Normalise a basis set name to yield a valid filename"""
    return "".join(["I" if c == "/" else c for c in name.lower()])


def download_basissets(l, fmt, destination="."):
    """Download all basis sets in the list using the supplied format
    (in optimally contracted form).
    """
    print("Downloading " + str(len(l)) + " basis sets in " + fmt + " format:")
    for b in l:
        path = destination + "/" + normalise_name(b["name"]) + "." + emsl.formats[fmt]

        if os.path.exists(path):
            print("   Warn: Skipping " + path + " since file already exists")
            continue

        print("   ", b["name"], " to ", path)
        data = emsl.download_basisset_raw(b, fmt)
        open(path, "w").write(data)


