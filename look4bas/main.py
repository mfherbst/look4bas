#!/usr/bin/env python3

from look4bas import sources, config, gaussian94


def main():
    # Update database (use internet if too old)
    db = sources.cache_database(config.cache_maxage)

    # Search for ccpvdz
    findings = db.search_basisset(name="cc-pVDZ$", regex=True, has_atnums=[2, 6])

    if len(findings) == 0:
        raise SystemExit("ccpvdz not found")

    # Found ... now obtain all details
    ccpvdz = db.obtain_basisset(findings[0]["id"])
    # and the contractions
    ccpvdz = sources.amend_cgto_definitions(db, ccpvdz)

    print(gaussian94.dumps(ccpvdz["atoms"]))
    with open(ccpvdz["name"] + ".g94", "w") as f:
        f.write(gaussian94.dumps(ccpvdz["atoms"]))


if __name__ == "__main__":
    main()
