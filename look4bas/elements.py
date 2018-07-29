#!/usr/bin/env python3
import collections


def iupac_list():
    """
    Build the list of elements per atomic number according to the IUPAC
    convention.

    The first entry of the list is "X", which is a dummy place holder.
    """
    Element = collections.namedtuple("Element", ["atnum", "symbol", "name"])

    elist = [
      Element(  0, "X",  "dummy"),
      Element(  1, "H" , "hydrogen"),       Element(  2, "He", "helium"),
      Element(  3, "Li", "lithium"),        Element(  4, "Be", "beryllium"),
      Element(  5, "B" , "boron"),          Element(  6, "C",  "carbon"),
      Element(  7, "N" , "nitrogen"),       Element(  8, "O",  "oxygen"),
      Element(  9, "F" , "fluorine"),       Element( 10, "Ne", "neon"),
      Element( 11, "Na", "sodium"),         Element( 12, "Mg", "magnesium"),
      Element( 13, "Al", "aluminium"),      Element( 14, "Si", "silicon"),
      Element( 15, "P" , "phosphorus"),     Element( 16, "S",  "sulphur"),
      Element( 17, "Cl", "chlorine"),       Element( 18, "Ar", "argon"),
      Element( 19, "K" , "potassium"),      Element( 20, "Ca", "calcium"),
      Element( 21, "Sc", "scandium"),       Element( 22, "Ti", "titanium"),
      Element( 23, "V" , "vanadium"),       Element( 24, "Cr", "chromium"),
      Element( 25, "Mn", "manganese"),      Element( 26, "Fe", "iron"),
      Element( 27, "Co", "cobalt"),         Element( 28, "Ni", "nickel"),
      Element( 29, "Cu", "copper"),         Element( 30, "Zn", "zinc"),
      Element( 31, "Ga", "gallium"),        Element( 32, "Ge", "germanium"),
      Element( 33, "As", "arsenic"),        Element( 34, "Se", "selenium"),
      Element( 35, "Br", "bromine"),        Element( 36, "Kr", "krypton"),
      Element( 37, "Rb", "rubidium"),       Element( 38, "Sr", "strontium"),
      Element( 39, "Y" , "yttrium"),        Element( 40, "Zr", "zirconium"),
      Element( 41, "Nb", "niobium"),        Element( 42, "Mo", "molybdenum"),
      Element( 43, "Tc", "technetium"),     Element( 44, "Ru", "ruthenium"),
      Element( 45, "Rh", "rhodium"),        Element( 46, "Pd", "palladium"),
      Element( 47, "Ag", "silver"),         Element( 48, "Cd", "cadmium"),
      Element( 49, "In", "indium"),         Element( 50, "Sn", "tin"),
      Element( 51, "Sb", "antimony"),       Element( 52, "Te", "tellurium"),
      Element( 53, "I" , "iodine"),         Element( 54, "Xe", "xenon"),
      Element( 55, "Cs", "caesium"),        Element( 56, "Ba", "barium"),
      Element( 57, "La", "lanthanum"),      Element( 58, "Ce", "cerium"),
      Element( 59, "Pr", "praseodymium"),   Element( 60, "Nd", "neodymium"),
      Element( 61, "Pm", "promethium"),     Element( 62, "Sm", "samarium"),
      Element( 63, "Eu", "europium"),       Element( 64, "Gd", "gadolinium"),
      Element( 65, "Tb", "terbium"),        Element( 66, "Dy", "dysprosium"),
      Element( 67, "Ho", "holmium"),        Element( 68, "Er", "erbium"),
      Element( 69, "Tm", "thulium"),        Element( 70, "Yb", "ytterbium"),
      Element( 71, "Lu", "lutetium"),       Element( 72, "Hf", "hafnium"),
      Element( 73, "Ta", "tantalum"),       Element( 74, "W", "tungsten"),
      Element( 75, "Re", "rhenium"),        Element( 76, "Os", "osmium"),
      Element( 77, "Ir", "iridium"),        Element( 78, "Pt", "platinum"),
      Element( 79, "Au", "gold"),           Element( 80, "Hg", "mercury"),
      Element( 81, "Tl", "thallium"),       Element( 82, "Pb", "lead"),
      Element( 83, "Bi", "bismuth"),        Element( 84, "Po", "polonium"),
      Element( 85, "At", "astatine"),       Element( 86, "Rn", "radon"),
      Element( 87, "Fr", "francium"),       Element( 88, "Ra", "radium"),
      Element( 89, "Ac", "actinium"),       Element( 90, "Th", "thorium"),
      Element( 91, "Pa", "protactinium"),   Element( 92, "U", "uranium"),
      Element( 93, "Np", "neptunium"),      Element( 94, "Pu", "plutonium"),
      Element( 95, "Am", "americium"),      Element( 96, "Cm", "curium"),
      Element( 97, "Bk", "berkelium"),      Element( 98, "Cf", "californium"),
      Element( 99, "Es", "einsteinium"),    Element(100, "Fm", "fermium"),
      Element(101, "Md", "mendelevium"),    Element(102, "No", "nobelium"),
      Element(103, "Lr", "lawrencium"),     Element(104, "Rf", "rutherfordium"),
      Element(105, "Db", "dubnium"),        Element(106, "Sg", "seaborgium"),
      Element(107, "Bh", "bohrium"),        Element(108, "Hs", "hassium"),
      Element(109, "Mt", "meitnerium"),     Element(110, "Ds", "darmstadtium"),
      Element(111, "Rg", "roentgenium"),    Element(112, "Cn", "copernicium"),
      Element(113, "Nh", "nihonium"),       Element(114, "Fl", "flerovium"),
      Element(115, "Mc", "moscovium"),      Element(116, "Lv", "livermorium"),
      Element(117, "Ts", "tennessine"),     Element(118, "Og", "oganesson"),
    ]
    return [dict(e._asdict()) for e in elist]
