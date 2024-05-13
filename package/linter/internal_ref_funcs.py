import requests
import yaml
from linter.generic_funcs import *

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

def extract_external_metadata(url, parsed_path, logger):
    """
        Extract metadata from BAHAG domains, and add them to a list
    """
    # if ur points to domain return
    return_flag = False

    # set default metadata
    if not logger.get_internal_metadata("domain_name"):
        logger.add_metadata("domain_name", "-")
        logger.add_metadata("domain_version", "-")
        logger.add_metadata("domain_model", "-")

    # problem or model?
    if url.find("Problem") != -1:
        logger.add_metadata("domain_name", "Problem")
    else:
        return_flag = True
    
    if return_flag:
        return

    # get external data
    dom_spec = EXTERNAL_DATA.get(url).get("data")

    # extract version
    version = dom_spec.get("info").get("version")

    # append version and 
    logger.add_metadata("domain_version", version)
    parsed_path = parsed_path[:-1]
    model = dom_spec

    for path in parsed_path:
        model = model.get(path)
    tmp_model = None
    for key in model.keys():
        if key == "Problem":
            tmp_model = "Problem"
        elif key == "ErrorModel":
            tmp_model = "ErrorModel"

    logger.add_metadata("domain_model", tmp_model)

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
                        extract_external_metadata(url, parsed_path, logger)
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