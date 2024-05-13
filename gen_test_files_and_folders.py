import yaml
from pathlib import Path
import json
import random
import string
import exrex
import sys

big_arr = [i for i in range(5, 30)]

with open("rules.json") as rj:
    rules = json.loads(rj.read())
rules = rules.get("rules")
WD = Path.cwd()
test_dir = WD / "tests"
Path.mkdir(test_dir , exist_ok=True)

def create_path(path, value):
    tmp_final = {}
    end = path.split(".")[-1]
    path = path.split(".")[:-1]
    x = tmp_final
    for key in path:
        tmp = {}
        x[key] = tmp
        x = x[key]
    x[end] = value
    return yaml.dump(tmp_final)

def pattern_matching(path, pattern):
    # get one string that matches the value
    matching_pattern = exrex.getone(pattern)
    # generate a random string
    random_str = "".join(random.choices(string.ascii_letters, k=random.choices(big_arr)[0]))

    passing_str = create_path(path, matching_pattern)
    failing_str = create_path(path, random_str)
    return passing_str, failing_str

def allowed_values(path, allowed):
    # choose one of the allowed values
    passing_str = create_path(path, random.choices(allowed)[0])
    # mash up all the values
    failing_str = create_path(path, "".join(allowed))
    return passing_str, failing_str

def gte(path, str_val):
    # set the str_val to pass the test
    passing_str = create_path(path, str_val)

    # failing test
    failing_str = create_path(path, "2.0.0")
    return passing_str, failing_str

def string_match(path, string_val):
    # matching the string_val to pass test
    passing_str = create_path(path, string_val)
    # add a new line so that the string does not match
    failing_str = create_path(path, string_val+"\n")
    return passing_str, failing_str


def is_array(pattern = None):
    sample_arr = [i for i in range(1,random.choices(big_arr)[0])]
    # generate a yaml path between the length 2 and 8
    gen_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])
    array_schema = {
        "type": "array",
        "items": {
            "type": "string"
        }
    }
    failing_str = create_path(gen_path, {"name": "store_id", "schema": array_schema})
    passing_str = create_path(gen_path, {"name": exrex.getone("^[a-zA-Z][a-zA-Z]*(s|es)$"), "schema": array_schema})

    return passing_str, failing_str



def pattern_matching_property(pattern):
    sample_value = None

    # create a path that matches the pattern
    path_matching = ".".join([exrex.getone(pattern) for i in range(random.randint(2,9))])
    # create a path that does not match the pattern
    path_not_matching = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])

    passing_str = create_path(path_matching, sample_value)
    failing_str = create_path(path_not_matching, sample_value)

    return passing_str, failing_str

def is_date_time(pattern):
    pattern = "^[0-9]{4}-[0-1]{2}-[0-2]{2}T[0-1]{2}:[0-5]{2}:[0-5]{2}\.[0-9]{2}Z$"

    # generate snake cased property names for yaml files
    snake_case = "^[a-z_][a-z_0-9]*$"
    path_matching = ".".join([exrex.getone(snake_case) for i in range(random.randint(2,9))]) + ".created_at"
    path_not_matching = ".".join([exrex.getone(snake_case) for i in range(random.randint(2,9))]) + ".check"

    date_time_obj = {
        "type": "string",
        "format": "date-time"
    }

    passing_str = create_path(path_matching, date_time_obj)
    failing_str = create_path(path_not_matching, date_time_obj)

    return passing_str, failing_str



# key name, pattern
def check_keys_pattern(key_name, pattern, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"

    new_key = exrex.getone(pattern)

    if id == "B142" or id == "B143" or id == "B146":
    # shallow keys that match the pattern
        path_matching = {"/"+new_key: "sample" for i in range(random.randint(2, 9))}
        path_not_matching = {"/"+"".join(random.choices(string.ascii_letters, k=random.choices(big_arr)[0])): "sample" for i in range(random.randint(2, 9))}
    else:
        path_matching = {new_key: "sample" for i in range(random.randint(2, 9))}
        path_not_matching = {"".join(random.choices(string.ascii_letters, k=random.choices(big_arr)[0])): "sample" for i in range(random.randint(2, 9))}

    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)
    return passing_str, failing_str

