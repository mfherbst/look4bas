#!/usr/bin/env python3
import emsl
import emsl2yaml
import yaml
import sys
import os
import datetime
import re
import argparse
import shutil
from io import StringIO

class config:
  emsl_cache = os.path.expanduser("~/.local/share/look4bas/emsl.yaml")
  cache_maxage = datetime.timedelta(days=3)
  default_download_formats=["Gaussian94"]

def get_basisset_list(force_update=False):
  """Check whether the cached emsl list file is recent enough
  and update it if not"""
  if os.path.exists(config.emsl_cache) and not force_update:
    with open(config.emsl_cache, "r") as f:
      data = yaml.safe_load(f)
      timestamp = datetime.datetime.strptime(data["meta"]["timestamp"],
                                             emsl2yaml.datetime_format)

      # Only use the cache if the age of the cached data is
      # less than the value the config wants:
      age = datetime.datetime.utcnow() - timestamp
      if age < config.cache_maxage:  return data["list"]

      # TODO Still use old list if we have a network error.

  os.makedirs(os.path.dirname(config.emsl_cache), exist_ok=True)
  cache = emsl2yaml.emsl2yaml()
  with open(config.emsl_cache, "w") as f:
    f.write(cache)
  return yaml.safe_load(StringIO(cache))["list"]

__strip_ANSI_escapes = re.compile(r"""
  \x1b     # literal ESC
  \[       # literal [
  [;\d]*   # zero or more digits or semicolons
  [A-Za-z] # a letter
  """, re.VERBOSE).sub
def printlen(s):
  """
  Return the printed length of a string
  """
  return len(__strip_ANSI_escapes("",s))

def crop_to_printlen(s,l):
  """Return only as many characters such that the printed length
  of them is less than or equal l"""
  if printlen(s) <= l: return s
  i=l
  while printlen(s[:i]) < l:   i+=1
  return s[:i]

