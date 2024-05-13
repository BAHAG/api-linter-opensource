import re
import json
import subprocess
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
import yaml
from yaml.resolver import Resolver
import requests
# contains all the references that match "country" and "language"
LANG_COUNTRY_META_REF = set()
# contains the name of the path parameter for iso-3166, for country codes
COUNTRY_PARAM_NAME = None

# contains data for all refrences, external spec file as dict or the computation if ref_exists as true and false
EXTERNAL_DATA = {}
# api key to download external sources
API_KEY = os.getenv("SWAGGERHUB_API_KEY")
SWAGGER_HEADERS = {
    "Accept": "application/yaml",
    "Authorization": API_KEY
}

# remove resolver entries for On/Off/Yes/No
for ch in "OoYyNn":
    if len(Resolver.yaml_implicit_resolvers[ch]) == 1:
        del Resolver.yaml_implicit_resolvers[ch]
    else:
        Resolver.yaml_implicit_resolvers[ch] = [x for x in
                Resolver.yaml_implicit_resolvers[ch] if x[0] != 'tag:yaml.org,2002:bool']

"""START: Utility funcs for spec file and rules file"""

# get api specification file
def get_spec(filename):
    yaml_file = None
    with open(filename) as yf:
        try:
            yaml_file = yaml.safe_load(yf)
        except yaml.YAMLError as exc:
            print(exc)
    return yaml_file

# get rules from json file as a dictionary
def get_rules(filename):
    env_path = str(Path.home()) + "/.env"
    # set environment variables
    load_dotenv(env_path)
    rules = None
    with open(filename) as jf:
        try:
            rules = json.load(jf)
        except json.JSONDecodeError as exc:
            print(exc)
    return rules

""" END """

# utility function to parse and get the line number of required paths
def parse_required_path(path, spec):
    spec_file_name = os.getenv("SPEC_FILE")
    if spec is None:
        return None, None, None
    # setting path for yq utility tool
    yq_path = "."+path

    path = path.split(".")
    common = path[:-1]
    last = path[-1]

    tmp_spec = spec

    for item in common:
        tmp_spec = tmp_spec.get(item)
        if not tmp_spec:
            return None, None, last
    
    tmp_spec = tmp_spec.get(last)
    
    if not tmp_spec:
        return None, None, last
    
    # get line number by using the yq utility tool
    line_num = subprocess.run(["yq", f"{yq_path} | key | line", spec_file_name], capture_output=True)
    line_num = line_num.stdout.decode().strip()

    return tmp_spec, line_num, last

# write logs to output file
def write_logs(output_fmt, output_file_name):
    with open(output_file_name+f"-output.{output_fmt}", "w") as of:
        if output_fmt=="json":
            print(error_logger.get_logs_json())
            of.write(error_logger.get_logs_json())
        elif output_fmt == "yaml":
            print(error_logger.get_logs_yaml())
            of.write(error_logger.get_logs_yaml())

# recursion handler + logger for checking version mismatch
def check_version_deep(spec, yq_path, pattern, logger, **kwargs):
    for key, value in spec.items():
        tmp = f'."{key}"'
        if key == "version" and value.get("default") and not re.match(pattern, value.get("default")):
            print(yq_path+tmp+".default")
            line_num = get_line_number_key(yq_path+tmp+".default", logger)
            # log the result to logger
            logger.log_with_line_number(line_num, "ERROR", "Version mismatch in /health and info.version", None)
        
        if type(value) is dict:
            check_version_deep(value, yq_path + tmp, pattern, logger, **kwargs)

# utility function to check the version number in health and info.version
def check_version(spec, logger):
    try:
        info_version = spec.get("info").get("version")

        # if health endpoint does not exist return
        health = spec.get("paths").get("/health")
        if not health:
            return
        
        check_version_deep(health, ".paths./health", info_version, logger)
    except:
        return


# recursion helper, checks if an array is an object
def check_example_array_helper(arr, yq_path, logger, spec):
    for i, item in enumerate(arr):
        tmp = f".[{i}]"
        if item is dict:
            check_example(item, yq_path+tmp, logger, spec)

