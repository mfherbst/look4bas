#!/usr/bin/env python3
import look4bas.cache
import look4bas.ccrepo
import sys
import warnings


def main():
    warnings.warn("This is a dummy script to download a single, "
                  "known basis set from the ccrepo. "
                  "It will certainly disappear in the future and is "
                  "just around to be able to use ccrepo from the "
                  "commandline at all.")

    if len(sys.argv) < 2:
        raise SystemExit("Need basis set name as in ccrepo")
    data = look4bas.cache.get_basisset_list("ccrepo")

    name = sys.argv[1]
    bset = [d for d in data if d["name"] == name]
    if len(bset) > 1:
        raise SystemExit("Found more than one basis")
    elif len(bset) == 0:
        raise SystemExit("Found no basis")

    down = look4bas.ccrepo.download_basisset(bset[0], "Gaussian")
    with open(name + ".g94", "w") as f:
        f.write(down)


if __name__ == "__main__":
    main()
