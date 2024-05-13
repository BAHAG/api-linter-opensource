#!/bin/bash
# get null instead of foler/*.yaml as value of file
shopt -s nullglob
for folder in tests/*; do
    for file in $folder/*.yaml; do
        if [ -z "$file" ]
        then
            echo "No files present in $folder"
        else
            echo "Logs for file: $file"
            python3 local_dev/linter.py -s $file -r ./rules.json -o json
        fi
    done
done
suffix="-output.json"
for folder in tests/*; do
    for file in $folder/*-output.json; do
        if [ -z "$file" ]
        then
            echo "No files in $folder"
        else
            #python3 strip_output.py $file
            # get rid of -output to compare it with the results from diff command
            mv $file ${file%"$suffix"}.json
        fi
    done
done

shopt -u nullglob