def check_ref_examples_object(spec, yq_path, logger, spec_duplicate):
    # has an example/ examples
    # /definition/Health = {type:.., properties:..}
    props = spec.get("properties")
    if not props:
        return
    
    for key, value in props.items():
        tmp = f".properties.{key}"
        if value.get("type") == "array":
            itms = value.get("items")
            # items either have a type or a ref
            itm_type = itms.get("type")
            ref_type = itms.get("$ref")

            if itm_type and not (value.get("example") or value.get("examples") or value.get("default") or itms.get("examples") or itms.get("example") or itms.get("default")):
                line_num = get_line_number_key(yq_path+tmp, logger)
                logger.log_missing_example(line_num, "Example not found for a schema in a HTTP response", yq_path+tmp)
            if ref_type:
                call_check_ref_example(spec_duplicate, ref_type, yq_path, logger)
            continue
        
        if value.get("$ref"):
            call_check_ref_example(spec_duplicate, value.get("$ref"), yq_path, logger)
            continue
        
        if value.get("type") == "object":
            check_ref_examples_object(value, yq_path+tmp, logger, spec_duplicate)
            continue
        if value.get("type") == "boolean":
            continue
        
        if not (value.get("example") or value.get("examples") or value.get("default") or value.get("enum")):
            line_num = get_line_number_key(yq_path+tmp, logger)
            logger.log_missing_example(line_num, "Example not found for a schema in a HTTP response", yq_path+tmp)

def check_ref_examples(spec_duplicate, ref_path, yq_path, logger):
    if not spec_duplicate:
        return
    tmp = spec_duplicate

    for path in ref_path:
        tmp = tmp.get(path)
        # path is not valid
        if not tmp:
            return
    
    schema_type = tmp.get("type")

    if schema_type == "array":
        items = tmp.get("items")

        # it has either primitive types or reference to an object
        item_type = items.get("type")
        ref_type = items.get("$ref")
        # item type can be objects
        if item_type == "object":
            check_ref_examples_object(tmp.get("items"), yq_path+".items", logger, spec_duplicate)
        elif item_type:
            # check for example/examples
            if not (value.get("example") or value.get("examples") or value.get("default") or items.get("examples") or items.get("example") or items.get("default")):
                num_path = yq_path + ".items"
                line_num = get_line_number_key(num_path, logger)
                logger.log_missing_example(line_num, "Example not found for a schema in a HTTP response", yq_path)
        
        if ref_type:
            # call_check_ref_example
            call_check_ref_example(spec_duplicate, ref_type, yq_path, logger)
            
    elif schema_type == "object":
        # call check_ref_examples_object
        check_ref_examples_object(tmp, yq_path, logger, spec_duplicate)

def call_check_ref_example(spec, ref, yq_path, logger):
    if not ref:
        return
    # check external ref
    if ref.find("https://") != -1:
        # https://...#/definitions/Health
        ref = ref.split("#")
        external_spec = EXTERNAL_DATA.get(ref[0])
        yq_path = "."+".".join(ref[1].split("/"))
        check_ref_examples(external_spec, ref[1].split("/"), yq_path, logger)
    # check internal ref
    else:
        ref = parse_internal_refs(ref)
        yq_path = "." + ".".join(ref)
        check_ref_examples(spec, ref, yq_path, logger)

def check_example_helper(spec, yq_path, logger, spec_duplicate):
    if type(spec) is not dict:
        return
    tmp = spec.get("content")
    if not tmp:
        return

    tmp = tmp.get("application/json")
    if not tmp:
        return

    tmp = tmp.get("schema")
    if not tmp:
        return
    
    if tmp.get("type") == "array":
        ref = tmp.get("items").get("$ref")
    elif tmp.get("type") == "object":
        ref = None
        check_ref_examples_object(tmp, yq_path+".content.application/json.schema", logger, spec_duplicate)
    else:
        ref = tmp.get("$ref")
    call_check_ref_example(spec_duplicate, ref, "", logger)

# recursively check if example exists and point to the helper function for validation
def check_example(spec, yq_path, logger, spec_duplicate):
    if not spec:
        return
    for key, value in spec.items():
        tmp = f'."{key}"'
        if f"{key}" == "200":
            check_example_helper(value, yq_path+tmp, logger, spec_duplicate)
            continue
        if type(value) is dict:
            check_example(value, yq_path + tmp, logger, spec_duplicate)
        elif type(value) is list:
            check_example_array_helper(value, yq_path, logger, spec_duplicate)
