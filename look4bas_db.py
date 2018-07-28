#!/usr/bin/env python3

from look4bas import emsl, ccrepo, database


def download_basis_for_atom(name, atnum, source, extra):
    funmap = {
        "EMSL": emsl.download_basis_for_atom,
        "ccrepo": ccrepo.download_basis_for_atom,
    }
    return funmap[source](name, atnum, extra)


def main():
    db = database.Database()

    # Todo Find out about age of database by looking at the modification
    # time of the database file and if it's too old update

    # Update database (if its too old)
    db.clear()
    emsl.add_to_database(db)
    # ccrepo.add_to_database(db)

    # Look at _look4bas.py and invent sensible querying mechanisms
    # in database.py such that the frontend can stay as it is, but
    # the backend is now the database

    atnum = 2
    name = "pc-0"
    extra = '{"url": "/files/projects/Basis_Set_Curators/Gaussian/contrib/frj_new/PC-0.xml"}'
    res = download_basis_for_atom(name, atnum, "EMSL", extra)
    print(res)


if __name__ == "__main__":
    main()
