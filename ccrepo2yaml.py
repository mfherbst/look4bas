#!/usr/bin/env python3
import ccrepo
import argparse
import yaml
import os
from datetime import datetime


def ccrepo2yaml():
    """ Download ccrepo basis data and return yaml string of it,
    which is enhanced with metadata about the date and version
    """
    d = {
        "list": ccrepo.download_basisset_list(),
        "meta": {
            # UTC timestamp
            "timestamp": datetime.utcnow().isoformat(),
            # yaml format version:
            "version": "0.0.0",
        }
    }
    return yaml.safe_dump(d)


def main():
    parser = argparse.ArgumentParser(
        description="Download and convert the ccrepo basis set data to a yaml file")
    parser.add_argument("output", type=str, metavar="out.yaml",
                        help="Location to store the yaml file")
    args = parser.parse_args()

    _, ext = os.path.splitext(args.output)
    if ext not in ['.yml', '.yaml']:
        args.output += '.yaml'

    data = ccrepo2yaml()
    open(args.output, "w").write(data)


if __name__ == "__main__":
    main()