# key name and the list
def check_keys_list(key_name, lst, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"
    path_matching = {x: "sample" for x in lst}
    path_not_matching = {f"{x}xx": "sample" for x in lst}
    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)
    return passing_str, failing_str

def check_keys_pattern_list(key_name, lst, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"
    path_matching = {exrex.getone(x): "sample" for x in lst}
    path_not_matching = {f"{x}xx": "sample" for x in lst}
    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)
    return passing_str, failing_str

# key name and pattern for shallow matching
def check_keys_value(key_name, pattern, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"
    # append / if id = 142 or 143
    if id == "B142" or id == "B143":
        # shallow keys that match the pattern
        path_matching = {"/"+exrex.getone(pattern): "sample" for i in range(random.randint(2, 9))}
        path_not_matching = {"/"+"".join(random.choices(string.ascii_letters, k=random.choices(big_arr)[0])): "sample" for i in range(random.randint(2, 9))}
    else:
        # shallow keys that match the pattern
        path_matching = {exrex.getone(pattern): "sample" for i in range(random.randint(2, 9))}

        path_not_matching = {"".join(random.choices(string.ascii_letters, k=random.choices(big_arr)[0])): "sample" for i in range(random.randint(2, 9))}

    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)
    return passing_str, failing_str

def check_keys_pattern_inverse(key_name, pattern, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"

    # keys that match the pattern are failures
    path_not_matching = {exrex.getone(pattern): "sample" for i in range(random.randint(2,9))}
    path_matching = {"/"+"".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) : "sample" for i in range(random.randint(2,9))}
    
    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)
    
    return passing_str, failing_str

def check_keys_B129(key_name, lst, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"
    # choose random 3 common field types
    path_matching = {exrex.getone(x) : "sample" for x in random.choices(lst, k=3)}
    path_not_matching = {exrex.getone(x).capitalize() : "sample" for x in random.choices(lst, k=3)}
    
    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)

    return passing_str, failing_str

def check_keys_B157(key_name, pattern, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+".properties.x"
    path_matching = { "type": "integer", "format": "bigint"}
    path_not_matching = {"type": "integer"}

    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)
    return passing_str, failing_str

def check_keys_B111(key_name, pattern, id):
    key_name = ".".join([exrex.getone(x) for x in key_name.split(".")])
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_name}"
    # choose random 3 common field types
    path_matching = [exrex.getone(pattern) for x in range(random.randint(3,5))]
    path_not_matching = ["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(3,5))]
    
    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)

    return passing_str, failing_str

def check_array_pattern(key_str, pattern, id):
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])+f".{key_str}"
    
    path_matching = [exrex.getone(pattern) for x in range(random.randint(3,5))]
    path_not_matching = ["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(3,5))]
    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)

    return passing_str, failing_str    

def check_keys_value(key_str, config, id):
    generic_path = ".".join(["".join(random.choices(string.ascii_lowercase, k=random.choices(big_arr)[0])) for i in range(random.randint(2,9))])
    
    partitioned_key = key_str.split(".")[:-1]
    key_to_match = key_str.split(".")[-1]

    val = config.get("value")
    arr = config.get("arr")
    gte = config.get("gte")
    lte = config.get("lte")

    sibling = config.get("required_sibling")
    type_of_match = type(config.get("sibling_requirement"))
    requirement_to_match = config.get("sibling_requirement")
    tmp = None
    if val:
        tmp = val
    elif arr:
        tmp = arr[0]
    elif gte:
        tmp = gte
    elif lte:
        tmp = lte
    
    sibling_pass = None
    sibling_fail = None
    if type_of_match is str:
        sibling_pass = requirement_to_match
        sibling_fail = requirement_to_match + "X"
    elif type_of_match is int or type_of_match is float:
        sibling_pass = requirement_to_match
        sibling_fail = requirement_to_match + 1
    elif type_of_match is list:
        sibling_pass = requirement_to_match[0]
        sibling_fail = "".join(requirement_to_match)
    
    path_matching = {key_to_match: tmp, sibling: sibling_pass}
    path_not_matching = {key_to_match: tmp, sibling: sibling_fail}

    passing_str = create_path(generic_path, path_matching)
    failing_str = create_path(generic_path, path_not_matching)

    return passing_str, failing_str


