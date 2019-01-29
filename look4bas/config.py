#!/usr/bin/env python3

"""
Static defaults for look4bas. Might be come run-time configurable
at some point
"""

dbfile = "~/.local/share/look4bas/basis_sets.db"
default_download_formats = ["gaussian94"]
format_flags = {
    "default": ["crop", "no-elements", "colour"],
    "extra":   ["crop", "elements", "colour"]
}
source_to_colour = {"ccrepo": "cyan", "EMSL": "yellow"}
