import argparse
from linter.utils import *
from linter.logger import Logger
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--spec", type=str, help="Path to the yaml specification file")
parser.add_argument("-r", "--rule", type=str, help="Path to the rules that specification file must follow")
parser.add_argument("-o", "--output", required=False, type=str, help="Output the linting errors possible options, json | yaml. Default JSON", default="json")

args = parser.parse_args()
# global logger
error_logger = Logger()

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

    # check version mismatch
    check_version(yaml_spec, error_logger)
    
    # extract required metadata from the api specification file => depends on check_refs
    extract_metadata(yaml_spec, error_logger, metadata_fields)
    
    # check internal references
    check_refs(yaml_spec, yaml_spec, "", error_logger)

    spec_title = yaml_spec.get("info", {"title": "dummy"}).get("title")
    spec_version = yaml_spec.get("info", {"version": "0.0.0"}).get("version")
    
    if not spec_version:
        spec_version = "0.0.0"
    if not spec_title:
        spec_title = "dummy"
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
            # one of path_name_config keys
            path_name = path_obj.get("path_name")
            # yaml path to perform the check
            path_value = path_obj.get("path_value")
            required_path = path_obj.get("required_path")

            # add rule id to the list of checks performed
            if id not in implemented_rules:
                implemented_rules.append(id)

            # if the path is required, and it does not exist log and skip checks
            if path_name == "required_path":
                parsed_path, line_number, _ = parse_required_path(required_path, yaml_spec)
                if not line_number:
                    error_logger.log_with_property(required_path, severity, path_obj.get("message"), id)
                    continue
            # path object can have multiple checks
            for check_obj in path_obj.get("checks"):
                # if a check has exception don't perform the check
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
                
                # set generic properties for logging
                value = check_obj.get("value")
                func = path_name_config.get(path_name).get(check_obj.get("name"))
                modified_key_name = path_value.split(".")
                parsed_path, line_number, _ = parse_required_path(path_value, yaml_spec)

                if path_name == "required_path":
                    # execute required path function
                    func(value, parsed_path, line_number, severity, check_obj.get("message"), id, error_logger)
                
                elif path_name == "properties":
                    # spec, line_spec, message, severity, logger, id, pattern
                    func(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, value)

                elif path_name == "key_name":
                    # spec, message, severity, logger, id, key_list, pattern_or_list, idx_of_key_list, log_flag, log_func
                    check_keys_global(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, modified_key_name, value, 0, False, log_func=func)
                
                elif path_name == "array_name":
                    # spec, message, severity, logger, id, key_list, pattern_or_list, idx_of_key_list, log_flag
                    func(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, modified_key_name, value, 0, False)
                
                elif path_name == "key_value":
                    # spec, message, severity, logger, id, key_list, pattern_or_list, idx_of_key_list, log_flag, **kwargs
                    func(yaml_spec, "", check_obj.get("message"), severity, error_logger, id, modified_key_name, None, 0, False, **value)
                
                elif path_name == "example":
                    # call func
                    func(yaml_spec, "", error_logger, yaml_spec)

    error_logger.print_and_save_logs()

def run_linter(spec_file, rule_file, output_fmt):
    # create a .env file to save global objects
    with open(Path.home()/".env", "w") as ev:
        ev.write(f"SPEC_FILE={spec_file}")
    # strip .yaml from filename
    output_file_name = spec_file.split(".")[0]
    error_logger.set_file_name_and_format(output_file_name, output_fmt)
    main(spec_file, rule_file, output_fmt)

if __name__ == "__main__":
    run_linter(args.spec, args.rule, args.output)