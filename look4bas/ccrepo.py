#!/usr/bin/env python3

from bs4 import BeautifulSoup
from . import tlsutil, gaussian94
import json
import re
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
        elem_obj = {"symbol": sym, "name": name, "atnum": atnum}
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


def add_to_database(db):
    """
    Add the basis set definitions to the database
    """
    elements = get_element_list()
    db.create_table_of_elements("ccrepo", elements)

    # Obtain unique list of basis sets and the elements
    # these are defined for
    bases = dict()
    for elem in elements:
        bas = get_basis_sets_for_elem(elem)

        for name in bas:
            if name in bases:
                bases[name]["atoms"].append(elem["atnum"])
            else:
                bases[name] = {
                    "name": name,
                    "key":  bas[name],
                    "atoms": [elem["atnum"]],
                }
    bases = list(bases.values())

    # Now add all of these to the database:
    for basset in bases:
        # TODO This is a hack for now to indicate that this is from ccrepo
        description = "<ccrepo>"
        extra = json.dumps({"key": basset["key"]})
        basset_id = db.insert_basisset(basset["name"], description=description,
                                       source="ccrepo", extra=extra)
        for atnum in basset["atoms"]:
            db.insert_basisset_atom(basset_id, atnum, reference="")


def download_cgto_for_atoms(elem_list, bset_name, atnums, extra):
    """
    Obtain the contracted Gaussian functions for the basis with the
    given name, the atom with the given atomic number as well
    as the indicated extra information.

    @param elem_list   List to use for element symbol <-> atomic number lookups
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

    basis_set_empty = []
    ret = []
    for atnum in atnums:
        basdef = get_basis_set_definition(elem_list[atnum], key, "Gaussian")

        # Remove empty basis set files (This is due to an upstream error)
        # and warn about them.
        if len(basdef) == 0:
            basis_set_empty += elem_list[atnum]["symbol"]
            continue

        # Replace the BASIS= line by ****
        basdef = re.sub("\nBASIS=[^\n]+\n", "\n****\n", basdef)

        # Parse obtained data and append to ret
        basparsed = gaussian94.loads(basdef)
        assert len(basparsed) == 1
        ret.append(basparsed[0])

    warnings.warn("While obtaing the basis set " + bset_name +
                  " these elements gave rise to empty basis definitions: " +
                  ", ".join(basis_set_empty) + ". " +
                  "This typically indicates an error at the ccrepo website.")
    return ret
