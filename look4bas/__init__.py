#!/usr/bin/env python3
from . import database as dbcache
from . import emsl, ccrepo, elements
import datetime
import os

__version__ = '0.1.1'
__all__ = ["Database", "update_database"]


class Database(dbcache.Database):
    def __init__(self, dbfile="~/.local/share/look4bas/basis_sets.db"):
        super().__init__(os.path.expanduser(dbfile))

    def lookup_basisset_full(self, basisset):
        """
        Lookup information about the basis set in the database and return
        the list of defined atoms and their basis functions.
        If the data is not stored in the database then it is automatically
        downloaded on the fly.

        @param basisset     Basis set dict as returned by search_basisset or
                            basis set id.
        """
        basisset = self.lookup_basisset(basisset)

        # TODO Check if data exists in db if not add it.

        atnums = [at["atnum"] for at in basisset["atoms"]]
        elem_list = self.lookup_element_list(basisset["source"])

        if basisset["source"] == "EMSL":
            basisset["atoms"] = emsl.download_cgto_for_atoms(elem_list, basisset["name"],
                                                             atnums, basisset["extra"])
            # TODO write data to db
        elif basisset["source"] == "ccrepo":
            basisset["atoms"] = ccrepo.download_cgto_for_atoms(elem_list,
                                                               basisset["name"],
                                                               atnums, basisset["extra"])
            # TODO write data to db
        else:
            raise ValueError("Unknown basis set source: {}".format(basisset["source"]))
        return basisset


def update_database(db):
    """
    Update the provided database, i.e. check whether new records
    exist online and update accordingly.
    """
    # TODO poor mans solution for now ... update if older than 14 days.
    #
    # Better: Check the most recent modification time for the EMSL and ccrepo
    #         data and only update the respective sources if there are changes.
    maxage = datetime.timedelta(days=14)

    age = datetime.datetime.utcnow() - db.timestamp
    if age > maxage or db.empty:
        db.clear()

        emsl.add_to_database(db)
        ccrepo.add_to_database(db)
        db.create_table_of_elements(
            "IUPAC",
            [e for e in elements.iupac_list() if e["atnum"] > 0]
        )
