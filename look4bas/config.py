#!/usr/bin/env python3

dbfile = "~/.local/share/look4bas/basis_sets.db"
default_download_formats = ["Gaussian94"]
format_flags = {
    "default": ["crop", "no-elements", "colour"],
    "extra":   ["crop", "elements", "colour"]
}
source_to_colour = {"ccrepo":"cyan", "EMSL": "yellow"}
