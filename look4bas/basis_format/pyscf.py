from . import nwchem
from .. import elements
from warnings import warn

try:
    from pyscf.gto.basis.parse_nwchem import optimize_contraction, remove_zeros
except ImportError:
    def optimize_contraction(basis):
        return basis

    def remove_zeros(basis):
        return basis


def dumps(data, elem_list=elements.IUPAC_LIST, **kwargs):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in the format expected by the pyscf.gto.parse() function,
    which is identical to the NWChem format.

    Note, that as of now potential ECP data present in the basis
    is ignored.

    Example:

    >>> from pyscf import gto
    >>> from look4bas.basis_format.pyscf import dumps
    >>>
    >>> pyscf_basis_string = dumps(look4bas_data)
    >>> mol = gto.Mole()
    >>> mol.basis = {atom: gto.parse(pyscf_basis_string, atom)
                     for atom in ["O", "H", "He"]}
    """
    return nwchem.dumps(data, elem_list)


def convert_to(data, elem_list=elements.IUPAC_LIST):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and return a dictionary in the format expected by pscf.gto.Mole.

    Example:

    >>> from pyscf import gto
    >>> from look4bas.basis_format.pyscf import convert_to
    >>>
    >>> mol = gto.Mole()
    >>> mol.basis = convert_to(look4bas_data)
    """
    ret = {}
    for atom in data:
        symbol = elem_list[atom["atnum"]]["symbol"]

        bdef = []
        for fun in sorted(atom["functions"],
                          key=lambda x: x["angular_momentum"]):
            data_symbol = [fun["angular_momentum"]]

            if len(fun["coefficients"]) != len(fun["exponents"]):
                raise ValueError("Length of coefficients and length of exponents "
                                 "in contraction specification need to agree")
            for i, coeff in enumerate(fun["coefficients"]):
                exp = fun["exponents"][i]
                data_symbol.append([exp, coeff])
            bdef.append(data_symbol)

        bdef = optimize_contraction(bdef)
        bdef = remove_zeros(bdef)
        ret[symbol] = bdef

    for atom in data:
        if "ecp" in atom:
            warn(convert_to.__name__ + " currently ignores any ECP "
                 "definitions parsed.")
            break

    return ret
