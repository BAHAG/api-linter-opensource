import json
import requests
import yaml
from requests.exceptions import RequestException
from urllib.parse import urlsplit
from generic_funcs import *

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
SWAGGER_METADATA_HEADERS = {
    "Accept": "application/json",
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

def _external_response_error(response, url):
    status_code = response.status_code
    response_text = getattr(response, "text", "") or ""
    response_message = response_text.lower()
    content_type = (response.headers.get("content-type") or "").lower()
    if "unpublish" in response_message:
        return f"SwaggerHub API/domain version is unpublished: {url}"
    if "json" in content_type:
        try:
            response_metadata = json.loads(response_text)
        except (TypeError, ValueError):
            response_metadata = None
        if isinstance(response_metadata, dict) and response_metadata.get("published") is False:
            return f"SwaggerHub API/domain version is unpublished: {url}"
    if status_code != 404:
        return None
    if "version" in response_message and any(
        phrase in response_message for phrase in ("not found", "does not exist", "doesn't exist")
    ):
        return f"SwaggerHub version does not exist: {url}"
    return f"SwaggerHub API/domain or version does not exist: {url}"

def _swaggerhub_publication_error(url):
    parsed_url = urlsplit(url)
    if parsed_url.netloc.lower() != "api.swaggerhub.com":
        return None

    path_parts = parsed_url.path.strip("/").split("/")
    if len(path_parts) != 4 or path_parts[0] not in ("apis", "domains"):
        return None

    version = path_parts[3]
    metadata_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{path_parts[0]}/{path_parts[1]}/{path_parts[2]}"
    offset = 0

    while True:
        try:
            response = requests.get(
                metadata_url,
                headers=SWAGGER_METADATA_HEADERS,
                params={"limit": 100, "offset": offset},
                timeout=15,
            )
        except RequestException:
            return None

        if response.status_code == 404:
            return f"SwaggerHub API/domain does not exist: {url}"
        if not 200 <= response.status_code < 300:
            return None

        try:
            metadata = response.json()
        except ValueError:
            return None
        if not isinstance(metadata, dict) or not isinstance(metadata.get("apis"), list):
            return None

        entries = metadata["apis"]
        for entry in entries:
            properties = {
                item.get("type", "").lower(): item.get("value")
                for item in entry.get("properties", [])
                if isinstance(item, dict)
            }
            if str(properties.get("x-version", "")) != version:
                continue

            published = str(properties.get("x-published", "")).strip().lower()
            if published == "false":
                return f"SwaggerHub API/domain version is unpublished: {url}"
            return None

        try:
            total_count = int(metadata.get("totalCount", len(entries)))
            current_offset = int(metadata.get("offset", offset))
        except (TypeError, ValueError):
            return None

        next_offset = current_offset + len(entries)
        if not entries or next_offset >= total_count or next_offset <= offset:
            return f"SwaggerHub version does not exist: {url}"
        offset = next_offset

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
                # app.swaggerhub.com serves HTML; B102 reports it, but resolve via the API host
                url = url.replace("app.swaggerhub.com", "api.swaggerhub.com")
                path = "#" + path
                parsed_path = parse_internal_refs(path)

                if url not in EXTERNAL_DATA:
                    publication_error = _swaggerhub_publication_error(url)
                    if publication_error:
                        EXTERNAL_DATA[url] = {"error": publication_error}

                if url not in EXTERNAL_DATA:
                    # get the external file
                    try:
                        r = requests.get(url, headers=SWAGGER_HEADERS)
                    except RequestException:
                        EXTERNAL_DATA[url] = {"skip": True}
                        continue

                    response_error = _external_response_error(r, url)
                    if response_error:
                        EXTERNAL_DATA[url] = {"error": response_error}
                    elif not 200 <= r.status_code < 300:
                        EXTERNAL_DATA[url] = {"skip": True}
                    elif "yaml" in (r.headers.get("content-type") or "").lower():
                        # save data for future requests
                        EXTERNAL_DATA[url] = {}
                        EXTERNAL_DATA[url]["data"] = yaml.safe_load(r.content.decode())
                        extract_external_metadata(url, parsed_path, logger)
                    # if header is not yaml log external source not found
                    else:
                        EXTERNAL_DATA[url] = {"data": {}, "error": f"External source not found: {url}"}

                if EXTERNAL_DATA[url].get("skip"):
                    continue
                if EXTERNAL_DATA[url].get("error"):
                    line_num = get_line_number_key(yq_path + tmp, logger)
                    logger.log_internal_references(line_num, EXTERNAL_DATA[url]["error"], yq_path + tmp, value)
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