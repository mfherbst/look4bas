import json
import os


def get_json(testcase):
    dir_of_this_file = os.path.dirname(__file__)
    json_file = os.path.join(dir_of_this_file, testcase + ".json")
    with open(json_file) as f:
        return json.load(f)


def get_g94(testcase):
    dir_of_this_file = os.path.dirname(__file__)
    g94_file = os.path.join(dir_of_this_file, testcase + ".g94")
    with open(g94_file) as f:
        return f.read()
