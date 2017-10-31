#!/usr/bin/env python3
import look4bas.cache
import os
import yaml
import sys


if len(sys.argv) < 2:
    raise SystemExit("Need output file as first argument.")

output = sys.argv[1]
_, ext = os.path.splitext(output)
if ext not in ['.yml', '.yaml']:
    output += '.yaml'

data = look4bas.cache.get_basisset_list("ccrepo", force_update=True)
with open(output, "w") as f:
    yaml.safe_dump(data, f)