"""START: Utility functions for extracting metadata"""

# find enum inside country-code and language-id path parameters
def deep_find_enum(spec, logger, log_key):
    enum_exists = False
    for key, value in spec.items():
        if key == "enum":
            if value:
                # enum is always an array
                logger.add_metadata(log_key, value)
                logger.add_metadata(log_key+"-length", len(value))
                return True
        if type(value) == dict:
            enum_exists = deep_find_enum(value, logger, log_key)
    return enum_exists

# extract enums for each path parameter
def extract_enum(spec, logger):
    remove_from_LANG_COUNTRY_META_REF = set()
    # loop through the set
    for lang_or_country, country_flag in LANG_COUNTRY_META_REF:
        # matches any schema/parameter with "country" and "language"
        if lang_or_country.lower().find("country") != -1:
            log_key = "supported-countries"
        else:
            log_key = "supported-languages"

        # check if ref is external
        if lang_or_country.find("https://") != -1:
            if not API_KEY:
                print("\tSwagger Hub API key not found. Skipping checks for external refs")
                continue
            # download the yaml specification file from swagger hub, http://smth#/components/x/y
            url, x = lang_or_country.split("#")
            # internal ref requires # as the first char
            x = parse_internal_refs("#"+x)

            if not EXTERNAL_DATA.get(url):
                r = requests.get(url, headers=SWAGGER_HEADERS)
                if r.headers.get('content-type').find('yaml') != -1:
                    # get yaml file r.content.decode()
                    tmp = yaml.safe_load(r.content.decode())
            else:
                tmp = EXTERNAL_DATA[url]["data"]
        else:
            # parses #/components/x/y => [components, x, y]
            x = parse_internal_refs(lang_or_country)

            tmp = spec
        
        # navigate to required model/schema
        for tmp_path in x:
            tmp = tmp.get(tmp_path)
        
        if tmp is None:
            return
        
        # skip if country flag is set and the name is not the same as the path parameter
        if country_flag and tmp.get("name") != COUNTRY_PARAM_NAME and tmp.get("name").replace("_", "-") != COUNTRY_PARAM_NAME:
            remove_from_LANG_COUNTRY_META_REF.add((lang_or_country, country_flag))
            continue
        #print(deep_find_enum(tmp, logger, log_key), log_key, tmp)
        # tmp has the model/schema/parameter of the country-code or language-id
        enum_exists = deep_find_enum(tmp, logger, log_key)
        #print(enum_exists, log_key, tmp)
        if not enum_exists:
            line_number = get_line_number_key("."+".".join(x), logger)
            logger.log_with_line_number(line_number, "WARN", f"{x[-1]} should have an enum field", None)
    # remove country refs if the name is not the same as path parameter
    for val in remove_from_LANG_COUNTRY_META_REF:
        LANG_COUNTRY_META_REF.remove(val)

# find ref inside path parameter(object)
def extract_deep_find_ref(spec):
    ref = None
    for key, value in spec.items():
        if type(value) is dict:
            ref = extract_deep_find_ref(value)
        if key == "$ref":
            ref = value
    return ref

