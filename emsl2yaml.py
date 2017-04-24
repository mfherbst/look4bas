#!/usr/bin/env python3
import emsl
import argparse
import yaml
import os
from datetime import datetime


"""The dateformat used in the emsl2yaml metadata"""
datetime_format="%Y-%m-%d %H:%M:%S.%f"


def emsl2yaml():
  """ Download emsl basis data and return yaml string of it,
  which is enhanced with metadata about the date and version
  """
  d = {
    "list": emsl.download_basisset_list(),
    "meta": {
      # UTC timestamp
      "timestamp": datetime.utcnow().strftime(datetime_format),
      # yaml format version:
      "version": "0.0.0",
    }
  }
  return yaml.safe_dump(d)

def main():
  parser = argparse.ArgumentParser(
    description="Download and convert the EMSL basis set exchange data to a yaml file")
  parser.add_argument("output", type=str, metavar="out.yaml",
                      help="Location to store the yaml file")
  args = parser.parse_args()

  _, ext = os.path.splitext(args.output)
  if not ext in [ '.yml', '.yaml' ]:
    args.output += '.yaml'

  with open(args.output, "w") as f:
    f.write(emsl2yaml())

if __name__ == "__main__":
  main()
