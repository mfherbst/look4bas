import json
from look4bas import gaussian94
import os
import unittest


def get_reference(testcase):
    dir_of_this_file = os.path.dirname(__file__)
    json_file = os.path.join(dir_of_this_file, "testdata", testcase + ".json")
    with open(json_file) as f:
        return json.load(f)


def get_g94(testcase):
    dir_of_this_file = os.path.dirname(__file__)
    g94_file = os.path.join(dir_of_this_file, "testdata", testcase + ".g94")
    with open(g94_file) as f:
        return f.read()


class TestGaussian94(unittest.TestCase):
    """
    Test reading and writing g94 files
    """

    def test_loading(self):
        loaded = gaussian94.loads(get_g94("pc-2"))
        assert loaded == get_reference("pc-2")

    def test_identity_dump_load(self):
        ref = get_reference("pc-2")
        dumped = gaussian94.dumps(ref)
        loaded = gaussian94.loads(dumped)
        assert loaded == ref

    def test_identity_load_dump(self):
        ref = gaussian94.dumps(get_reference("pc-2"))
        loaded = gaussian94.loads(get_g94("pc-2"))
        dumped = gaussian94.dumps(loaded)
        assert dumped == ref
