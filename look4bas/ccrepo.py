#!/usr/bin/env python3

from . import tlsutil, element, gaussian94
import re
import json
from bs4 import BeautifulSoup
import warnings

"""ccrepo base url"""
base_url = "http://grant-hill.group.shef.ac.uk/ccrepo"
# https does not work


class CcrepoError(Exception):
    """
    Generic error thrown if some data obtained from the EMSL basis set exchange
    is not in the format expected
    """
    def __init__(self, message):
        super(CcrepoError, self).__init__(message)


def get_element_list():
    ret = tlsutil.get_tls_fallback(base_url)
    if not ret.ok:
        raise CcrepoError("Error downloading list of elements from ccrepo")
    soup = BeautifulSoup(ret.text, "lxml")

    table = soup.find_all(id="pertable")
    if len(table) != 1:
        raise CcrepoError("Found more than one periodic table on the page")
    table = table[0]

    elements = []
    for elem in table.find_all(class_=re.compile("xs|xp|xd|xf|xg")):
        atnum = elem.find(class_="at_num")
        sym = elem.find(class_="symbol")

        if atnum is None or sym is None:
            continue

        try:
            atnum = int(atnum.text)
        except TypeError as e:
            raise CcrepoError("Cannot interpret as atom number: " + str(e))

        if "href" not in sym.a.attrs:
            raise CcrepoError("No element link fund for " + sym.a.text)
        name = sym.a["href"]
        if name.endswith("index.html"):
            name = name[:-10]
        name = name.strip("/")

        sym = sym.text
        elem_obj = {"symbol": sym, "name": name, "number": atnum}
        elements.append(elem_obj)
    return elements


def get_basis_set_definition(element, basis, format):
    """
    element: Element dictionary
    basis:   basis set identifier as used internally
             by ccrepo (returned as the mapped string by
             get_basis_sets_for_element.
    format:  The internal identifier used to identify
             the basis set format used.
             (returned as the mapped string by
             get_formats_for_element)
    """
    sym = element["symbol"].lower()
    ele = element["name"]

    payload = {"basis": basis, "program": format}
    page = base_url + "/" + ele + "/" + sym + "basis.php"
    ret = tlsutil.post_tls_fallback(page, data=payload)

    if not ret.ok:
        raise CcrepoError("Error downloading page " + page)

    if len(ret.text) == 0:
        raise CcrepoError("Got unexpected empty page on " + page)

    soup = BeautifulSoup(ret.text, "lxml")
    cont = soup.find_all(class_="container")
    if len(cont) == 0:
        raise CcrepoError("Found no container on page " + page)
    if len(cont) > 1:
        raise CcrepoError("Found more than one container on the page " + page)
    cont = cont[0]

    # TODO Extract reference as well!

    # All content sits in a nobr block
    cont = str(cont.nobr)
    cont = cont.replace("<nobr>", "")
    cont = cont.replace("</nobr>", "")
    cont = cont.replace("<br/>", "\n")
    cont = cont.replace("\n\n", "\n")
    cont = re.sub("[ \t\r\f\v\xa0]", " ", cont)
    cont = cont.replace("\n ", "\n")
    cont = cont.strip("\n")
    return cont


def __get_options(option, element):
    page = base_url + "/" + element["name"] + "/index.html"
    ret = tlsutil.get_tls_fallback(page)
    if not ret.ok:
        raise CcrepoError("Error downloading list of elements from: " +
                          element["name"] + "/index.html")
    soup = BeautifulSoup(ret.text, "lxml")

    opt = soup.find_all(id=option)
    if len(opt) == 0:
        pagetext = soup.text.strip()
        if "not quite ready to go yet" in pagetext or \
           "no correlation consistent basis sets" in pagetext:
            # The page is not yet ready ... return empty dictionary
            return dict()
        else:
            raise CcrepoError("Could not find " + option + " on page.")
    elif len(opt) > 1:
        raise CcrepoError("Found more than one " + option +
                          " field on the page " + page)
    opt = opt[0]
    return {option.text: option["value"] for option in opt.find_all("option")}


def get_basis_sets_for_elem(element):
    return __get_options("basis", element)


