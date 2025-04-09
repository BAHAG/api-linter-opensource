import re
from linter.generic_funcs import *
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
        if not re.search(pattern, f"{s_key.replace('{', '').replace('}', '')}"):
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