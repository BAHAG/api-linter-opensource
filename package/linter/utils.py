import re
import json
import subprocess
from dotenv import load_dotenv
from pathlib import Path
import os
import yaml
from yaml.resolver import Resolver
import requests
from linter.object_example_funcs import *
from linter.required_path_funcs import *
from linter.yaml_property_funcs import *
from linter.array_name_funcs import *
from linter.key_value_funcs import *
from linter.key_name_funcs import *
from linter.generic_funcs import *
from linter.internal_ref_funcs import *

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

# remove boolean keys from yaml spec files
def parse_yaml_files(spec_file):
    replacing_str = ""
    with open(spec_file) as yf:
        for line in yf.readlines():
            truth_index = line.lower().find("true")
            falsy_index = line.lower().find("false")
            colon_index = line.find(":")

            if truth_index != -1 and colon_index != -1 and truth_index < colon_index:
                line = line.replace("true", "Trueeee")
            
            if falsy_index != -1 and colon_index != -1 and falsy_index < colon_index:
                line = line.replace("false", "Falseeee")
            
            replacing_str += line
    
    file_name = spec_file #spec_file.split(".")[0] + "-remodeled.yaml"

    with open(file_name, "w") as yf:
            yf.write(replacing_str)

    return file_name

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
    
    if not last in tmp_spec:
        return None, None, last

    tmp_spec = tmp_spec.get(last)
    
    # get line number by using the yq utility tool
    line_num = subprocess.run(["yq", f"{yq_path} | key | line", spec_file_name], capture_output=True)
    line_num = line_num.stdout.decode().strip()

    return tmp_spec, line_num, last
""" END """

""" START   Version Mismatch"""
# recursion handler + logger for checking version mismatch
def check_version_deep(spec, yq_path, pattern, logger, **kwargs):
    for key, value in spec.items():
        tmp = f'."{key}"'
        if key == "version" and value.get("default") and not re.match(pattern, value.get("default")):
            line_num = get_line_number_key(yq_path+tmp+'."default"', logger)
            # log the result to logger
            logger.log_with_line_number(line_num, "ERROR", "Version mismatch in /health and info.version", None)
        if key == "$ref" and type(value) == str and value.lower().find("health") != -1:
            ref = parse_internal_refs(value)
            ref = "." + ".".join([f'"{x}"' for x in ref])
            health_spec = get_internal_ref(kwargs.get("spec_yaml"), value)
            check_version_deep(health_spec, ref, pattern, logger, **kwargs)

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
        # print(health)
        check_version_deep(health, ".paths./health", info_version, logger, spec_yaml=spec)
    except:
        return
""" END Version Mismatch"""

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
        # i += 1
        # find the first matching country path param
        if not COUNTRY_PARAM_NAME:
            for country_name in path.split("/"):
                if country_name.find("country") != -1:
                    COUNTRY_PARAM_NAME = country_name.replace("{", "").replace("}", "")
                    break
        
        for param in param_list:
            ref = param.get("$ref")
            # some params don't have ref
            if not ref:
                continue

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
                i += 1
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
def check_date_format(input_str):
    if not input_str:
        return False
    # Define regular expressions for the two formats
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')  # YYYY-MM-DD
    datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')  # YYYY-MM-DDTHH:MM:SSZ

    # Check if the input string matches either of the patterns
    if date_pattern.match(input_str):
        return True
    elif datetime_pattern.match(input_str):
        return True
    else:
        return False

def extract_metadata(spec, logger, req_paths):
    for pth in req_paths:
        value, _, bq_path = parse_required_path(pth, spec)
        # check if the date time in the following fields are valid
        if bq_path == "x-sunset-date" or bq_path == "x-shutdown-date":
            if not check_date_format(value):
                line_number = get_line_number_key(f".{pth}", logger)
                # log if x-sunset-date or x-shutdown-date exists in the spec file
                if value is not None:
                    logger.log_with_line_number(line_number, "WARN", f"Datetime Format for {bq_path} is invalid", "B105")
                value = None
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



# configuration maps
required_path_config = {
   "pattern": pattern_matching,
   "allowed_values":allowed_values,
   "string_match": string_match,
   "gte":gte,
}

key_name_config = {
    "check_keys_list": check_keys_list_log,
    "check_keys_pattern": check_keys_pattern_log,
    "check_keys_pattern_inverse": check_keys_pattern_inverse_log,
    "check_keys_pattern_list": check_keys_pattern_list_log,
    "check_keys_list_at_least_n": check_keys_list_at_least_n_log
}

key_value_config = {
    "check_keys_value": check_keys_value
}

array_name_config = {
    "check_array_pattern": check_array_pattern
}

property_config = {
    "is_array": is_array,
    "is_date_time": is_date_time
}

example_config = {
    "check_example": check_example
}

path_name_config = {
    "required_path": required_path_config,
    "properties": property_config,
    "key_name": key_name_config,
    "key_value": key_value_config,
    "array_name": array_name_config,
    "example": example_config
}