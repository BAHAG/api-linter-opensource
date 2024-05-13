#!/bin/bash
# get null instead of foler/*.yaml as value of file
shopt -s nullglob

suffix=".yaml"
flag=false
BLACK='\033[0;30m'
RED='\033[0;31m'
GRAY='\033[0;90m'
for folder in tests/*; do
    for file in $folder/*.yaml; do
        if [ -z "$file" ]
        then
            echo "No files present in $folder"
        else
            echo -e "${BLACK}"
            python3 local_dev/linter.py -s $file -r ./rules.json -o json
            truth_file=${file%"$suffix"}.json
            output_file=${file%"$suffix"}"-output.json"
            # check the difference only if the files exist
            if [ -f $truth_file ] && [ -f $output_file ]; then
                # compares files character by character
                if cmp -s "$truth_file" "$output_file"; then
                    echo -e "${GRAY}The contents of $output_file match $truth_file"
                else
                    echo -e "${RED}The contents of $output_file do not match $truth_file"
                    flag=true
                fi
            fi
        fi
    done
done

NON_ZERO=100
# if flag is set one of the files does not match the truthy file
if $flag; then
    echo "Exiting with non-zero code"
    exit $NON_ZERO
fi

shopt -u nullglob