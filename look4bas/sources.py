#!/usr/bin/env python3

import datetime
from . import emsl, ccrepo, database


def cache_database(maxage=datetime.timedelta(days=14)):
    """
    Obtain a Database object which guaranteed to be not older
    than maxage. If maxage is 0 or None, then the database
    will always be created from scratch.
    """
    db = database.Database()

    age = datetime.datetime.utcnow() - db.timestamp
    if maxage is not None and maxage != 0 and age < maxage:
        return db
    else:
        db.clear()
        emsl.add_to_database(db)
        # ccrepo.add_to_database(db)


def amend_cgto_definitions(basisset):
    """
    Download the contractions for all the elements of the basis dict passed.
    The dict is modified in-place and the result returned.
    """
    for atom in basisset["atoms"]:
        del atom["has_functions"]

        if basisset["source"] == "EMSL":
            atom["functions"] = emsl.download_cgto_for_atom(basisset["name"],
                                                            atom["atnum"],
                                                            basisset["extra"])
        elif basisset["source"] == "ccrepo":
            atom["functions"] = ccrepo.download_cgto_for_atom(basisset["name"],
                                                              atom["atnum"],
                                                              basisset["extra"])
        else:
            raise ValueError("Unknown basis set source: {}".format(basisset["source"]))
    return basisset
