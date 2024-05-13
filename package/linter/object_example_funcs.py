from linter.generic_funcs import *
from linter.internal_ref_funcs import EXTERNAL_DATA

""""START   EXAMPLE utility functions"""
# recursion helper, checks if an array is an object
def check_example_array_helper(arr, yq_path, logger, spec):
    for i, item in enumerate(arr):
        tmp = f".[{i}]"
        if item is dict:
            check_example(item, yq_path+tmp, logger, spec)

def check_ref_examples_object(spec, yq_path, logger, spec_duplicate):
    # has an example/ examples
    # /definition/Health = {type:.., properties:.., example:..}
    props = spec.get("properties")
    examples = spec.get("examples")
    if not examples:
        examples = spec.get("example")

    if not props:
        return
    
    if examples:
        for key, value in props.items():
            tmp = f".properties.{key}"
            
            if value.get("$ref"):
                call_check_ref_example(spec_duplicate, value.get("$ref"), yq_path, logger)
                continue

            # log the error
            if examples.get(key) is None:
                line_num = get_line_number_key(yq_path+tmp, logger)
                logger.log_missing_example(line_num, "Example not found for a schema in a HTTP response", yq_path+tmp)
            
        return

    for key, value in props.items():
        tmp = f".properties.{key}"
        
        if value.get("$ref"):
            call_check_ref_example(spec_duplicate, value.get("$ref"), yq_path, logger)
            continue
        
        if value.get("type") == "object":
            check_ref_examples_object(value, yq_path+tmp, logger, spec_duplicate)
            continue

        if value.get("type") == "boolean":
            continue
        
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
            if not (items.get("examples") or items.get("example") or items.get("default")):
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
""""END:   EXAMPLE utility functions"""