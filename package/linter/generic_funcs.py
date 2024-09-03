import os
import subprocess
import sys
# change this string '#/components/schemas/Health' to ['components', 'schemas', 'Health']
def parse_internal_refs(ref):
    ref = ref.split("/")[1:]
    return ref

def get_internal_ref(spec, ref):
    ref = parse_internal_refs(ref)
    tmp = spec
    for item in ref:
        if not tmp.get(item):
            return None
        tmp = tmp.get(item)
    return tmp
# helper function to recursively call the function that invoked it, if it contains any value of type dict
# useful for recursion
def deep_check_generic_array(spec, yq_path, message, severity, logger, id, key_list, pattern_or_lst, func, idx_of_key_list, log_flag, **kwargs):
    for idx, item in enumerate(spec):
        tmp = f".[{idx}]"
        if type(item) is dict:
            func(item,yq_path + tmp, message, severity, logger, id, key_list, pattern_or_lst, idx_of_key_list, log_flag, **kwargs)

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