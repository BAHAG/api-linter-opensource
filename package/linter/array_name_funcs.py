import re
from linter.generic_funcs import *
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
        if type(s_key) == str and (s_key.lower().find("country") != -1 or s_key.lower().find("language") != -1):
            continue
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
            # if the dict has name=country/language skip
            name = (value.get("name", "") if type(value.get("name")) == str else "").lower()
            if type(name) == str and (name.find("country") != -1 or name.find("language") != -1):
                continue
            check_array_pattern(value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, idx, log_flag)
        elif type(value) is list:
            deep_check_generic_array(value, yq_path + tmp, message, severity, logger, id, key_lst, pattern, check_array_pattern, idx, log_flag)
"""END"""
