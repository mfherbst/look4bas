#!/usr/bin/env python3

from . import database as dbcache
from . import emsl, ccrepo, elements, config
import datetime
import os


__all__ = ["database", "amend_cgto_definitions"]


def database(dbfile=os.path.join(config.cache_folder, "basis_sets.db"),
             maxage=config.cache_maxage):
    """
    Obtain a Database object which guaranteed to be not older
    than maxage. If maxage is 0 or None, then the database
    will always be created from scratch.

    @param use_ccrepo     Obtaining data from ccrepo is pretty slow at the
                          moment. For this reason it is disabled by default
    """
    db = dbcache.Database(dbfile)

    age = datetime.datetime.utcnow() - db.timestamp
    if maxage is not None and maxage != 0 and age < maxage and not db.empty:
        return db
    else:
        db.clear()

        # TODO I do not fancy the print statement here, but I cannot see how else to do this.
        print("Updating cached data ... this may take a while.")

        # Add iupac elements to db
        db.create_table_of_elements("IUPAC",
                                    [e for e in elements.iupac_list() if e["atnum"] > 0])

        emsl.add_to_database(db)
        ccrepo.add_to_database(db)
        return db


def amend_cgto_definitions(db, basisset):
    """
    Download the contractions for all the elements of the basis dict passed.
    The dict is modified in-place and the result returned.
    """
    elem_list = db.obtain_element_list(basisset["source"])
    atoms_orig = basisset["atoms"]
    atnums = [at["atnum"] for at in atoms_orig]
    for atom in atoms_orig:
        if atom["has_functions"]:
            raise NotImplementedError("Cannot used cached data from db yet.")

    if basisset["source"] == "EMSL":
        basisset["atoms"] = emsl.download_cgto_for_atoms(elem_list, basisset["name"],
                                                         atnums, basisset["extra"])
        # TODO write data to db
    elif basisset["source"] == "ccrepo":
        basisset["atoms"] = ccrepo.download_cgto_for_atoms(elem_list, basisset["name"],
                                                           atnums, basisset["extra"])
        # TODO write data to db
    else:
        raise ValueError("Unknown basis set source: {}".format(basisset["source"]))
    return basisset
