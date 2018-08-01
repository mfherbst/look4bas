#!/usr/bin/env python3

from bs4 import BeautifulSoup
from . import tlsutil, gaussian94
import json
import re

"""ccrepo base url"""
base_url = "https://grant-hill.group.shef.ac.uk/ccrepo"
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


def get_basis_g94(element, basis):
    """
    Get info about a basis set for a particular
    element in Gaussian94 format

    element: Element dictionary
    basis:   basis set identifier as used internally
             by ccrepo (returned as the mapped string by
             get_basis_sets_for_element.

    returns a dict with
        reference     Reference to the basis set
        description   Basis set description
        definition     The basis set definition in Gaussian94 format
    """
    sym = element["symbol"].lower()
    ele = element["name"]

    payload = {"basis": basis, "program": "Gaussian"}
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

    # All basis set definition content sits in a nobr block
    nobr = str(cont.nobr)
    nobr = nobr.replace("<nobr>", "")
    nobr = nobr.replace("</nobr>", "")
    nobr = nobr.replace("<br/>", "\n")
    nobr = nobr.replace("\n\n", "\n")
    nobr = re.sub("[ \t\r\f\v\xa0]", " ", nobr)
    nobr = nobr.replace("\n ", "\n")
    nobr = nobr.strip("\n")

    # Replace the BASIS= line by ****
    definition = re.sub("\nBASIS=[^\n]+\n", "\n****\n", nobr)

    # Find prelines with reference and description
    # This is really messy, but essentially tries to
    # extract the first two lines of real text
    cont_text = str(cont)
    cont_text = cont_text.replace("<br/>", "\n")
    prelines = []
    for line in cont_text.split("\n"):
        if len(line) == 0 or 'class="container"' in line:
            continue
        prelines.append(line.strip())
        if len(prelines) == 2:
            break

    reference = prelines[0]
    description = prelines[1]

    # Post-processing: Remove 'for Element':
    ifor = description.rfind("for ")
    description = description[:ifor].strip()
    description = description.replace("  ", " ")

    return {
        "reference": reference,
        "description": description,
        "definition": definition,
    }


def get_basis_sets_for_elem(element):
    page = base_url + "/" + element["name"] + "/index.html"
    ret = tlsutil.get_tls_fallback(page)
    if not ret.ok:
        raise CcrepoError("Error downloading list of elements from: " +
                          element["name"] + "/index.html")
    soup = BeautifulSoup(ret.text, "lxml")

    opt = soup.find_all(id="basis")
    if len(opt) == 0:
        pagetext = soup.text.strip()
        if "not quite ready to go yet" in pagetext or \
           "no correlation consistent basis sets" in pagetext:
            # The page is not yet ready ... return empty dictionary
            return dict()
        else:
            raise CcrepoError("Could not find basis on page.")
    elif len(opt) > 1:
        raise CcrepoError("Found more than one basis "
                          " field on the page " + page)
    opt = opt[0]
    return {option.text: option["value"] for option in opt.find_all("option")}


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
                # Download the basis for this very element
                # to obtain the description string
                basdef = get_basis_g94(elem, bas[name])

                bases[name] = {
                    "name": name,
                    "key":  bas[name],
                    "atoms": [elem["atnum"]],
                    "description": basdef["description"],
                }
    bases = list(bases.values())

    # Now add all of these to the database:
    for basset in bases:
        extra = json.dumps({"key": basset["key"]})
        basset_id = db.insert_basisset(basset["name"],
                                       description=basset["description"],
                                       source="ccrepo", extra=extra)
        for atnum in basset["atoms"]:
            # TODO Add reference
            db.insert_atom_to_basisset(basset_id, atnum, reference="")


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

    ret = []
    for atnum in atnums:
        basdef = get_basis_g94(elem_list[atnum], key)["definition"]

        # Parse obtained data and append to ret
        basparsed = gaussian94.loads(basdef)
        assert len(basparsed) == 1
        ret.append(basparsed[0])
    return ret
