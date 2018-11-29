#!/usr/bin/env python3
from . import database as dbcache
from . import emsl, ccrepo, elements, tlsutil
import datetime
import os

__version__ = '0.2.3'
__licence__ = "GPL v3"
__authors__ = "Michael F. Herbsty"
__email__ = "info@michael-herbst.com"

__all__ = ["Database"]


available_sources = ["EMSL", "ccrepo"]


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

    def update_from_source_sites(self):
        """
        Update the database by scraping the source websites (i.e EMSL and ccrepo).

        This takes longer than the default update function, but there is the
        guarantee that the data is the uttermost recent.
        """
        # TODO: Check the most recent modification time for the EMSL and ccrepo
        #       data and only update the respective sources if there are changes.

        self.clear()
        emsl.add_to_database(self)
        ccrepo.add_to_database(self)
        self.create_table_of_elements(
            "IUPAC",
            [e for e in elements.iupac_list() if e["atnum"] > 0]
        )

    def update(self, url="https://get.michael-herbst.com/look4bas/basis_sets.db"):
        """
        Update the database, i.e. check whether a newer version
        exists on get.michael-herbst.com/look4bas/basis_sets.db
        and update accordingly.
        """
        # If last update was less than 2 days ago, do nothing
        age = datetime.datetime.utcnow() - self.timestamp
        if age < datetime.timedelta(days=2):
            return

        # Else get the most recent database from the web
        ret = tlsutil.get_tls_fallback(url)
        if not ret.ok:
            raise IOError("Error updating basis_set database from "
                          "'{}'".format(url))
        if "Last-Modified" in ret.headers:
            try:
                lastmodified = None
                lastmodified = datetime.datetime.strptime(ret.headers["Last-Modified"],
                                                          "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError as e:
                raise ValueError("Error parsing last modified date from '{}': \n{}"
                                 "".format(url, str(e)))

        # Perform update only if local version is older
        if self.timestamp < lastmodified:
            # Close the database and overwrite the databasefile on disk
            self.close()
            if os.path.exists(self.dbfile):
                os.remove(self.dbfile)

            with open(self.dbfile, "wb") as f:
                f.write(ret.content)

            # Reconnect to the updated file
            self.connect(self.dbfile)
