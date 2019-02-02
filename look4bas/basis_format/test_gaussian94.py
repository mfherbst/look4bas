from . import gaussian94
from ..testdata import get_g94, get_json
import unittest


class TestGaussian94(unittest.TestCase):
    """
    Test reading and writing g94 files
    """

    def test_loading_pc2(self):
        loaded = gaussian94.loads(get_g94("pc-2"))
        assert loaded == get_json("pc-2")

    def test_identity_dump_load_pc2(self):
        ref = get_json("pc-2")
        dumped = gaussian94.dumps(ref)
        loaded = gaussian94.loads(dumped)
        assert loaded == ref

    def test_identity_load_dump_pc2(self):
        ref = gaussian94.dumps(get_json("pc-2"))
        loaded = gaussian94.loads(get_g94("pc-2"))
        dumped = gaussian94.dumps(loaded)
        assert dumped == ref