#extract parameters if they match "country" or "language
def extract_path_parameter_refs(spec, logger):
    # .paths contains all the endpoints
    paths = spec.get("paths")
    if not paths:
        print("\tNo endpoints detected")
        return
    # change the global country_param_name variable
    global COUNTRY_PARAM_NAME
    i = 0
    for path, path_obj in paths.items():
        if i > 0:
            break
        # skip if the endpoint is a health endpoint
        if path == "/health":
            continue
        # get list of url parameters
        param_list = path_obj.get("parameters")
        # sometimes the parameters are listed inside of http verbs
        if not param_list:
            http_verbs = ["post", "get", "delete", "patch"]
            for verb in http_verbs:
                if path_obj.get(verb):
                    param_list = path_obj.get(verb).get("parameters")
                    break
        # if there is still no list of parameters check all paths
        if not param_list:
            continue
        i += 1
        # find the first matching country path param
        for country_name in path.split("/"):
            if re.match("country", country_name):
                COUNTRY_PARAM_NAME = country_name
                break
        
        for param in param_list:
            ref = param.get("$ref")

            # if parameter is a ref and has a country in the shema/param model
            if ref and ref.lower().find("country") != -1:
                LANG_COUNTRY_META_REF.add((ref, True))
                continue
            # if parameter is a ref and has a language in the shema/param model
            if ref and ref.lower().find("language") != -1:
                LANG_COUNTRY_META_REF.add((ref, False))
                continue

            # if the parameter is an object and represents country code
            if param.get("name") and param.get("name") == COUNTRY_PARAM_NAME:
                # find enum
                enum_exists = deep_find_enum(param, logger, "supported-countries")
                # if enum exists the value has already been set
                if not enum_exists:
                    # if enum does not exist find a ref
                    country_ref = extract_deep_find_ref(param)
                    if not country_ref:
                        line_number = get_line_number_key(f".paths.{path}.param", logger)
                        logger.log_with_line_number(line_number, "WARN", f"{param.get('name')} should have an enum field", None)
                    else:
                        # if ref exists, no need to check for COUNTRY_PARAM_NAME so skip with False
                        LANG_COUNTRY_META_REF.add((country_ref, False))
            
            # if the parameter is an object and represents language id
            if param.get("name") and re.match("language", param.get("name")):
                # find enum
                enum_exists = deep_find_enum(param, logger, "supported-languages")
                # if enum exists the value has already been set
                if not enum_exists:
                    # if enum does not exist find a ref
                    language_ref = extract_deep_find_ref(param)
                    if not language_ref:
                        line_number = get_line_number_key(f".paths.{path}.param", logger)
                        logger.log_with_line_number(line_number, "WARN", f"{param.get('name')} should have an enum field", None)
                    else:
                        # if ref exists, no need to check for COUNTRY_PARAM_NAME so skip with False
                        LANG_COUNTRY_META_REF.add((language_ref, False))            

def extract_metadata(spec, logger, req_paths):
    for pth in req_paths:
        value, _, bq_path = parse_required_path(pth, spec)
        logger.add_metadata(bq_path, value)
    
    extract_path_parameter_refs(spec, logger)
    extract_enum(spec, logger)

    country_count = 0
    lang_count = 0

    for tmp in LANG_COUNTRY_META_REF:
        if tmp[0].find("country") != -1:
            country_count += 1
        if tmp[0].find("lang") != -1:
            lang_count += 1

    if country_count == 0:
        logger.add_metadata("supported-countries", ["all"])
        logger.add_metadata("supported-countries-length", 1)
    
    if lang_count == 0:
        logger.add_metadata("supported-languages", ["N/A"])
        logger.add_metadata("supported-languages-length", 1)
    
    if not logger.check_internal_metadata("supported-countries"):
        logger.add_metadata("supported-countries", None)
        logger.add_metadata("supported-countries-length", 0)

    if not logger.check_internal_metadata("supported-languages"):
        logger.add_metadata("supported-languages", None)
        logger.add_metadata("supported-languages-length", 0)
"""END"""

"""START: Utility functions for performing checks on required_path"""

# check if the pattern matches the property value
def pattern_matching(pattern, property_):
    if re.match(pattern, property_):
        return True
    return False

# check if the value in spec file is matches one of the predefined values
def allowed_values(all_values, value):
    if value in all_values:
        return True
    return False

# check if semantic versioning is >= version specified in the rules.json
def gte(check, spec_value):
    check = int("".join(check.split(".")))
    try:
        spec_value = int("".join(spec_value.split(".")))

        if spec_value >= check:
            return True
        return False
    except:
        return False

# check if the value matches the predifined string
def string_match(check, spec_value):
    if check == spec_value:
        return True
    else:
        return False
"""END"""

"""START: Utility functions to get the line number for a key or value in a yaml document"""

