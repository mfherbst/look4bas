#!/usr/bin/env python3

import codecs
import datetime
import os
import re
import sqlite3 as sqlite


def capitalise(word):
    return word[0].upper() + word[1:]


def quote_identifier(s, errors="strict"):
    """
    Quote identifiers for sqlite (e.g. table names)
    """
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return "\"" + encodable.replace("\"", "\"\"") + "\""


class Database:
    """Database frontend"""

    """Current database version"""
    database_version = 1

    def __init__(self, dbfile):
        """
        Initialise specifying database to work on
        """
        self.dbfile = dbfile
        self.conn = None

        if not os.path.isfile(dbfile):
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
            return re.search(expr, item) is not None
        self.conn.create_function("MATCHES", 2, matches)

        def matchesi(expr, item):
            return re.search(expr, item, flags=re.I) is not None
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

    def create_table_of_elements(self, source, elements):
        """
        Create a table of elements in a convention used
        by a particular source (e.g. IUPAC, EMSL, ccrepo).

        elements should be a list of dicts with the entries
            atnum:   Atom number
            symbol:  Atom symbol
            name:    Atom name
        """
        tablename = quote_identifier("Elements" + str(source))
        with self.conn:
            cur = self.conn.cursor()

            # Drop the table if it exists
            cur.execute("DROP TABLE IF EXISTS " + tablename)
            cur.execute("CREATE TABLE " + tablename + " ("
                        "AtNum INTEGER PRIMARY KEY, "  # Atomic number
                        "Symbol TEXT, "  # Atom symbol in all lower case
                        "Name TEXT"      # Atom name
                        ")")

            for elem in elements:
                symbol = elem["symbol"].lower()
                cur.execute(
                    "INSERT INTO " + tablename + " "
                    "(AtNum, Symbol, Name) VALUES (?, ?, ?)",
                    (elem["atnum"], symbol, elem["name"])
                )

    def search_element(self, source, key):
        """
        Search an element by the given key in symbol,
        name and atom number and return a dict with the keys
            atnum:   Atom number
            symbol:  Atom symbol
            name:    Atom name

        @param source  The source to search in (e.g. EMSL, ccrepo, IUPAC)
        @param key     The key to search for
        """
        if isinstance(key, int):
            query = "Atnum = ?"
            args = [key]
        elif isinstance(key, str):
            query = "Name = ? OR Symbol = ?"
            args = [key.lower(), key.lower()]
        else:
            raise TypeError("Key may either be a string or an integer")

        tablename = quote_identifier("Elements" + str(source))
        with self.conn:
            cur = self.conn.cursor()

            cur.execute("SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name=" + tablename)
            res = cur.fetchone()
            if res is None:
                raise ValueError("Unknown source {}".format(source))

            cur.execute("SELECT * FROM " + tablename + " " + "WHERE " + query, args)
            res = cur.fetchall()

        if len(res) == 0:
            raise ValueError("No element not found, which matches key {}".format(key))
        assert len(res) == 1
        entry = res[0]

        symbol = capitalise(entry[1])
        return {"atnum": entry[0], "symbol": symbol, "name": entry[2]}

    def obtain_element_list(self, source):
        """
        Build the list of elements per atomic number for a particular
        source (e.g. EMSL, ccrepo, IUPAC).

        The first entry of the list is "X", which is a dummy place holder.
        """
        tablename = quote_identifier("Elements" + str(source))
        with self.conn:
            cur = self.conn.cursor()

            cur.execute("SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name=" + tablename)
            res = cur.fetchone()
            if res is None:
                raise ValueError("Unknown source {}".format(source))

            cur.execute("SELECT AtNum, Symbol, Name FROM " + tablename +
                        " ORDER BY AtNum ASC")
            ret = [{"atnum": 0, "symbol": "X", "name": "dummy"}]
            for atnum, symbol, name in cur.fetchall():
                ret.append({"atnum": atnum, "name": name,
                            "symbol": capitalise(symbol)})
        return ret

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
                        has_atnums=[], source=None, regex=False, pattern=None):
        """
        Function to filter basis sets. If no arguments are provided,
        all registered basis sets will be returned.

        name    String to be contained in the basis set same
                or regular expression to be matched against the name.
        description   String to be contained in the description
                      or regular expression to be matched against it.
        pattern      String to be contained either in the basis set name
                     *or* the description or regex to be matching
                     against either these fields.
        has_atnums   Atoms to be contained in this basis set
                     Should be a list of atomic numbers.
        source       The source of the basis set. Is matched exactly.
        ignore_case  Regular expression and string matchings
                     in name, pattern and description are done ignoring case.
        regex        Are the strings supplied to name, descriptions
                     and pattern
                     to be interpreted as regular exrpessions

        Returns a list of dicts with content id, name, description,
        source and extra and their respective atoms.
        """
        if name is not None and not isinstance(name, str):
            raise TypeError("name needs to be None or a string")
        if description is not None and not isinstance(description, str):
            raise TypeError("descrption needs to be None or a string")
        if pattern is not None and not isinstance(pattern, str):
            raise TypeError("pattern needs to be None or a string")
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
        if pattern:
            q = "( " + match_field("Description") + \
                " OR " + match_field("Name") + " )"
            wheres.append(q)
            args.append(pattern)
            args.append(pattern)
        if source:
            wheres.append("Source = ?")
            args.append(source)
        if has_atnums:
            for atnum in has_atnums:
                if not isinstance(atnum, int):
                    raise TypeError("All entries of has_atnums need to be integers")
                args.append(atnum)
            q = "(BasisSet.Id IN (SELECT BasisSetID FROM AtomPerBasis WHERE " + \
                " OR ".join(len(has_atnums) * ["AtNum = ?"]) + "))"
            wheres.append(q)

        if wheres:
            query = prefix + " WHERE " + " AND ".join(wheres)
        else:
            query = prefix

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(query, args)
            return self.__ditcify_basisset_query_result(cur.fetchall())
