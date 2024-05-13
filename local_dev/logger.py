import json
import yaml

class Logger():
    def __init__(self):
        self.logs = []
        self.example_errors = 0
        self.warnings = 0
        self.errors = 0
        self.severe = 0
        self.output_file_name = None
        self.output_fmt = "json"
        self.metadata = {}
        self.ref_data = set()
    
    def strip_double_quotes(self, key):
        return key.replace("\"", "")

    def add_metadata(self, key, value):
        self.metadata[key] = value
    
    def append_to_metadata_lst(self, key, value):
        self.metadata[key].append(value)
    
    def check_internal_metadata(self, key):
        if not self.metadata.get(key):
            return False
        return True
    
    def get_internal_metadata(self, key):
        return self.metadata.get(key, 0)
    
    def set_file_name_and_format(self, file_name, output_fmt):
        self.output_file_name = file_name
        self.output_fmt = output_fmt
    
    def log_missing_example(self, num_line, message, key):
        transformed_data = f"{num_line}${message}${key}"
        self.ref_data.add(transformed_data)
    
    def append_ref_data_to_logs(self):
        for log in self.ref_data:
            log = log.split("$")
            tmp = {
                "num_line" : int(log[0]),
                "message": log[1],
                "key": self.strip_double_quotes(log[2]),
                "severity": "ERROR",
                "id": "B229"
            }
            self.logs.append(tmp)
            self.example_errors += 1
            self.errors += 1
    
    def log_with_line_number(self, num_line, severity, message, id):
        tmp_dict = {
            "id": id,
            "num_line": num_line,
            "severity": severity,
            "message": message
        }
        self.logs.append(tmp_dict)
        if severity == "WARN":
            self.warnings += 1
        else:
            self.errors += 1

    def log_with_line_number_key_and_value(self, num_line, severity, message, id, key, value):
        tmp_dict = {
            "id": id,
            "num_line": num_line,
            "severity": severity,
            "message": message,
            "key": self.strip_double_quotes(key),
            "value": value
        }
        self.logs.append(tmp_dict)
        if severity == "WARN":
            self.warnings += 1
        else:
            self.errors += 1
    
    def log_with_line_number_key(self, num_line, severity, message, id, key):
        tmp_dict = {
            "id": id,
            "num_line": num_line,
            "severity": severity,
            "message": message,
            "key": self.strip_double_quotes(key)
        }
        self.logs.append(tmp_dict)
        if severity == "WARN":
            self.warnings += 1
        else:
            self.errors += 1
        
    def log_with_property(self, property_, severity, message, id):
        tmp_dict = {
            "id": id,
            "key": self.strip_double_quotes(property_),
            "severity": severity,
            "message": message
        }
        self.logs.append(tmp_dict)
        if severity == "WARN":
            self.warnings += 1
        else:
            self.errors += 1
    
    def log_internal_references(self, num_line, message, key, value):
        tmp_dict = {
            "num_line": num_line,
            "severity": "ERROR",
            "message": message,
            "key": self.strip_double_quotes(key),
            "value": value
        }
        self.logs.append(tmp_dict)
        self.errors += 1
    
    def log_invalid_path(self, line_num, message):
        tmp_dict = {
            "severity": "SEVERE",
            "num_line": line_num,
            "message": message,
        }
        self.logs.append(tmp_dict)
        self.severe += 1
    
    def get_severe_content(self):
        file_name = self.output_file_name + ".yaml"
        line_num = self.logs[0].get("num_line")
        print(line_num)
        tmp_str = ""
        with open(file_name) as yf:
            for count, line in enumerate(yf.readlines()):
                # take two lines
                if count + 1 == line_num or count == line_num:
                    tmp_str += line.strip()
        self.logs[0]["line_content"] = tmp_str

    def get_line_content(self):
        file_name = self.output_file_name + ".yaml"
        # extract line numbers
        line_num = [log.get("num_line") for log in self.logs if log.get("num_line")]
        print(line_num)
        # sort in ascending number
        line_num.sort()
        tmp_dict = {}

        with open(file_name) as yf:
            for count, line in enumerate(yf.readlines()):
                # count starts from 0, if the line number is in our array line_num
                if count + 1 in line_num:
                    tmp_dict[count+1] = line.strip()
        
        for log in self.logs:
            if log.get("num_line"):
                log["line_content"] = tmp_dict[log["num_line"]]
    
    def check_metadata(self):
        req_paths = ['x-audience', 'x-channel', 'openapi']
        supported = ["supported-countries", "supported-languages"]

        for item in req_paths:
            if not self.metadata.get(item):
                self.metadata[item] = None
        
        for item in supported:
            if not self.metadata.get(item):
                self.metadata[item] = None
                self.metadata[item+"-length"] = 0

        if not self.metadata.get("domain_name"):
            self.metadata["domain_name"] = "-"
            self.metadata["domain_model"] = "-"
            self.metadata["domain_version"] = "-"

    def get_logs_json(self):
        return json.dumps(
            {
                "total": len(self.logs),
                "example-errors": self.example_errors,
                "warnings": self.warnings,
                "errors": self.errors + self.severe,
                "logs":self.logs,
                "metadata": self.metadata
            }, 
                indent=4
            )

    def get_logs_yaml(self):
        return yaml.dump(
            {
                "total": len(self.logs),
                "example-errors": self.example_errors,
                "warnings": self.warnings,
                "errors": self.errors + self.severe,
                "logs": self.logs,
                "metadata": self.metadata
            },
                indent=4
            , sort_keys = False
            )
    
    def print_and_save_logs(self):
        # if self.severe > 0:
        #     self.get_severe_content()
        # else:
        #     self.get_line_content()
        self.check_metadata()
        self.append_ref_data_to_logs()
        with open(self.output_file_name+f"-output.{self.output_fmt}", "w") as of:
            if self.output_fmt=="json":
                print(self.get_logs_json())
                of.write(self.get_logs_json())
            elif self.output_fmt == "yaml":
                print(self.get_logs_yaml())
                of.write(self.get_logs_yaml())