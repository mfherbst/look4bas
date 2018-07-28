#!/usr/bin/env python3

from bs4 import BeautifulSoup
import re
from . import tlsutil, gaussian94, element
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


def download_basisset_raw(basisset, format):
    """
    Obtain a basisset from the emsl library in a certain format
    for all the elements which are available

    Return the downloaded basis set data as a string.
    """
    # TODO contraction=False does not seem to work and is hence
    #      not exposed via the interface

    base_url = get_base_url()
    url = base_url + "/action/portlets.BasisSetAction/template/courier_content/panel/" \
        "Main/eventSubmit_doDownload/true"

    params = {
        "bsurl": basisset['url'],
        "bsname": basisset['name'],
        "elts": " ".join(basisset['elements']) + " ",
        "format": format,
        # Or "false" if not optimised general contractions are desired
        "minimize": "true",
    }

    ret = tlsutil.get_tls_fallback(url, params=params)
    if not ret.ok:
        raise EmslError("Error getting basis set " + basisset['name'] + " from emsl.")
    soup = BeautifulSoup(ret.text, "lxml")

    # The basis set should be encoded inside a pre tag
    if soup.pre is None:
        raise EmslError("No pre in result from emsl for basis set name " +
                        basisset['name'])
    if "$bsdata" in soup.pre.text:
        raise EmslError("Only found dummy content in pre element for basis set name " +
                        basisset['name'])
    return soup.pre.text


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


def download_basisset_list():
    """
    Download and parse the list of basis sets from emsl
    Returns a list of basis set dictionaries
    """
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

    return basis_sets


def add_to_database(db):
    """
    Add the basis set definitions to the database
    """
    lst = download_basisset_list()

    for bas in lst:
        extra = json.dumps({"url": bas["url"]})
        basset_id = db.insert_basisset(bas["name"], source="EMSL", extra=extra,
                                       description=bas["description"])

        for atom in bas["elements"]:
            try:
                # TODO Do not use element.by, use a custom translation table,
                #      which is cached from the emsl website
                atnum = element.by_symbol(atom).atom_number
            except KeyError as e:
                print("Skipping atom {}: ".format(atom) + str(e))
                continue
            db.insert_basisset_atom(basset_id, atnum, reference="")


def download_cgto_for_atom(bset_name, atnum, extra):
    """
    Obtain the contracted Gaussian functions for the basis with the
    given name, the atom with the given atomic number as well
    as the indicated extra information.

    @param bset_name   Name of the basis set
    @param atnum  Atomic number
    @param extra  Extra info required

    Returns a list of dicts with the following information:
        angular_momentum  Angular momentum of the function
        coefficients      List of contraction coefficients
        exponents         List of contraction exponents
    """
    basis_url = json.loads(extra)["url"]

    # TODO Do not use element.by, use a custom translation table,
    #      which is cached from the emsl website
    symbol = element.by_atomic_number(atnum).symbol

    base_url = get_base_url()
    url = base_url + "/action/portlets.BasisSetAction/template/courier_content/panel/" \
        "Main/eventSubmit_doDownload/true"

    params = {
        "bsurl": basis_url,
        "bsname": bset_name,
        "elts":  symbol + " ",
        "format": "Gaussian94",
        "minimize": "true",      # Get contracted version, decontraction can happen later
    }

    ret = tlsutil.get_tls_fallback(url, params=params)
    if not ret.ok:
        raise EmslError("Error getting basis set " + bset_name + " from emsl.")
    soup = BeautifulSoup(ret.text, "lxml")

    # The basis set should be encoded inside a pre tag
    if soup.pre is None:
        raise EmslError("No pre in result from emsl for basis set name " +
                        bset_name)
    if "$bsdata" in soup.pre.text:
        raise EmslError("Only found dummy content in pre element for basis set name " +
                        bset_name)

    ret = gaussian94.parse_g94(soup.pre.text)
    if len(ret) != 1:
        raise AssertionError("Something went wrong parsing EMSL basis set text "
                             "\n{}".format(soup.pre.text))

    return ret[0]["functions"]


def download_cgto_for_basisset(bset_name, extra):
    pass # TODO Improved version where the complete basis set is downloaded at once
    # left for the caller to filter what he / she needs
