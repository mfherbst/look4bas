#!/usr/bin/env python3

import pyscf
import look4bas
import look4bas.basis_format
import pyscf.geomopt.berny_solver

# Search for basis set
db = look4bas.Database()
db.update()
findings = db.search_basisset("^pc-2$", regex=True,
                              has_atnums=[1, 8, 32])
assert len(findings) == 1
bset = db.lookup_basisset_full(findings[0])

# Setup water HF geometry optimisation in pyscf
mol = pyscf.gto.Mole()
mol.atom = "H 1 0 0; H 0 1 0; O 0 0 0"
mol.basis = look4bas.basis_format.convert_to("pyscf", bset["atoms"])
mol.build()

mf = pyscf.scf.RHF(mol)
mol_eq = pyscf.geomopt.berny_solver.optimize(mf)
