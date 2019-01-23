#!/usr/bin/env python3
import look4bas
import json

# Search for Def2-SVP
db = look4bas.Database()
findings = db.search_basisset(pattern="^Def2-SVP$", regex=True)

if not findings or len(findings) > 1:
    print("Could not find Def2-SVP")

# Retrieve full basis set information online
bset = db.lookup_basisset_full(findings[0])

# Build a mapping from the atom number to the list
# of ecp definitions
num_map = {at["atnum"]: at["ecp"] for at in bset["atoms"] if "ecp" in at}

# Build mapping from the atom symbol to the list
# of ecp definitions
element_list = look4bas.elements.iupac_list()
symbol_map = {element_list[atnum]["symbol"]: functions
              for atnum, functions in num_map.items()}

# Print ecp definiton for Hafnium
print("ECP definition for Hafnium:")
print(json.dumps(symbol_map["Hf"], indent=2, sort_keys=True))
