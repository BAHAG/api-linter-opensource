import requests
import json
from pathlib import Path
import os
import subprocess
from google.cloud import bigquery as bq
from datetime import datetime
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

SWAGGER_HUB = os.getenv("SWAGGERHUB_API_KEY")

headers = {
    "Accept": "application/yaml",
    "Authorization": SWAGGER_HUB
}
# contains all the required information about our api
api_data = []
credentials = service_account.Credentials.from_service_account_info(
    json.loads(
        os.getenv("BIGQUERY_API_SERVICE_ACCOUNT_JSON")
    )
)

def get_spec_files_from_bq():
    OWNER = "BAHAG"
    WD = Path("/tmp")
    SPEC_PATH = WD / "spec_files"
    TABLE_NAME = "int-apitesting-prod-9866.test_results.view_api_versions2"
    
    query_api_view = f"""
    SELECT * FROM {TABLE_NAME}
    """

    if not SPEC_PATH.exists():
        print(f"Creating folder in {SPEC_PATH.resolve()}")
        os.mkdir(SPEC_PATH)
    
    client = bq.Client(credentials=credentials, project="int-apitesting-prod-9866")
    api_job = client.query(query_api_view)
    # extract required data from view_api_versions2
    for row in api_job.result():
        tmp = {
            "name": row.api,
            "version": row.version,
            "team": row.team,
            "status": int(row.status),
            "basepath": row.basepath,
            "stage": row.stage,
            # api-masterdata-v1-assets-masterdata-2-x-x-x-prod
            "file_name": f"{row.api}{'-'.join(row.basepath.split('/'))}{'-'.join(row.version.split('.')).replace('/', '-')}-{row.stage}"
        }
        api_data.append(tmp)
    
    # download all apis from swaggerhub
    for api in api_data:
        file_name = api["file_name"]
        
        # Missing version number in bigquery database
        if not api["version"]:
            with open(SPEC_PATH / f"{file_name}-output.json", "w") as jf:
                jf.write(json.dumps({
                    "total": 1,
                    "warnings": 0,
                    "errors": 1,
                    "logs": [
                        {
                            "severity": "ERROR",
                            "message": f"Missing version number in database. Status: {api['status']}"
                        }
                    ]
                }))
            print(f"Failed to fetch yaml file for: {api['name']}. Status code: {api['status']}")
            # no need to send a request
            continue
        # /owner/api-name/api-version
        SWAGGER_HUB_URL = f"https://api.swaggerhub.com/apis/{OWNER}/{api['name']}/{api['version']}"

        r = requests.get(SWAGGER_HUB_URL, headers=headers)
        print(f"Downloading spec file for {api['name']}, version: {api['version']}, stage: {api['stage']}, content-type: {r.headers.get('content-type')}")

        if r.headers.get('content-type').find('json') != -1:
            with open(SPEC_PATH / f"{file_name}-output.json", "w") as jf:
                jf.write(json.dumps({
                    "total": 1,
                    "warnings": 0,
                    "errors": 1,
                    "logs": [
                        {
                            "severity": "ERROR",
                            "message": f"API specification does not exist in swagger hub, version: {api['version']}, stage: {api['stage']}"
                        }
                    ]
                }))
                print(f"Specification file does not exist in swagger hub {api['name']}, version: {api['version']}, stage: {api['stage']}")
                # no need to create a yaml file
            continue

        with open(SPEC_PATH / f"{file_name}.yaml", "w") as yf:
            yf.write(r.content.decode())


# use linter to lint all the yaml spec files
def check_spec_errors():
    spec_dir = Path("/tmp") / "spec_files"
    files = [x for x in os.listdir(spec_dir) if x.split(".")[1] == "yaml"]
    # get logs from docker image
    for file_name in files:
        print(f"\n\nLogs for {file_name}:\n")
        # creates file_name-output.json
        s = subprocess.run(["python3", "local_dev/linter.py","-s", f"{spec_dir.resolve()}/{file_name}","-r","rules.json", "-o", "json"], capture_output=True)
        # log the output to the console
        print(s.stdout.decode())
        print(s.stderr.decode())

if __name__ == "__main__":
    # download the specification files of apis on production
    get_spec_files_from_bq()
    # lint the errors with api-linter package
    check_spec_errors()