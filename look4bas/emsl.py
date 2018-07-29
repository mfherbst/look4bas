#!/usr/bin/env python3

from bs4 import BeautifulSoup
import re
from . import tlsutil, gaussian94
import json


""" Dictionary of the basis set formats supported by emsl as well as this script,
    mapped to the default file extension used.
"""
formats = {
    "Gaussian94": "g94",
}


class EmslError(Exception):
    """
    Generic error thrown if some data obtained from the EMSL basis set exchange
    is not in the format expected
    """
    def __init__(self, message):
        super(EmslError, self).__init__(message)


"""Cache for the base url"""
__base_url_cache = None


def get_base_url():
    """
    Unfortunately the emsl base url changes from time to time.
    This function determines it.
    """
    global __base_url_cache
    if __base_url_cache is not None:
        return __base_url_cache

    portal_url = "https://bse.pnl.gov/bse/portal"
    ret = tlsutil.get_tls_fallback(portal_url)

    if not ret.ok:
        raise EmslError("Error determining base url from {}.".format(portal_url))
    soup = BeautifulSoup(ret.text, "lxml")

    iframe = soup.find("iframe", class_="chefContentIFrame")
    if iframe is None:
        raise EmslError("Could not find content iframe in {}.".format(portal_url))

    title_url = iframe["src"]
    if not title_url.endswith("/panel/Main/template/content"):
        raise EmslError("Unexpected title iframe url")

    __base_url_cache = title_url[:-28]
    return __base_url_cache


def _parse_list(string):
    """ Parse a list string into a list of strings"""
    if string[0] != "[" and string[-1] != "]":
        raise ValueError("Invalid list string: " + string)
    return [elem.strip() for elem in string[1:-1].split(sep=",")]


def _parse_basis_line(line):
    startstr = "new basisSet("
    endstr = ");"

    # Truncate the line
    line = line[line.find(startstr) + len(startstr):line.rfind(endstr)]

    # And split into argument strings (without leading and tailling '"')
    splitted = [m[1:-1] for m in re.findall('"[^"]*"', line)]

    if len(splitted) != 11:
        raise ValueError("Invalid emsl basis line: " + line +
                         ", error: More params than expected.")

    try:
        elems = _parse_list(splitted[3])
    except ValueError as e:
        raise ValueError("Invalid emsl basis line: " + line + ", error: " + e.args[0])

    return {
        "url": splitted[0],              # Url to download it from
        "name": splitted[1],             # Name of the basis
        "type": splitted[2],
        "elements": elems,
        "status": splitted[4],
        "hasEcp": splitted[5],
        "hasSpin": splitted[6],
        "lastModifiedDate": splitted[7],
        "contributionPI": splitted[8],
        "contributorName": splitted[9],
        "description": splitted[10]      # Short description of the basis
    }


def download_basisset_list(return_elements=False):
    """
    Download and parse the list of basis sets from emsl
    Returns a list of basis set dictionaries
    """
    # TODO This function should go in the future and merged
    #      into add_to_database

    base_url = get_base_url()
    ret = tlsutil.get_tls_fallback(base_url + "/panel/Main/template/content")

    if not ret.ok:
        raise EmslError("Error downloading list of basis sets from emsl")
    soup = BeautifulSoup(ret.text, "lxml")

    basis_sets = []  # The basis set list to return

    # Search expression for script tags which define basisSet objects
    re_bassets = re.compile("basisSets\[[0-9]+\]\W*=")

    # Search expression for the basisSet definition lines:
    re_basdef = re.compile("^\W*basisSets\[[0-9]+\]\W*=\W*new\W*basisSet")

    # Search expression for the number of basis sets expected
    re_num = re.compile("numBasis\W*=\W*([0-9]+)")

    # Seek through all script blocks, which contain basis definitions:
    for script in soup.find_all("script"):
        # Ignore script html tags, which do not contain the string
        # 'basisSets[number]=' in their text
        if not re_bassets.search(script.text):
            continue
        lines = script.text.splitlines()

        numlines = [re_num.search(l).group(1) for l in lines if re_num.search(l)]
        if len(numlines) > 1:
            raise EmslError("The string describing the number of basis sets is "
                            "found more than once.")
        expected_num_bases = int(numlines[0])

        try:
            bases = [_parse_basis_line(l) for l in lines if re_basdef.match(l)]
        except ValueError as e:
            raise EmslError(e.args[0])

        if (len(bases) != expected_num_bases):
            raise EmslError("Deviation between expected number of basis definitions "
                            "and the actual number found.")
        basis_sets.extend(bases)

    if len(basis_sets) == 0:
        raise EmslError("No basis sets obtained from emsl bse data")

    if not return_elements:
        return basis_sets

    elements = []  # The element list to return
    for div in soup.find_all(class_="table-row", name="div"):
        for elem in div.find_all(class_="elt", name="a"):
            # Loop over the periodic table that the emsl start page
            # produces and extract the elements

            if "id" not in elem.attrs or "title" not in elem.attrs:
                raise EmslError("Elements of the periodic table does not "
                                "contain attribute "
                                "'id' or 'title': {}".format(str(elem)))
            try:
                atnum = int(elem["id"])
            except ValueError:
                raise EmslError("Elements of the periodic table have a non-integer id "
                                "which cannot be interpreted as the atomic number: "
                                "{}".format(str(elem)))

            elements.append({
                "symbol": elem.text,
                "atnum": atnum,
                "name": elem["title"]
            })
    if len(elements) == 0:
        raise EmslError("No elements obtained from emsl bse data")
    return elements, basis_sets


def add_to_database(db):
    """
    Add the basis set definitions to the database
    """
    elements, lst = download_basisset_list(return_elements=True)
    db.create_table_of_elements("EMSL", elements)

    for bas in lst:
        extra = json.dumps({"url": bas["url"]})
        basset_id = db.insert_basisset(bas["name"], source="EMSL", extra=extra,
                                       description=bas["description"])

        for atom in bas["elements"]:
            try:
                element = db.search_element("EMSL", atom)
            except ValueError as e:
                if atom != "X":
                    # atom == X is a known issue in some of the basis set definitions
                    print("Skipping atom {}: ".format(atom) + str(e))
                continue
            db.insert_basisset_atom(basset_id, element["atnum"], reference="")


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
    basis_url = json.loads(extra)["url"]

    # Lookup atomic numbers to symbols
    symbols = [elem_list[atnum]["symbol"] for atnum in atnums]

    base_url = get_base_url()
    url = base_url + "/action/portlets.BasisSetAction/template/courier_content/panel/" \
        "Main/eventSubmit_doDownload/true"

    params = {
        "bsurl": basis_url,
        "bsname": bset_name,
        "elts":  " ".join(symbols) + " ",
        "format": "Gaussian94",
        "minimize": "true",      # Get contracted version, decontraction can happen later
    }

    ret = tlsutil.get_tls_fallback(url, params=params)
    if not ret.ok:
        raise EmslError("Error getting basis set " + bset_name + " from emsl.")
    soup = BeautifulSoup(ret.text, "lxml")

    # The basis set should be encoded inside a pre tag
    if soup.pre is None:
        raise EmslError("No pre in result from emsl for basis set name " + bset_name)
    if "$bsdata" in soup.pre.text:
        raise EmslError("Only found dummy content in pre element for basis set name " +
                        bset_name)

    ret = gaussian94.loads(soup.pre.text, elem_list=elem_list)
    if len(ret) < 1:
        raise AssertionError("Something went wrong parsing EMSL basis set text "
                             "\n{}".format(soup.pre.text))
    return ret