def get_formats_for_elem(element):
    return __get_options("program", element)


def download_basisset_list():
    elements = get_element_list()

    bases = dict()
    for elem in elements:
        bas = get_basis_sets_for_elem(elem)

        for name in bas:
            if name in bases:
                bases[name]["elements"].append(dict(elem))
            else:
                bases[name] = {
                    "name": name,
                    "key":  bas[name],
                    "elements": [dict(elem)],
                }
    return [bases[k] for k in bases]


def merge_gaussian_basis(parts):
    startlines = []
    bodylines = []
    appended_BASIS_line = False
    for i, part in enumerate(parts):
        # Did we already get the BASIS= line for the element?
        got_BASIS_line = False
        for line in part.split("\n"):
            if got_BASIS_line:
                bodylines.append(line)
            elif line.startswith("BASIS="):
                got_BASIS_line = True
                if not appended_BASIS_line:
                    startlines.append(line)
                    appended_BASIS_line = True
            elif len(line) > 0 and line != "!":
                startlines.append(line)
        if not got_BASIS_line:
            raise CcrepoError("Did not get any BASIS= line for the " +
                              str(i) + "th gaussian basis file part.")
    return "\n".join(startlines) + "\n\n****\n" + "\n".join(bodylines)


def download_basisset_raw(basisset, format):
    # TODO We assume the same formats are available for all elements
    element = basisset["elements"][0]
    formats = get_formats_for_elem(element)
    if format not in formats:
        raise ValueError("The format " + format + " is unsupported.")

    basis_set_files = [
        (elem["symbol"], get_basis_set_definition(elem, basisset["key"], formats[format]))
        for elem in basisset["elements"]
    ]

    # Remove empty basis set files (This is due to an upstream error)
    # and warn about them.
    basis_set_empty = [elem for elem, basis in basis_set_files if len(basis) == 0]
    if len(basis_set_empty) > 0:
        warnings.warn("While obtaing the basis set " + basisset["name"] +
                      " these elements gave rise to empty basis definitions: " +
                      ", ".join(basis_set_empty) + ". " +
                      "This typically indicates an error at the ccrepo website.")
    basis_set_files = [bset for elem, bset in basis_set_files if len(bset) > 0]

    if format == "Gaussian":
        return merge_gaussian_basis(basis_set_files)
    else:
        raise NotImplementedError("Only merging gaussian basis sets is "
                                  "currently implemented.")


def add_to_database(db):
    """
    Add the basis set definitions to the database
    """
    lst = download_basisset_list()

    for bas in lst:
        extra = json.dumps({"key": bas["key"]})
        basset_id = db.insert_basisset(bas["name"], description="",
                                       source="ccrepo", extra=extra)

        for elem in bas["elements"]:
            # TODO Do not use element.by, use a custom translation table,
            #      which is cached from the ccrepo website
            atnum = element.by_symbol(elem["symbol"]).atom_number
            db.insert_basisset_atom(basset_id, atnum, reference="")


def download_cgto_for_atoms(bset_name, atnums, extra):
    """
    Obtain the contracted Gaussian functions for the basis with the
    given name, the atom with the given atomic number as well
    as the indicated extra information.

    @param bset_name   Name of the basis set
    @param atnum  List of atomic numbers
    @param extra  Extra info required

    Returns a list of dicts containing the following entries:
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    """
    key = json.loads(extra)["key"]

    elem0 = element.by_atomic_number(atnums[0])
    formats = get_formats_for_elem(elem0._asdict())  # Note: This is an https request!

    ret = []
    for atnum in atnums:
        elem = element.by_atomic_number(atnum)
        basdef = get_basis_set_definition(elem._asdict(), key, formats["Gaussian"])

        # Replace the BASIS= line by ****
        basdef = re.sub("\nBASIS=[^\n]+\n", "\n****\n", basdef)

        basparsed = gaussian94.loads(basdef)
        assert len(basparsed) == 1
        ret.append(basparsed[0])
    return ret


def main(format="Gaussian"):
    ss = 22
    data = download_basisset_list()
    print("Selecting set: ", data[ss]["name"])
    print(download_basisset_raw(data[ss], format))


if __name__ == "__main__":
    main()
