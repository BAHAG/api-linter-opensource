# BAHAG API linter

This api-linter is a quality assurance tool for OpenAPI specifications, which:

- Increases the quality of APIs
- Checks compliance
- Delivers early feedback for API designers
- Ensures the same look-and-feel of APIs

Its standard configuration will check your APIs against the rules defined in
[Bauhaus' RESTful Guidelines](https://guideline.api.bauhaus/).

## Dependencies
The linter relies on several open source tools, install them from the links provided below
- [yq](https://github.com/mikefarah/yq/#install)

## Quick start guide

Trying out the api-linter locally is easy. \
<span style="color:#006400">Json structure is supported for local testing</span>

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

docker pull ghcr.io/bahag/api-linter:latest

docker run --platform linux/amd64 -it -v $(pwd):/spec ghcr.io/bahag/api-linter:latest linting -s /spec/your-filename.yml -r /rules.json -o json -l -c
```

It will create your-filename-remodeled-output.json and a corresponding your-filename-remodeled.yaml

### Creating rules.json file:
#### The file should be a json object with two fields.
1. metadata
2. rules
```json
    {
        "metadata": [],
        "rules" : {}
    }
```

### 1.) metadata
Metadata should be an array of yaml paths, separated by a .
```yaml
### eg yaml file
openapi: 1.2.3
info:
    version: 1.2.3
    name: some-api
```
```json
### eg rules.json to extract metadata
    {
        "metadata": ["openapi", "info.version", "info.name"]
    }
```

### 2.) rules
Rules should be an array of objects. The attributes of objects should match:
- id : ID of the rule : String
- description : Description of the rule : String
- severity: Severity of the rule : "ERROR" | "WARN"
- specification-type: "OPENAPI"
- specification-version: specification version for openapi, "ALL" or "x.x.x" : String
``` json
[
    {
        "id": "id",
        "description": "Provide api specification using open api",
        "severity": "ERROR",
        "specification-type": "OPENAPI",
        "specification-version": "ALL",
        "paths": [
            {
                "required_path/properties/key_name": "",
                "message": "",
                "checks": [
                    {
                        "check": "pattern/list",
                        "message": "message"
                    }
                ]
            }
        ]
    },
]
```
- paths: Array of objects
``` json
    # append paths with . separated values
    # required path checks for the absolute path in the yaml file
    {
        "path_name": "required_path",
        "path_value": "x.y.z",
        "message" : "Message to display if the required path does not exist",
        "checks" : []
    }
```
``` json
    # key_name checks for the presence of key in the yaml file 
    {
        "key_name" : "key",
        "checks" : []
    }
```
``` json
    # checks for all the property configuration in the yaml file
    {
        "properties" : "*",
        "checks" : []
    }
```
- checks: Array of objects
``` json
    # options for required paths: gte, pattern, allowed_values, string_match
    {
        "name": "gte",
        "value": "3.0.0",
        "message": "Semantic versioning must be greater than or equal to 3.0.0"
    },
    {
        "name": "pattern",
        "value": "^\\d+\\.\\d+\\.\\d+$",
        "message": "Must match the pattern above"
    },
    {
        "name": "allowed_values",
        "value": ["x-yz", "abcd"],
        "message": "required path must match one of the values in the array above"
    },
    {
        "name": "string_match",
        "value": "abc",
        "message": "Must match the string aove"
    }
```
``` json
    # options for properties, BAHAG specific, is_array, is_date_time
    {
        "name": "is_array",
        "value": true,
        "message": "Array name is not plural"
    },
    {
        "name": "is_date_time",
        "value":["[a-z]*_at$", "valid_from", "valid_until", "[a-z]*_start$", "[a-z]*_end$"],
        "message": "Date/Time property does not end with _at, _start, _end"
    }
```
``` json
    # options for checking keys in yaml file: key_name

    # check_keys_value
    # checks if the pattern matches for all of the children keys of key_name
    {
        "message": "Query parameters don't follow snake case",
        "name": "check_keys_value",
        "value": {
            "value": "query",
            "required_node": "name",
            "node_requirement": "^[a-z_][a-z_0-9]*$"
        }
    }
    # check_keys_list
    # children keys must match one of the values in the check_keys_list
    {
        "message": "The response does not use standard http status codes",
        "name": "check_keys_list",
        "value": [
            "200",
            "201",
            "202",
            "204"
        ]
    }
    # check_keys_inverse
    # similar to check_keys_value, but it logs an error if the pattern matches one of the keys
    {
        "name": "check_keys_pattern_inverse",
        "value": "[a-z/-]*(/{2}|/$)",
        "message": "Path is not normalized"
    }
    # check_keys_pattern_list
    # children keys must match one of the patterns in the list and be non empty
    {
        "name": "check_keys_pattern_list",
        "value": ["2[0-9]{2}"],
        "message": "Specification must define at least one success code"
    }
    #check_keys_list_at_least_n
    #keys should match at least n patterns in the list, value of n should be at the end of the list
    {
        "name": "check_keys_list_at_least_n",
        "value": ["patterns", "patterns", "patterns", "value_of_n"],
        "message": "Keys did not match the number of patterns"
    }
```
```json
    # options for creating checks for arrays: array_name

    # check_array_pattern
    # checks if the elements of an array matches the predefined pattern
    {
        "name":"check_array_pattern",
        "value": "^[A-Z][A-Z_]*[A-Z]$",
        "message": "enum property does not follow UPPER_SNAKE_CASE"
    }
```
```json
    # options for creating checks for values in keys

    # check_key_value
    {
        "check_key_value": {
            "value": "x",
            "reqiured_sibling": "y",
            "sibling_requirement": "z"
        },
        "message": "y does not match z"
    }
    {
        "check_key_value": {
            "arr": ["a", "b"],
            "reqiured_sibling": "y",
            "sibling_requirement": "z"
        },
        "message": "y does not match z"
    }
    {
        "check_key_value": {
            "gte": 5,
            "reqiured_sibling": "y",
            "sibling_requirement": "z"
        },
        "message": "y does not match z"
    }
    {
        "check_key_value": {
            "lte": 5,
            "reqiured_sibling": "y",
            "sibling_requirement": "z"
        },
        "message": "y does not match z"
    }
    {
        "check_key_value": {
            "lte": 5,
            "reqiured_sibling": "y",
            "sibling_requirement": ["a", "b", "c"]
        },
        "message": "y does not match one of ['a', 'b', 'c']"
    }
```
### 3.) Exceptions
```json
    # inside check objects we can specify a list of exception objects like the example below 
    "checks": [
                {
                    "check_keys_pattern": "^[a-z_][a-z_0-9]*$",
                    "message": "Property names don't follow snake_case",
                    "name": "check_keys_pattern",
                    "value": "^[a-z_][a-z_0-9]*$",
                    "exceptions": [{
                        "title": "Store Masterdata API",
                        "version": "2"
                    }]
                }
            ]
```

### DEPLOYMENT

#### VERSIONING
- Any update that does not change the functionality of the rule should be a patch

- Any update to the current functionality, i.e. change in the package and local_dev should be a minor change

- New rules / new functionality should be a major version change

#### DEPLOYMENT PROTOCOL
- After making changes to the code, the developer has to change the version number in the package/setup.py file. After the pull request has been merged the package will be deployed to pypi

- After the PR has been merged create a git tag, it will trigger a workflow to create a docker image and push it to ghcr.io. The tag should use semantic versioning: [major.minor.patch](https://docs.npmjs.com/about-semantic-versioning)

##### Note that the pypi version and docker image version are not synced. List the git tags and make changes accordingly