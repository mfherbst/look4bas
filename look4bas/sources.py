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
    if maxage is not None and maxage != 0 and age < maxage and not db.empty:
        return db
    else:
        db.clear()
        emsl.add_to_database(db)
        # ccrepo.add_to_database(db)
        return db


def amend_cgto_definitions(db, basisset):
    """
    Download the contractions for all the elements of the basis dict passed.
    The dict is modified in-place and the result returned.
    """
    atoms_orig = basisset["atoms"]
    atnums = [at["atnum"] for at in atoms_orig]
    for atom in atoms_orig:
        if atom["has_functions"]:
            raise NotImplementedError("Cannot used cached data from db yet.")

    if basisset["source"] == "EMSL":
        basisset["atoms"] = emsl.download_cgto_for_atoms(basisset["name"],
                                                         atnums, basisset["extra"])
        # TODO write data to db
    elif basisset["source"] == "ccrepo":
        basisset["atoms"] = ccrepo.download_cgto_for_atoms(basisset["name"],
                                                           atnums, basisset["extra"])
        # TODO write data to db
    else:
        raise ValueError("Unknown basis set source: {}".format(basisset["source"]))
    return basisset
