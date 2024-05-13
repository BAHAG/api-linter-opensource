import re

"""START: Utility functions for performing checks on required_path"""

# check if the pattern matches the property value
def pattern_matching(pattern, property_, line_number, severity, message, id, error_logger):
    if not re.match(pattern, property_):
        error_logger.log_with_line_number(line_number, severity, message, id)

# check if the value in spec file is matches one of the predefined values
def allowed_values(all_values, value, line_number, severity, message, id, error_logger):
    if not (value in all_values):
        error_logger.log_with_line_number(line_number, severity, message, id)

# check if semantic versioning is >= version specified in the rules.json
def gte(check, spec_value, line_number, severity, message, id, error_logger):
    check = int("".join(check.split(".")))
    try:
        spec_value = int("".join(spec_value.split(".")))

        if spec_value >= check:
            return
        error_logger.log_with_line_number(line_number, severity, message, id)
    except:
        error_logger.log_with_line_number(line_number, severity, message, id)

# check if the value matches the predifined string
def string_match(check, spec_value, line_number, severity, message, id, error_logger):
    if check != spec_value:
        error_logger.log_with_line_number(line_number, severity, message, id)
"""END"""