#!/usr/bin/env python3

import sqlite3 as sqlite
import os
from . import config


# Current expected version of the database
DEFAULT_DB_FILE = os.path.join(config.cache_folder, "basis_sets.db")


class Database:
    """Database frontend"""

    """Current database version"""
    database_version = 1

    def __init__(self, dbfile=DEFAULT_DB_FILE, force_create=False):
        """
        Initialise specifying database to work on
        """
        self.dbfile = dbfile
        self.conn = None

        if not os.path.isfile(dbfile):
            self.clear()
        elif force_create:
            self.clear()
        else:
            conn = sqlite.connect(dbfile)

            # Check version: version < DB_VERSION indicates an invalid db,
            # that is too old or uninitialised and needs to be discarded
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version is None or version < self.database_version:
                # Delete current database and create a new one
                self.clear()
            else:
                self.conn = conn

    def clear(self):
        """Clear the complete database and reset to untouched state"""
        if self.conn:
            self.conn.close()
            self.conn = None
        if os.path.isfile(self.dbfile):
            os.remove(self.dbfile)

        dirname = os.path.dirname(self.dbfile)
        os.makedirs(dirname, exist_ok=True)
        self.conn = sqlite.connect(self.dbfile)

        with self.conn:
            cur = self.conn.cursor()

            # Table of basis sets
            cur.execute("CREATE TABLE BasisSet("
                        "Id INTEGER PRIMARY KEY, "
                        "Name TEXT, "               # Name of the basis set
                        "Description TEXT"          # Short description
                        ")")

            # Table of basis definitions for atoms contained in the basis sets
            cur.execute("CREATE TABLE AtomPerBasis("
                        "Id INTEGER PRIMARY KEY, "
                        "BasisSetID INT, "   # ID of the BasSet this atom entry
                        "AtNum INT, "        # Atomic number
                        "Source TEXT, "      # Source of this definition
                                             # (e.g. EMSL, ccrepo)
                        "Extra TEXT,"        # Extra info, specific to the source
                        "Reference TEXT"     # Reference of a Paper where this set of
                                             # functions for this element were defined
                        ")")

            # Table of contracted basis functions
            cur.execute("CREATE TABLE BasisFunctions("
                        "Id INTEGER PRIMARY KEY, "
                        "AtomBasisId INT, "      # ID of the AtomBasis of this function
                        "AngularMomentum INT "   # angular momentum quantum number
                        ")")

            # Table of contraction coefficients
            cur.execute("CREATE TABLE Contraction("
                        "Id INTEGER PRIMARY KEY, "  # Unique ID
                        "FunctionId INT, "     # ID of the basis function
                        "Coefficient REAL,"    # Contraction coefficient
                        "Exponent REAL"        # Gaussian exponent
                        ")")

            # Set value to db version to indicate initialisation
            cur.execute("PRAGMA user_version = {v:d}".format(v=self.database_version))

    def close(self):
        """
        Close the connection held by conn
        """
        self.conn.close()
        self.conn = None

    def insert_basis_function(self, atbas_id, angular_momentum, coefficients, exponents):
        """
        Insert a list of contractions for the provided element.

        @param atbas_id      ID of the atom for which functions should be added to the
                             basis set
        @param angular_momentum    Angular momentum of the contracted basis function
                                   to be inserted
        @param coefficients  List of contraction coefficients
        @param exponents     List of contraction exponents
        """
        if not isinstance(atbas_id, int):
            raise TypeError("atbas_id needs to be an integer")
        if not isinstance(angular_momentum, int):
            raise TypeError("angular_momentum needs to be an integer")
        if len(coefficients) != len(exponents):
            raise ValueError("Coefficients and exponents need to have the "
                             "same length")
        with self.conn:
            cur = self.conn.cursor()

            cur.execute(
                "INSERT INTO BasisFunctions (AtomBasisId, AngularMomentum)"
                "VALUES (?, ?)", (atbas_id, angular_momentum)
            )
            function_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]

            for i, coeff in enumerate(coefficients):
                exp = exponents[i]
                cur.execute(
                    "INSERT INTO Contraction "
                    "(FunctionId, Coefficient, Exponent) VALUES"
                    "(?, ?, ?)", (function_id, coeff, exp)
                )

    def select_basis_functions(self, atbas_id):
        """
        Select all basis functions belonging to a particular atbas_id.

        Returns a list of dicts with the keys
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
        """
        if not isinstance(atbas_id, int):
            raise TypeError("atbas_id needs to be an integer")

        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT BasisFunctions.AngularMomentum, Contraction.FunctionId, "
                        "Contraction.Coefficient, Contraction.Exponent "
                        "FROM BasisFunctions "
                        "INNER JOIN Contraction ON BasisFunctions.Id = "
                        "Contraction.FunctionId WHERE BasisFunctions.AtomBasisId = ?",
                        str(atbas_id))
            contractions = cur.fetchall()

            ret = {}
            for am, fun_id, coeff, exp in contractions:
                if fun_id not in ret:
                    ret[fun_id] = {"coefficients": [coeff],
                                   "exponents": [exp],
                                   "angular_momentum": am, }
                else:
                    assert am == ret[fun_id]["angular_momentum"]
                    ret[fun_id]["coefficients"].append(coeff)
                    ret[fun_id]["exponents"].append(exp)
        return list(ret.values())

    def insert_basset_atom(self, basset_id, atnum, source, extra="", reference=""):
        """
        Insert a new atom for a particular basis set.

        @param basset_id   ID of the basis set
        @param atnum       Atomic number
        @param source      Source where the data comes from (e.g. EMSL, ccrepo)
        @param extra       Extra data depending on the source
        @param reference   A paper reference if available

        returns the id of the element which was inserted.
        """
        if not isinstance(basset_id, int):
            raise TypeError("basset_id needs to be an integer")
        if not isinstance(atnum, int):
            raise TypeError("atnum needs to be an integer")
        if not isinstance(source, str):
            raise TypeError("source needs to be a string")
        if not isinstance(reference, str):
            raise TypeError("reference needs to be a string")

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO AtomPerBasis (BasisSetID, AtNum, Source, Extra, Reference)"
                "VALUES (?, ?, ?, ?, ?)",
                (basset_id, atnum, source, extra, reference)
            )
            rowid = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        return rowid

    def insert_basset(self, name, description=""):
        if not isinstance(name, str):
            raise TypeError("name needs to be a string")
        if not isinstance(description, str):
            raise TypeError("description needs to be a string")

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO BasisSet (Name, Description)"
                "VALUES (?, ?)", (name, description)
            )
            rowid = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        return rowid
