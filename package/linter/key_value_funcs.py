import re
from linter.generic_funcs import *
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