# get the line number of a path in spec file using yq utility
def get_line_number_key(yq_path, logger):
    # filename is saved to .env file for easy access
    spec_file_name = os.getenv("SPEC_FILE")
    # query for line number
    line_num = subprocess.run(["yq", f"{yq_path} | key | line", spec_file_name], capture_output=True)
    
    int_line = line_num.stdout.decode().strip()
    try:
        int_line = int(int_line)
        return int_line
    except:
        # log the line number
        err = line_num.stderr.decode().strip()
        print(err)
        tmp = err.split("line")
        # log the error and exit the program
        if len(tmp) > 1:
            line_num = int(tmp[1].strip().split(":")[0])
            # log the usage of characters not supported by yq
            logger.log_invalid_path(line_num, "Use of json structure is not supported")
            logger.print_and_save_logs()
            sys.exit(1)
    
# get the line number of the value, useful in cases of finding line number of arrays in json
def get_line_number_value(yq_path, logger):
    spec_file_name = os.getenv("SPEC_FILE")
    line_num = subprocess.run(["yq", f"{yq_path} | line", spec_file_name], capture_output=True)
    int_line = line_num.stdout.decode().strip()
    try:
        int_line = int(int_line)
        return int_line
    except:
        # log the line number
        err = line_num.stderr.decode().strip()
        print(err)
        tmp = err.split("line")
        # log the error and exit the program
        if len(tmp) > 1:
            line_num = int(tmp[1].strip().split(":")[0])
            # log the usage of characters not supported by yq
            logger.log_invalid_path(line_num, "Use of json structure is not supported")
            logger.print_and_save_logs()
            sys.exit(1)
"""END"""

"""START: Utility functions for performing checks on properties on a yaml document"""

# recursively check if the yaml key has an array as it's value
# if it does not match snake case or is not plural log it
def check_deep_array(spec, yq_path, message, severity, logger, id, pattern, idx, log_flag):
    for key, value in spec.items():
        tmp = f'."{key}"'
        if type(value) is dict:
            if value.get("schema") and value.get("schema").get("type") == "array":
                # check if name exists inside schema first
                if value.get("name") and not re.match(pattern, value.get("name")):
                    tmp = yq_path + tmp + ".name"
                    message_ = message
                    line_num = get_line_number_key(tmp, logger)
                    logger.log_with_line_number_key(line_num, severity, message_, id, tmp)
            else:
                check_deep_array(value, yq_path+tmp, message, severity, logger, id, pattern, idx, log_flag)
        elif type(value) is list:
            deep_check_generic_array(spec, yq_path, message, severity, logger, id, key, pattern, is_array, idx, log_flag)

# stub function to call check_deep_array
def is_array(spec, yq_path, message, severity, logger, id, pattern):
    pattern = "^[a-zA-Z][a-zA-Z_]*(s|es)$"
    return check_deep_array(spec, "", message, severity, logger, id, pattern, 0, False)

def deep_is_date_time(spec, yq_path, message, severity, logger, id, lst, idx, log_flag):
    for key, value in spec.items():
        tmp = f'."{key}"'
        if type(value) is dict:
            if value.get("format") and value.get("format") == "date-time":
                flag = False
                # check if it matches one of the items in the list
                for valid_name in lst:
                    if re.match(valid_name, f"{key}"):
                        flag = True
                # log if no match is found
                if not flag:
                    line_num = get_line_number_key(yq_path + tmp, logger)
                    logger.log_with_line_number_key(line_num, severity, message, id, yq_path+tmp)
            else:
                deep_is_date_time(value, yq_path+tmp, message, severity, logger, id, lst, idx, log_flag)
        elif type(value) is list:
            deep_check_generic_array(spec, yq_path+tmp, message, severity, logger, id, key, lst, deep_is_date_time, 0, False)

# only works for UTC time format
def is_date_time(spec, yq_path, message, severity, logger, id, lst):
    return deep_is_date_time(spec, "", message, severity, logger, id, lst, 0, False)
"""END"""

"""START: Utility functions for checking internal refrences"""

# change this string '#/components/schemas/Health' to ['components', 'schemas', 'Health']
def parse_internal_refs(ref):
    ref = ref.split("/")[1:]
    return ref

# check if the path of the internal reference is valid
def check_internal_ref_path(spec_file, path_list):
    for path in path_list:
        spec_file = spec_file.get(path)
        if not spec_file:
            return False
    return True

