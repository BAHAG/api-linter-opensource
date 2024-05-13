import os
import json
from pathlib import Path
import shutil


SOURCE = Path("local_dev")
DESTINATION = Path("package/linter")

LOCAL_IMPORT_LIST = []

def copy_to_package():
    file_lst = os.listdir(SOURCE)

    for file in file_lst:
        # copy file to destination
        shutil.copyfile(SOURCE / file, DESTINATION / file)
        # strip .py extension and add it to local import list
        file = file.replace(".py", "")
        LOCAL_IMPORT_LIST.append(file)
    print("Internal import List: ")
    print(json.dumps(LOCAL_IMPORT_LIST, indent=4))

def change_import_in_dest():
    file_lst = os.listdir(DESTINATION)

    for file in file_lst:
        print(f"Parsing file: {file}")
        if file == "__init__.py":
            with open(DESTINATION / file, "w") as pyf:
                file_content = ""
                for import_name in LOCAL_IMPORT_LIST:
                    print(f"\tAdding import statements for {import_name}")
                    file_content += f"from linter.{import_name} import *\n"
                pyf.write(file_content)
                continue
        with open(DESTINATION / file, "r") as pyf:
            file_content = pyf.read()
            for import_name in LOCAL_IMPORT_LIST:
                if file_content.find(f"from {import_name} import") != -1:
                    print(f"\tReplaced {import_name} to linter.{import_name} in {file}")
                    file_content = file_content.replace(f"from {import_name} import", f"from linter.{import_name} import")

        with open(DESTINATION/file, "w") as pyf:
            pyf.write(file_content)
        # if import is from local_import_list replace the string with linter. prepended to it

if __name__ == "__main__":
    copy_to_package()
    change_import_in_dest()