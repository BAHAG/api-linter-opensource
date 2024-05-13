import argparse
from linter.utils import *
from linter.logger import Logger
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--spec", type=str, help="Path to the yaml specification file")
parser.add_argument("-r", "--rule", type=str, help="Path to the rules that specification file must follow")
parser.add_argument("-o", "--output", required=False, type=str, help="Output the linting errors possible options, json | yaml. Default JSON")
parser.add_argument("-l", "--local", action="store_true", help="Use local flag for local testing")

args = parser.parse_args()
# global logger
error_logger = Logger()
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

# array to know the number of implemented rules
implemented_rules = []
def main(spec_file="sample.yaml", rule_file="rules.json", output_fmt="json"):
    # extract rules and metadata
    rules_and_metadata = get_rules(rule_file)
    metadata_fields = rules_and_metadata.get("metadata")
    rules = rules_and_metadata.get("rules")

    yaml_spec = get_spec(spec_file)
    if not yaml_spec:
        return

    output_file_name = spec_file.split(".")[0]
    # check version mismatch
    check_version(yaml_spec, error_logger)
    
    # extract required metadata from the api specification file => depends on check_refs
    extract_metadata(yaml_spec, error_logger, metadata_fields)
    
    # check internal references
    check_refs(yaml_spec, yaml_spec, "", error_logger)

    # check examples
    check_example(yaml_spec, "", error_logger, yaml_spec)
    if yaml_spec.get("info"):
        spec_title = yaml_spec.get("info").get("title")
        spec_version = yaml_spec.get("info").get("version")
    else:
        spec_title = None
        spec_version = None
    if not spec_title:
        spec_title = "dummy"
    if not spec_version:
        spec_version = "10"
    else:
        spec_version = spec_version.split(".")[0]
    # get one rule at a time
    for rule in rules:
        # id and severity of the rule
        id = rule.get("id")
        severity = rule.get("severity")
        # implementation is set to "NULL" if we don't want to check for the rule
        if rule.get("implementation"):
            continue
        for path_obj in rule.get("paths"):
            
            required_path = path_obj.get("required_path")
            key_name = path_obj.get("key_name")
            key_value = path_obj.get("key_value")
            array_name = path_obj.get("array_name")
            properties = path_obj.get("properties")

            if id not in implemented_rules:
                implemented_rules.append(id)

            # if the path is required log the error and continue
            if required_path:
                parsed_path, line_number, _ = parse_required_path(required_path, yaml_spec)
                if not parsed_path:
                    error_logger.log_with_property(required_path, severity, path_obj.get("message"), id)
                    continue
            
            for check_obj in path_obj.get("checks"):
                if check_obj.get("exceptions"):
                    continue_flag = False
                    for exception in check_obj.get("exceptions"):
                        except_version = exception.get("version")
                        except_title = exception.get("title")

                        if except_title == spec_title and except_version == spec_version:
                            continue_flag = True
                            break
                    if continue_flag:
                        continue

                if required_path:
                    func = required_path_config[check_obj.get("name")]
                    value = check_obj.get("value")
                    parsed_path, line_number, _ = parse_required_path(required_path, yaml_spec)
                    # do required path stuff
                    if not func(value, parsed_path):
                        # log errors on checks
                        error_logger.log_with_line_number(line_number, severity, check_obj.get("message"), id)
                elif properties:
                    func = property_config[check_obj.get("name")]
                    value = check_obj.get("value")
                    # spec, line_spec, message, severity, logger, id, pattern
                    func(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, value)
                    
                elif key_name:
                    modified_key_name = key_name.split(".")
                    # func = logger function
                    func = key_name_config[check_obj.get("name")]
                    value = check_obj.get("value")
                    # spec, message, severity, logger, id, key_list, pattern_or_list, idx_of_key_list, log_flag
                    check_keys_global(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, modified_key_name, value, 0, False, log_func=func)
                elif array_name:
                    modified_key_name = array_name.split(".")
                    func = array_name_config[check_obj.get("name")]
                    value = check_obj.get("value")
                    # spec, message, severity, logger, id, key_list, pattern_or_list, idx_of_key_list, log_flag
                    func(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, modified_key_name, value, 0, False)
                elif key_value:
                    modified_key_name = key_value.split(".")
                    func = key_value_config[check_obj.get("name")]
                    value = check_obj.get("value")
                    # spec, message, severity, logger, id, key_list, pattern_or_list, idx_of_key_list, log_flag, **kwargs
                    func(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, modified_key_name, None, 0, False, **value)

    error_logger.print_and_save_logs()

# remove {}, and turn booleans into strings
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

def run_script(spec_file, rule_file, output_fmt):
    # create a .env file to save global objects
    with open(Path.home()/".env", "w") as ev:
        ev.write(f"SPEC_FILE={args.spec}")
    # strip .yaml from filename
    output_file_name = args.spec.split(".")[0]
    error_logger.set_file_name_and_format(output_file_name, args.output)
    main(spec_file, rule_file, output_fmt)

def run_local(spec_file, rule_file, output_fmt):
    spec_file = parse_yaml_files(spec_file)
    # create a .env file to save global objects
    with open(Path.home()/".env", "w") as ev:
        ev.write(f"SPEC_FILE={spec_file}")
    # strip .yaml from filename
    output_file_name = spec_file.split(".")[0]
    error_logger.set_file_name_and_format(output_file_name, args.output)
    main(spec_file, rule_file, output_fmt)

if __name__ == "__main__":
    if not args.output:
        args.output = "json"
    if args.local:
        run_local(args.spec, args.rule, args.output)
    else:
        run_script(args.spec, args.rule, args.output)