# recursively check if an array contains dictionaries and perform checks
def deep_check_array_refs(spec_iter_file, spec_file, yq_path, logger, message):
    for i, item in enumerate(spec_iter_file):
        tmp = f".[{i}]"
        if type(item) is dict:
            deep_check_refs(item, spec_file, yq_path + tmp, logger, message)
"""
recursively check if the key equals $ref,
    -> validate the path contained in $ref,
    -> if path does not exist log the line of $ref
"""
def deep_check_refs(spec_iter_file, spec_file, yq_path, logger, message):
    for key, value in spec_iter_file.items():
        tmp = f'."{key}"'
        if type(value) is dict:
            deep_check_refs(value, spec_file, yq_path + tmp, logger, message)
        elif type(value) is list:
            deep_check_array_refs(value, spec_file, yq_path + tmp, logger, message)
        elif key == "$ref":
            # check for external refs
            if value.find("https://") != -1:
                if not API_KEY:
                    print("\tAPI Key for swaggerhub is not present. Skipping checks for external refs")
                    continue
                url, path = value.split("#")
                path = "#" + path
                parsed_path = parse_internal_refs(path)

                if not EXTERNAL_DATA.get(url):
                    EXTERNAL_DATA[url] = {}
                    # get the external file
                    r = requests.get(url, headers=SWAGGER_HEADERS)
                    if r.headers.get('content-type').find('yaml') != -1:
                        # save data for future requests
                        EXTERNAL_DATA[url]["data"] = yaml.safe_load(r.content.decode())
                    # if header is not yaml log external source not found
                    else:
                        EXTERNAL_DATA[url]["data"] = {}
                        line_num = get_line_number_key(yq_path + tmp, logger)
                        logger.log_internal_references(line_num, f"External source not found: {url}", yq_path + tmp, value)
                        continue

                if EXTERNAL_DATA[url].get(path) is None:
                    EXTERNAL_DATA[url][path] = check_internal_ref_path(EXTERNAL_DATA[url]["data"], parsed_path)

                # if the external ref does not exist log
                if not EXTERNAL_DATA[url][path]:
                    line_num = get_line_number_key(yq_path + tmp, logger)
                    logger.log_internal_references(line_num, message, yq_path + tmp, value)
            else:
                parsed_path = parse_internal_refs(value)

                if EXTERNAL_DATA.get(value) is None:
                    EXTERNAL_DATA[value] = check_internal_ref_path(spec_file, parsed_path)

                if not EXTERNAL_DATA.get(value):
                    line_num = get_line_number_key(yq_path + tmp, logger)
                    logger.log_internal_references(line_num, message, yq_path + tmp, value)
            
# checks to see if internal references exist or not
def check_refs(spec_iter_file, spec_file, yq_path, logger):
    if spec_iter_file is None:
        return
    message = "Reference does not exist"
    deep_check_refs(spec_iter_file, spec_file, "", logger, message)
"""END"""

# helper function to recursively call the function that invoked it, if it contains any value of type dict
# useful for recursion
def deep_check_generic_array(spec, yq_path, message, severity, logger, id, key_list, pattern_or_lst, func, idx_of_key_list, log_flag, **kwargs):
    for idx, item in enumerate(spec):
        tmp = f".[{idx}]"
        if type(item) is dict:
            func(item,yq_path + tmp, message, severity, logger, id, key_list, pattern_or_lst, idx_of_key_list, log_flag, **kwargs)

"""START: Utility functions to perform checks on key_name"""

# check the keys of a property, against a list of prebuilt standards

def check_keys_global(spec, yq_path, message, severity, logger, id, key_lst, pattern, idx, log_flag, **kwargs):
    tmp_flag = log_flag
    for s_key, s_value in spec.items():
        tmp = f'."{s_key}"'
        if re.match(key_lst[idx], f"{s_key}"):#s_key == key_lst[idx]:
            # set parent node to true for logging
            if idx == 0:
                log_flag = True
            if idx >= len(key_lst) - 1:
                idx = len(key_lst) - 1
            else:
                idx += 1
        else:
            log_flag = False
        # if we are inside parent node set log_flag to true
        if tmp_flag:
            log_flag = True

        if s_key == key_lst[-1] and log_flag:# and type(s_value) is dict:
            kwargs.get("log_func")(s_value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, idx, log_flag, **kwargs)
        elif type(s_value) is dict:
            check_keys_global(s_value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, idx, log_flag, **kwargs)
        elif type(s_value) is list:
            deep_check_generic_array(s_value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, check_keys_global, idx, log_flag, **kwargs)

