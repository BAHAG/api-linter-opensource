import re

# scan the raw spec file line by line and log every line matching the pattern
def check_line_pattern(spec_file, message, severity, logger, id, pattern):
    regex = re.compile(pattern)
    with open(spec_file) as yf:
        for line_num, line in enumerate(yf, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if regex.search(line):
                logger.log_with_line_number_key_and_value(line_num, severity, message, id, "$ref", stripped)
