#!/usr/bin/env python3
import look4bas

# Search for a basis set which has helium and beryllium
# and which matches the regular expression '^cc-pv.z'
# ignoring case.
db = look4bas.Database()
findings = db.search_basisset(pattern="^cc-pv.z", ignore_case=True,
                              regex=True, has_atnums=[2, 4])

if not findings:
    print("Found nothing")

# Pick the first finding
bset = findings[0]

# Print metadata
print("Basis set name:         ", bset["name"])
print("Basis set description:  ", bset["description"])

# Retrieve full basis set information online
bset = db.lookup_basisset_full(bset)

# Build a mapping from the atom number to the list
# of contracted basis functions
num_map = {at["atnum"]: at["functions"] for at in bset["atoms"]}

# Build mapping from the atom symbol to the list
# of contracted basis functions
element_list = look4bas.elements.iupac_list()
symbol_map = {element_list[atnum]["symbol"]: functions
              for atnum, functions in num_map.items()}

# Print basis set for the helium atom
print("Basis definition for helium:")
print(symbol_map["He"])
