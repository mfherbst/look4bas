#!/usr/bin/env python3

import sqlite3 as sqlite
import os
import re
import datetime
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
                self.__register_user_functions()

    def __register_user_functions(self):
        def matches(expr, item):
            return re.match(expr, item) is not None
        self.conn.create_function("MATCHES", 2, matches)

        def matchesi(expr, item):
            return re.match(expr, item, flags=re.I) is not None
        self.conn.create_function("MATCHESI", 2, matchesi)

    @property
    def timestamp(self):
        if os.path.exists(self.dbfile):
            return datetime.datetime.fromtimestamp(os.path.getmtime(self.dbfile))
        else:
            return datetime.datetime.fromtimestamp(0)

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
        self.__register_user_functions()

        with self.conn:
            cur = self.conn.cursor()

            # Table of basis sets
            cur.execute("CREATE TABLE BasisSet("
                        "Id INTEGER PRIMARY KEY, "
                        "Name TEXT, "        # Name of the basis set
                        "Description TEXT,"  # Short description
                        "Source TEXT, "      # Source of this definition
                                             # (e.g. EMSL, ccrepo)
                        "Extra TEXT"         # Extra info, specific to the source
                        ")")

            # Table of basis definitions for atoms contained in the basis sets
            cur.execute("CREATE TABLE AtomPerBasis("
                        "Id INTEGER PRIMARY KEY, "
                        "BasisSetID INT, "   # ID of the BasSet this atom entry
                        "AtNum INT, "        # Atomic number
                        "Reference TEXT,"    # Reference of a Paper where this set of
                                             # functions for this element were defined
                        "HasFunctions INT"   # Are the basis functions stored
                                             # in the database?
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

    @property
    def empty(self):
        with self.conn:
            cur = self.conn.cursor()
            count = cur.execute("SELECT COUNT(*) FROM BasisSet").fetchone()[0]
        return count == 0

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

            # Mark that the appropriate element has basis functions set in the db
            cur.execute("UPDATE AtomPerBasis SET HasFunctions = 1 WHERE Id = ?", atbas_id)

    def obtain_basis_functions(self, atbas_id):
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
                        (str(atbas_id),))
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

    def insert_basisset_atom(self, basset_id, atnum, reference=""):
        """
        Insert a new atom for a particular basis set.

        @param basset_id   ID of the basis set
        @param atnum       Atomic number
        @param reference   A paper reference if available

        returns the id of the element which was inserted.
        """
        if not isinstance(basset_id, int):
            raise TypeError("basset_id needs to be an integer")
        if not isinstance(atnum, int):
            raise TypeError("atnum needs to be an integer")
        if not isinstance(reference, str):
            raise TypeError("reference needs to be a string")

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO AtomPerBasis (BasisSetID, AtNum, Reference, HasFunctions)"
                "VALUES (?, ?, ?, 0)", (basset_id, atnum, reference)
            )
            rowid = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        return rowid

    def insert_basisset(self, name, source, extra="", description=""):
        """
        Insert a new basis set.

        @param name        Name of the basis set
        @param source      Source where the data comes from (e.g. EMSL, ccrepo)
        @param extra       Extra data depending on the source
        @param description Description of the basis set
        """
        if not isinstance(name, str):
            raise TypeError("name needs to be a string")
        if not isinstance(description, str):
            raise TypeError("description needs to be a string")
        if not isinstance(source, str):
            raise TypeError("source needs to be a string")
        if not isinstance(extra, str):
            raise TypeError("extra needs to be a string")

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO BasisSet (Name, Description, Source, Extra)"
                "VALUES (?, ?, ?, ?)", (name, description, source, extra)
            )
            rowid = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        return rowid

    def __ditcify_basisset_query_result(self, res):
        ret = {}
        for row in res:
            basset = ret.get(row[0], {"atoms": []})
            basset["id"], basset["name"], basset["description"], \
                basset["source"], basset["extra"], \
                atbas_id, atnum, has_functions = row
            basset["atoms"].append({
                "atnum": atnum,
                "atbas_id": atbas_id,
                "has_functions": bool(has_functions)
            })
            ret[row[0]] = basset
        return list(ret.values())

    def obtain_basisset(self, basset_id):
        """
        Return information about the basis set along with the list of defined
        atoms and their atbas_id to perform further queries with
        obtain_basis_functions. If the has_functions flag is false,
        then there are no basis functions defined in the database for this
        combination of atom and basis set.
        """
        if not isinstance(basset_id, int):
            raise TypeError("basset_id needs to be an integer")

        with self.conn:
            cur = self.conn.cursor()

            cur.execute("SELECT BasisSet.Id, BasisSet.Name, BasisSet.Description, " +
                        "BasisSet.Source, BasisSet.Extra, AtomPerBasis.Id, " +
                        "AtomPerBasis.AtNum, AtomPerBasis.HasFunctions " +
                        "FROM BasisSet LEFT JOIN AtomPerBasis " +
                        "ON AtomPerBasis.BasisSetID = BasisSet.Id " +
                        "WHERE BasisSet.Id = ?", (str(basset_id),))
            ret = self.__ditcify_basisset_query_result(cur.fetchall())
            assert len(ret) == 1
            return ret[0]

    def search_basisset(self, name=None, description=None, ignore_case=False,
                        has_atnums=[], source=None, regex=False):
        """
        Function to filter basis sets. If no arguments are provided,
        all registered basis sets will be returned.

        name    String to be contained in the basis set same
                or regular expression to be matched against the name.
        description   String to be contained in the description
                      or regular expression to be matched against it.
        has_atnums   Atoms to be contained in this basis set
                     Should be a list of atomic numbers.
        source       The source of the basis set. Is matched exactly.
        ignore_case  Regular expression and string matchings
                     in name and description are done ignoring case.
        regex        Are the strings supplied to name and descriptions
                     to be interpreted as regular exrpessions

        Returns a list of dicts with content id, name, description,
        source and extra and all atoms matching has_atnums.
        """
        if name is not None and not isinstance(name, str):
            raise TypeError("name needs to be None or a string")
        if description is not None and not isinstance(description, str):
            raise TypeError("descrption needs to be None or a string")
        if source is not None and not isinstance(source, str):
            raise TypeError("source needs to be None or a string")
        if not isinstance(has_atnums, list):
            raise TypeError("has_atnums needs to be alist")

        if regex:
            if ignore_case:
                def match_field(field):
                    return "matchesi(?, " + field + ")"
            else:
                def match_field(field):
                    return "matches(?, " + field + ")"
        else:
            if ignore_case:
                def match_field(field):
                    return "instr(lower(" + field + "), lower(?))"
            else:
                def match_field(field):
                    return "instr(" + field + ", ?)"

        prefix = ("SELECT BasisSet.Id, BasisSet.Name, BasisSet.Description, " +
                  "BasisSet.Source, BasisSet.Extra, AtomPerBasis.Id, " +
                  "AtomPerBasis.AtNum, AtomPerBasis.HasFunctions " +
                  "FROM BasisSet LEFT JOIN AtomPerBasis " +
                  "ON AtomPerBasis.BasisSetID = BasisSet.Id ")
        wheres = []
        args = []

        if name is not None:
            wheres.append(match_field("Name"))
            args.append(name)
        if description:
            wheres.append(match_field("Description"))
            args.append(description)
        if source:
            wheres.append("Source = ?")
            args.append(source)
        if has_atnums:
            for atnum in has_atnums:
                if not isinstance(atnum, int):
                    raise TypeError("All entries of has_atnums need to be integers")
                args.append(atnum)
            q = "(" + " OR ".join(len(has_atnums) * ["AtomPerBasis.AtNum = ?"]) + ")"
            wheres.append(q)

        if wheres:
            query = prefix + " WHERE " + " AND ".join(wheres)
        else:
            query = prefix

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(query, args)
            return self.__ditcify_basisset_query_result(cur.fetchall())