def check_keys_list_at_least_n_log(spec, yq_path, message, severity, logger, id, key, lst, idx, log_flag, **kwargs):
    n = lst[-1]
    tmp_arr = [False] * (len(lst) - 1)

    for p_key, value in spec.items():
        for i, pattern in enumerate(lst[:-1]):
            # if the condition is already fulfilled skip
            if tmp_arr[i]:
                continue
            # check if the key in spec file matches the pattern
            if re.match(pattern, f"{p_key}"):
                tmp_arr[i] = True
    
    if sum(tmp_arr) < n:
        line_num = get_line_number_key(yq_path, logger)
        logger.log_with_line_number_key(line_num, severity, message, id, yq_path)

# log values if spec value is not in the predefined list
def check_keys_list_log(spec, yq_path, message, severity, logger, id, key, lst, idx, log_flag, **kwargs):
    if type(spec) is not dict:
        return
    for p_key, value in spec.items():
        tmp = f".{p_key}"
        # turn integer keys into string keys
        if f"{p_key}" not in lst:
            line_num = get_line_number_key(yq_path + tmp, logger)
            logger.log_with_line_number_key(line_num, severity, message, id, yq_path+tmp)

# check if the keys(shallow) of the property matches the standard value
def check_keys_pattern_log(spec, yq_path, message, severity, logger, id, key, pattern, idx, log_flag, **kwargs):
    if type(spec) is not dict:
        return
    for s_key, s_value in spec.items():
        tmp = f'."{s_key}"'
        if not re.match(pattern, f"{s_key}"):
            line_num = get_line_number_key(yq_path + tmp, logger)
            logger.log_with_line_number_key(line_num, severity, message, id, yq_path + tmp)

# check if the keys(shallow) of the property match the pattern, log if it matches the pattern
def check_keys_pattern_inverse_log(spec, yq_path, message, severity, logger, id, key, pattern, idx, log_flag, **kwargs):
    if type(spec) is not dict:
        return
    for s_key, s_value in spec.items():
        tmp = f'."{s_key}"'
        if re.match(pattern, f"{s_key}"):
            line_num = get_line_number_key(yq_path + tmp, logger)
            logger.log_with_line_number_key(line_num, severity, message, id, yq_path + tmp)

def check_keys_pattern_list_log(spec, yq_path, message, severity, logger, id, key, pattern_lst, idx, log_flag, **kwargs):
    # if the dict is empty log
    if type(spec) is not dict:
        line_num = get_line_number_key(yq_path, logger)
        logger.log_with_line_number_key(line_num, severity, message, id, yq_path)
        return
    
    tmp_flag = True
    for s_key, s_value in spec.items():
        for pattern in pattern_lst:
            # no logging if it matches one of the values in the list
            if re.match(pattern, f"{s_key}"):
                tmp_flag = False
  
    # log the error
    if tmp_flag:
        line_num = get_line_number_key(yq_path, logger)
        logger.log_with_line_number_key(line_num, severity, message, id, yq_path)
    
"""END"""

"""START: Utility functions to perform checks on key_value"""

