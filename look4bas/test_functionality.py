import look4bas
import unittest


class TestFunctionality(unittest.TestCase):
    """
    Uttermost simple and basic test, just checking a few obtained coefficients
    """
    def test_emsl_def2svp(self):
        db = look4bas.Database()
        db.update()

        findings = db.search_basisset("^Def2-SVP$", regex=True, sources=["EMSL"])
        assert len(findings) == 1
        bset = findings[0]
        assert bset["name"] == "Def2-SVP"
        len(bset["atoms"]) == 72

        bset = db.lookup_basisset_full(bset)
        silicon = [at for at in bset["atoms"] if at["atnum"] == 14]
        assert len(silicon) == 1
        silicon = silicon[0]

        assert len(silicon["functions"]) == 8
        five_contracted = [fun for fun in silicon["functions"]
                           if len(fun["exponents"]) > 4]
        assert len(five_contracted) == 2

        assert five_contracted[0]["angular_momentum"] == 0
        assert five_contracted[0]["exponents"] == [
            6903.7118686, 1038.4346419, 235.87581480, 66.069385169, 20.247945761
        ]
        assert five_contracted[1]["angular_momentum"] == 1

    def test_ccrepo_ccpvdz(self):
        db = look4bas.Database()
        db.update()

        findings = db.search_basisset("^cc-pVDZ$", regex=True, sources=["ccrepo"])
        assert len(findings) == 1
        bset = findings[0]
        assert bset["name"] == "cc-pVDZ"
        len(bset["atoms"]) == 35

        bset = db.lookup_basisset_full(bset)
        germanium = [at for at in bset["atoms"] if at["atnum"] == 32]
        assert len(germanium) == 1
        germanium = germanium[0]

        assert len(germanium["functions"]) == 11
        five_contracted = [fun for fun in germanium["functions"]
                           if len(fun["exponents"]) == 5]
        assert len(five_contracted) == 1

        assert five_contracted[0]["angular_momentum"] == 2
        assert five_contracted[0]["exponents"] == [
            74.7620000, 21.3020000, 7.3436000, 2.5651000, 0.8197000
        ]
        assert five_contracted[0]["coefficients"] == [
            0.0257684, 0.1454421, 0.3713721, 0.4800002, 0.2896800
        ]
