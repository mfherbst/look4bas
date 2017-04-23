#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup

""" List of basis set formats supported by emsl as well as this script """
formats=[ "Gaussian94", ]

""" Emsl BSE base url """
base_url="https://bse.pnl.gov:443/bse/portal/user/anon/js_peid/11535052407933"

class EmslError(Exception):
    """
    Generic error thrown if some data obtained from the EMSL basis set exchange
    is not in the format expected
    """
    def __init__(self,message):
        super(EmslError, self).__init__(message)

def download_basisset(basisset, format="Gaussian94", contraction=True):
    """
    Obtain a basisset from the emsl library in gaussian format
    for all the elements which are available

    Return the downloaded basis set data as a string.
    """

    eltlist=" ".join(basisset['elements'])
    url=base_url+"/action/portlets.BasisSetAction/template/courier_content/panel/Main"
    url += "/eventSubmit_doDownload/true"

    params = {
        "bsurl": basisset['url'],
        "bsname": basisset['name'],
        "elts": eltlist,
        "format": format,
        "minimize": 'true'
    }
    if not contraction:
        params["minimize"] = 'false'

    ret = requests.get(url, params)
    if not ret.ok:
        raise EmslError("Error getting basis set " + basisset['name'] + " from emsl")
    soup = BeautifulSoup(ret.text,"lxml")

    return soup.pre.text

def _parse_list(string):
    """ Parse a list string into a list of strings"""
    if string[0] != "[" and string[-1] != "]":
        raise ValueError("Invalid list string: " + string)
    return [ elem.strip() for elem in string[1:-1].split(sep=",") ]

def _parse_basis_line(line):
    startstr = "new basisSet("
    endstr = ");"

    # Truncate the line
    line=line[line.find(startstr)+len(startstr):line.rfind(endstr)]

    # And split into argument strings (without leading and tailling '"')
    splitted=[ m[1:-1] for m in re.findall('"[^"]*"',line) ]

    if len(splitted) != 11:
        raise ValueError("Invalid emsl basis line: " + line + ", error: More params than expected.")

    try:
        elems = _parse_list(splitted[3])
    except ValueError as e:
        raise ValueError("Invalid emsl basis line: " + line + ", error: " + e.args[0])

    return {
        "url": splitted[0],
        "name": splitted[1],
        "type": splitted[2],
        "elements": elems,
        "type": splitted[4],
        "hasEcp": splitted[5],
        "hasSpin": splitted[6],
        "lastModifiedDate": splitted[7],
        "contributionPI": splitted[8],
        "contributorName": splitted[9],
        "bsAbstract": splitted[10]
    }

def download_basisset_list():
    """
    Download and parse the list of basis sets from emsl
    Returns a list of basis set dictionaries
    """
    ret = requests.get(base_url+"/panel/Main/template/content")
    if not ret.ok:
        raise EmslError("Error downloading list of basis sets from emsl")
    soup = BeautifulSoup(ret.text,"lxml")

    basis_sets=[] # The basis set list to return

    # Search expression for the basisSet definition lines:
    re_basdef = re.compile("^\W*basisSets\[[0-9]+\]\W*=\W*new\W*basisSet")

    # Search expression for the number of basis sets expected
    re_num = re.compile("numBasis\W*=\W*([0-9]+)")

    # Seek through all script blocks, which contain basis definitions:
    for script in soup.find_all("script", string=re.compile("basisSets\[[0-9]+\]\W*=")):
        lines = script.text.splitlines()

        numlines = [ re_num.search(l).group(1) for l in lines if re_num.search(l) ]
        if len(numlines) > 1:
            raise EmslError("The string describing the number of basis sets is found more than once.")
        expected_num_bases = int(numlines[0])

        try:
            bases=[ _parse_basis_line(l) for l in lines if re_basdef.match(l) ]
        except ValueError as e:
            raise EmslError(e.args[0])

        if (len(bases) != expected_num_bases):
            raise EmslError("Deviation between expected number of basis definitions and the actual number found.")
        basis_sets.extend(bases)
    return basis_sets