# only checks the value of node if the value on the spec file matches the value of rules.json for a particular key
# eg, if x == 1 in both rules.json and spec file, will it check for the value of y
#   x: 1
#   z:
#    y: 2
def check_keys_value_log(spec, yq_path, message, severity, logger, id, key_lst, r_value, idx, log_flag, **kwargs):
    check_flag = False
    val = spec.get(key_lst[-1])
    if kwargs.get("value"):
        if val == kwargs.get("value"):
            check_flag = True
    elif kwargs.get("arr"):
        if val in kwargs.get("arr"):
            check_flag = True
    elif kwargs.get("gte"):
        if val >= kwargs.get("gte"):
            check_flag = True
    elif kwargs.get("lte"):
        if val <= kwargs.get("lte"):
            check_flag = True
    
    if check_flag:
        node = kwargs.get("required_node")
        type_of_match = type(kwargs.get("node_requirement"))
        requirement_to_match = kwargs.get("node_requirement")

        parsed_node = node.split(".")
        node_value = spec
        for tmp_node in parsed_node:
            node_value = node_value.get(tmp_node)
            if not node_value:
                tmp = f".{key_lst[-1]}"
                line_num = get_line_number_key(yq_path + tmp, logger)
                # log node is not present
                logger.log_with_line_number_key(line_num, severity, message + f" not found", id, yq_path + tmp)
                return
        
        tmp = f".{node}"
        line_num = get_line_number_key(yq_path + tmp, logger)
        
        if type_of_match is list:
            if type(requirement_to_match[0]) is str:
                tmp_flag = True
                for req in requirement_to_match:
                    if re.match(req, f"{node_value}"):
                        tmp_flag = False
                if tmp_flag:
                    logger.log_with_line_number_key_and_value(line_num, severity, message + f" must be one of {requirement_to_match}", id, yq_path + tmp, node_value)
            elif not node_value in requirement_to_match:
                # log the error
                logger.log_with_line_number_key_and_value(line_num, severity, message + f" must be one of {requirement_to_match}", id, yq_path + tmp, node_value)
        elif type_of_match is str:
            if not re.match(requirement_to_match, node_value):
                logger.log_with_line_number_key_and_value(line_num, severity, message + f" must be snake case", id, yq_path + tmp, node_value)
        elif type_of_match is int or type_of_match is float:
            if not node_value == requirement_to_match:
                logger.log_with_line_number_key_and_value(line_num, severity, message + f" must be {requirement_to_match}", id, yq_path + tmp, node_value)
# helper func to log the error
def check_keys_value(spec, yq_path, message, severity, logger, id, key_lst, r_value, idx, log_flag, **kwargs):
    tmp_flag = log_flag
    for s_key, s_value in spec.items():
        tmp = f'."{s_key}"'
        if re.match(key_lst[idx], f"{s_key}"):#s_key == key_lst[idx]
            # set parent node to true for logging
            if idx == 0:
                log_flag = True
            if idx >= len(key_lst) - 1:
                idx = len(key_lst) - 1
            else:
                idx += 1
        else:
            log_flag = False
        # if we are inside parent node set log_flag to true
        if tmp_flag:
            log_flag = True

        if s_key == key_lst[-1] and log_flag:
            check_keys_value_log(spec, yq_path, message, severity, logger, id, key_lst, r_value, idx, log_flag, **kwargs)
        elif type(s_value) is dict:
            check_keys_value(s_value, yq_path + tmp, message, severity, logger, id, key_lst, r_value, idx, log_flag, **kwargs)
        elif type(s_value) is list:
            deep_check_generic_array(s_value, yq_path + tmp, message, severity, logger, id, key_lst, r_value, check_keys_value, idx, log_flag, **kwargs)
"""END"""

"""START: Utility function to perform checks on array_name"""
def check_array_pattern_log(spec, yq_path, message, severity, logger, id, key_lst, pattern, idx, log_flag):
    for idx, item in enumerate(spec):
        tmp = f".[{idx}]"
        if not re.match(pattern, f"{item}"):
            line_num = get_line_number_value(yq_path + tmp, logger)
            logger.log_with_line_number_key(line_num, severity, message, id, yq_path + tmp)


def check_array_pattern(spec, yq_path, message, severity, logger, id, key_lst, pattern, idx, log_flag):
    # inherit flag from parent node
    tmp_flag = log_flag
    for s_key, value in spec.items():
        tmp = f'."{s_key}"'

        if re.match(key_lst[idx], f"{s_key}"):#s_key == key_lst[idx]
            # set parent node to true for logging
            if idx == 0:
                log_flag = True
            if idx >= len(key_lst) - 1:
                idx = len(key_lst) - 1
            else:
                idx += 1
        else:
            log_flag = False
        # if we are inside parent node set log_flag to true
        if tmp_flag:
            log_flag = True

        if s_key == key_lst[-1] and log_flag:
            check_array_pattern_log(value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, idx, log_flag)
        elif type(value) is dict:
            check_array_pattern(value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, idx, log_flag)
        elif type(value) is list:
            deep_check_generic_array(value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, check_array_pattern, idx, log_flag)
"""END"""