from . import orca
from ..testdata import get_json
import unittest
import re


# The reference result for the Si section of pc-2
# in Orca format
reference_si = """
 S    9
  1  120040.0000000     0.000160750000
  2   17991.0000000     0.00124720000
  3    4094.8000000     0.00650400000
  4    1159.6000000     0.0266650000
  5     378.0000000     0.0888160000
  6     135.9300000     0.229320000
  7      52.4110000     0.400250000
  8      20.9270000     0.338280000
  9       7.7130000     0.0655120000
 S    9
  1   17991.0000000    -6.84030000E-07
  2    4094.8000000    -2.11240000E-06
  3    1159.6000000    -6.91570000E-05
  4     378.0000000    -0.000480800000
  5     135.9300000    -0.00416940000
  6      52.4110000    -0.0176740000
  7      20.9270000    -0.0428910000
  8       7.7130000     0.0453680000
  9       3.1604000     0.139040000
 S    9
  1    4094.8000000    -3.98970000E-06
  2    1159.6000000    -5.02030000E-05
  3     378.0000000    -0.000575530000
  4     135.9300000    -0.00415240000
  5      52.4110000    -0.0204370000
  6      20.9270000    -0.0469980000
  7       7.7130000     0.0439860000
  8       3.1604000     0.339570000
  9       1.2348000     0.350380000
 S    1
  1       0.2677500     1.00000000
 S    1
  1       0.0940670     1.00000000
 P    7
  1     677.1300000     0.00109250000
  2     160.6700000     0.00896010000
  3      51.5850000     0.0447440000
  4      18.9480000     0.147480000
  5       7.6163000     0.314800000
  6       3.1317000     0.413390000
  7       1.2703000     0.264400000
 P    7
  1     160.6700000     7.90140000E-06
  2      51.5850000    -0.000136130000
  3      18.9480000    -0.000903780000
  4       7.6163000    -0.00558630000
  5       3.1317000    -0.0101410000
  6       1.2703000     0.0186610000
  7       0.4333200     0.288900000
 P    1
  1       0.1608800     1.00000000
 P    1
  1       0.0548830     1.00000000
 D    1
  1       1.6800000     1.00000000
 D    1
  1       0.3800000     1.00000000
 F    1
  1       0.5400000     1.00000000
"""


# The reference result for the C section of pc-2
# in Orca format
reference_c = """
 S    7
  1    7857.1000000     0.000568250000
  2    1178.7000000     0.00439150000
  3     268.3200000     0.0225040000
  4      75.9480000     0.0866530000
  5      24.5590000     0.244050000
  6       8.6212000     0.441480000
  7       3.1278000     0.353320000
 S    7
  1    1178.7000000    -5.94920000E-07
  2     268.3200000    -6.27480000E-05
  3      75.9480000    -0.000757730000
  4      24.5590000    -0.00733080000
  5       8.6212000    -0.0389320000
  6       3.1278000    -0.0889080000
  7       0.8220200     0.216890000
 S    1
  1       0.3301700     1.00000000
 S    1
  1       0.1146300     1.00000000
 P    4
  1      33.7750000     0.00602940000
  2       7.6766000     0.0432280000
  3       2.2357000     0.163010000
  4       0.7644700     0.365040000
 P    1
  1       0.2623200     1.00000000
 P    1
  1       0.0846380     1.00000000
 D    1
  1       1.4000000     1.00000000
 D    1
  1       0.4500000     1.00000000
 F    1
  1       0.9500000     1.00000000
"""


class TestOrca(unittest.TestCase):
    """
    Test dumping Orca basis section
    """
    def test_dumps(self):
        data = get_json("pc-2")
        dump = orca.dumps(data)

        lines = dump.split("\n")
        assert lines[0] == "%basis"
        assert lines[-1] == "end"

        # Silicon
        re_si = re.compile(r"NewGTO 14\n(.*?)end", re.MULTILINE + re.DOTALL)
        part_si = re.search(re_si, dump)
        assert part_si
        assert reference_si.strip() == part_si.group(1).strip()

        # Carbon
        re_c = re.compile(r"NewGTO 6\n(.*?)end", re.MULTILINE + re.DOTALL)
        part_c = re.search(re_c, dump)
        assert part_c
        assert reference_c.strip() == part_c.group(1).strip()