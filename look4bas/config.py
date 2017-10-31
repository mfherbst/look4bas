#!/usr/bin/env python3
import os
import datetime


cache_folder = os.path.expanduser("~/.local/share/look4bas")
cache_maxage = datetime.timedelta(days=14)
default_download_formats = ["Gaussian94"]
list_formats = {
    "default": ["crop", "noelements", "colour"],
    "extra":   ["crop", "elements", "colour"]
}
