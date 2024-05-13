import re
from linter.generic_funcs import *
"""START: Utility functions for performing checks on properties on a yaml document"""

# recursively check if the yaml key has an array as it's value
# if it does not match snake case or is not plural log it
def check_deep_array(spec, yq_path, message, severity, logger, id, pattern, idx, log_flag):
    for key, value in spec.items():
        tmp = f'."{key}"'
        if type(value) is dict:
            if value.get("schema") and type(value.get("schema")) is dict and value.get("schema").get("type") == "array":
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