# key value pair for generating tests according to keys in the rules.json file
path_test = {
    "pattern": pattern_matching,
    "allowed_values": allowed_values,
    "string_match": string_match,
    "gte": gte
}

property_config = {
    "pattern": pattern_matching_property,
    "is_array": is_array,
    "is_date_time": is_date_time
}

key_config = {
    "check_keys_pattern": check_keys_pattern,
    "check_keys_list": check_keys_list,
    "check_keys_value": check_keys_value,
    "check_keys_pattern_inverse": check_keys_pattern_inverse,
    "check_keys_pattern_list": check_keys_pattern_list
}

array_config = {
    "check_array_pattern": check_array_pattern,
}

key_value_config = {
    "check_keys_value": check_keys_value
}

def gen_test_files():
    # gen yaml files for testing
    for rule in rules:
        id = rule.get("id")
        severity = rule.get("severity")
        description = rule.get("description")
        if rule.get("implementation"):
            continue
        print(f"Creating tests for rule: {id}")
        # create a folder for the rule with id
        Path.mkdir(test_dir / id, exist_ok=True)
        
        for path in rule.get("paths"):
            required_path = path.get("required_path")
            properties = path.get("properties")
            key_name = path.get("key_name")
            array_name = path.get("array_name")
            key_value = path.get("key_value")

            if not required_path:
                generic_file_name = ""
            else:
                # create a filename from absolute path to the value
                generic_file_name = "-".join(required_path.split("."))
            # if the required path must exist
            if len(path.get("checks")) == 0:
                # create a path in the yaml file
                passing_file_name = generic_file_name + "_passing_test.yaml"
                with open(test_dir/id/passing_file_name, "w") as pt:
                    pt.write(create_path(required_path, None))
            
            for check in path.get("checks"):
                key = check.get("name")
                value = check.get("value")

                if required_path:
                    # path exists
                    func =  path_test.get(key)
                    passing_test, failing_test = func(required_path, value)
                    # create file names
                    passing_file_name = generic_file_name + "_passing_test.yaml"
                    failing_file_name = generic_file_name + "_failing_test.yaml"
                    # create file content
                    with open(test_dir/id/passing_file_name, "w") as pt:
                        pt.write(passing_test)
                    with open(test_dir/id/failing_file_name, "w") as ft:
                        ft.write(failing_test)
                # checks for the properties
                elif properties:
                    generic_file_name = key
                    func = property_config.get(key)
                    passing_test, failing_test = func(value)
                    passing_file_name = generic_file_name + "_passing_test.yaml"
                    failing_file_name = generic_file_name + "_failing_test.yaml"

                elif key_name:
                    generic_file_name = id
                    func = key_config.get(key)
                    passing_test, failing_test = func(key_name, value, id)
                    passing_file_name = generic_file_name + f"_passing_test_{'_'.join([exrex.getone(x) for x in key_name.split('.')])}.yaml"
                    failing_file_name = generic_file_name + f"_failing_test_{'_'.join([exrex.getone(x) for x in key_name.split('.')])}.yaml"

                elif array_name:
                    generic_file_name = id
                    func = array_config.get(key)
                    passing_test, failing_test = func(array_name, value, id)
                    passing_file_name = generic_file_name + f"_passing_test_{'_'.join([exrex.getone(x) for x in array_name.split('.')])}.yaml"
                    failing_file_name = generic_file_name + f"_failing_test_{'_'.join([exrex.getone(x) for x in array_name.split('.')])}.yaml"

                elif key_value:
                    generic_file_name = id
                    func = key_value_config.get(key)
                    passing_test, failing_test = func(key_value, value, id)
                    passing_file_name = generic_file_name + f"_passing_test_{'_'.join([exrex.getone(x) for x in key_value.split('.')])}.yaml"
                    failing_file_name = generic_file_name + f"_failing_test_{'_'.join([exrex.getone(x) for x in key_value.split('.')])}.yaml"
                else:
                    continue
                with open(test_dir/id/passing_file_name, "w") as pt:
                    pt.write(passing_test)
                with open(test_dir/id/failing_file_name, "w") as ft:
                    ft.write(failing_test)

# generate -output.json files for validating
if __name__ == "__main__":
    gen_test_files()