def list_basissets(l, highlight_elements=[], colour=True, elements=False, crop=True):
  """
  Pretty print the basissets in the list

  elements   Print the elements in the basis set as well
  highlight_elements    Highlight the elements in the list
  colour    Use colour
  crop      Use basic heuristics to crop the description string if it gets too long
  """
  print(len(l), "basis sets matched your search:")

  # TODO improve this method ... it really is a compound of a hell lot of code

  # Colours to use
  yellow='\033[93m'
  white='\033[0m'
  if not colour:  yellow=white

  # Print the elements as well?
  if highlight_elements: elements = True

  # Determine maximal lengths of the strings we have:
  maxlen_name=0
  maxlen_descr=0
  maxlen_elem=0
  for bset in l:
    maxlen_name = max(maxlen_name, len(bset["name"]))
    maxlen_descr = max(maxlen_descr, len(bset["description"]))
    maxlen_elem = max(maxlen_elem, len(",".join(bset["elements"])))

  # Ignore element string length if we don't care
  if not elements: maxlen_elem=0

  # Adjust depending on width of terminal
  cols, _  =shutil.get_terminal_size(fallback=(120,50))
  cols = max(120,cols)
  extra =4 # What we need for column separators, ...

  if maxlen_name + maxlen_descr + maxlen_elem + extra > cols:
    # We don't crop the name ever, so compute the remainder:
    rem = cols - maxlen_name - extra

    if elements:
      # 2/3 for description, but only if its needed
      # and at least 1/3 for elements:
      maxlen_descr = min(maxlen_descr,max(50,2*rem//3, rem-maxlen_elem-1))
      maxlen_elem = max(50,rem - maxlen_descr)
    else:
      maxlen_descr=rem
      maxlen_elem=0

  # Build format string:
  fstr=yellow+"{name:"+ str(maxlen_name) + "s}"+white
  fstr+="  {description:"+str(maxlen_descr)+"s}"
  if elements:
    fstr += "  {elements:"+str(maxlen_elem)+"s}"

  for bset in l:
    elems=",".join([
      yellow + e + white if e in highlight_elements else e for e in bset["elements"]
    ])
    descr=bset["description"]

    if crop and printlen(descr) > maxlen_descr:
      descr=crop_to_printlen(descr,maxlen_descr-3)
      descr+="..."
    if crop and printlen(elems) > maxlen_elem:
      elems=crop_to_printlen(elems,maxlen_elem-3+1)
      # Remove the half-printed element number after the last ","
      elems=elems[:elems.rfind(",")]
      elems+="..."

    print(fstr.format(name=bset["name"], description=descr, elements=elems))

def normalise_name(name):
  """Normalise a basis set name to yield a valid filename"""
  return "".join([ "I" if c == "/" else c for c in name.lower() ])

def download_basissets(l, format, contraction=True):
  """Download all basis sets in the list using the supplied format.

  Either download contracted basis sets or not
  """
  print("Downloading " + str(len(l)) + " basis sets in " + format + " format:")
  for b in l:
    path="./" + normalise_name(b["name"]) + "." + emsl.formats[format]

    if os.path.exists(path):
      print("   Warn: Skipping " + path + " since file already exists")
      continue

    print("   ", b["name"], " to ", path)
    with open(path, "w") as f:
      f.write(emsl.download_basisset(b,format))

def contains_elements(b, le):
  """Filter which tests whether a basis contains a list of elements"""
  for e in le:
    if not e in b["elements"]: return False
    return True

def main():
  parser = argparse.ArgumentParser(
    description="Commandline tool to search and download Gaussian basis sets. " \
    "The tool downloads (and caches) the list of basis sets from the emsl basis set exchange" \
    " (https://bse.pnl.gov/bse/portal) for offline search and allows to easily download individual basis sets from it.")

  parser.add_argument("--uncontracted", dest="contracted", action="store_false",
                      help="Receive uncontracted basis sets")
  parser.add_argument("--force-update", action="store_true",
                      help="Force the cached EMSL BSE database to be updated.")
  parser.add_argument("--print-elements", action="store_true",
                      help="When performing --list, print the elements for which a basis set is defined as well.")
  parser.add_argument("pattern", nargs='?', default=None, type=str,
                      help="A regular expression to match against the basis set name (Same as -e)")

  mode = parser.add_mutually_exclusive_group()
  mode.add_argument("--list", action='store_true', help="List the matching basis sets (Default)")
  mode.add_argument("--download", nargs="*", metavar='format',
                    choices=emsl.formats.keys(),
                    help="Download the matching basis sets in the requested formats "
                    "(Default: "+" ".join(config.default_download_formats)+")")

  filters = parser.add_argument_group("Basisset filters")
  filters.add_argument("--elements", metavar="element", nargs='+',
                       help="List of elements the basis set should contain. Implies '--print-elements'.")
  filters.add_argument("-e", "--regexp", dest="regexp",
                       metavar="regexp",
                       help="A regular expression to macth against the basis set name (same as 'pattern')")
  filters.add_argument("-d", "--description-regexp", metavar="regexp",
                       dest="description_regexp",
                       help="Regular expression the basis set description should match")
  filters.add_argument("-i", "--ignore-case", action="store_true",dest="ignorecase", 
                       help="Ignore case when matching patterns")
  args = parser.parse_args()

  # Initial parsing:
  if args.download is not None:
    # If we want download, than append at least the default
    # format to download
    args.download.extend(config.default_download_formats)
  if args.pattern is not None:
    args.regexp = args.pattern

  # Some defaults:
  case_transform = lambda s: s
  highlight_elements=[]
  filters = []

  # Parse args:
  if args.ignorecase:
    case_transform = lambda s: s.lower()

  if args.elements:
    highlight_elements=args.elements
    filters.append(lambda b: contains_elements(b,args.elements))
  if args.regexp:
    reg = re.compile(case_transform(args.regexp))
    filters.append(lambda b : reg.match(case_transform(b["name"])))
  if args.description_regexp:
    reg = re.compile(case_transform(args.description_regexp))
    filters.append(lambda b : reg.match(case_transform(b["description"])))

  # Predicate which is true iff all filters are true
  # for a particular b:
  matchall = lambda b : len(filters) == len(
    [ True for f in filters if f(b) ]
  )
  li = [ b for b in get_basisset_list(force_update=args.force_update) if matchall(b) ]

  if not li:
    raise SystemExit("No basis set matched your search")

  if args.download:
    for fmt in args.download:
      download_basissets(li, format=fmt, contraction=args.contracted)
  else:
    list_basissets(li,highlight_elements=highlight_elements, elements=args.print_elements)

if __name__ == "__main__":
  main()
