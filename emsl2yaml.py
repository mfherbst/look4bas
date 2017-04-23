#!/usr/bin/env python3
import emsl
import argparse
import json
import yaml
import os

def main():
    parser = argparse.ArgumentParser(
       description="Download and convert the EMSL basis set exchange data to a yaml" \
        "or json file (depending on the file extension).")
    parser.add_argument("output", type=str, metavar="out",
                        help="Location to store the json/yaml file")
    args = parser.parse_args()

    _, ext = os.path.splitext(args.output)
    if ext in [ '.json' ]:
        dumper = json.dumps
    else:
        dumper = yaml.safe_dump

    # Download and dump:
    bases = emsl.download_basisset_list()
    with open(args.output, "w") as f:
        f.write(dumper(bases))

if __name__ == "__main__":
    main()
