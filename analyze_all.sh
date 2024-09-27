#!/bin/bash

APPLICATIONS_FILE="./analysed_repositories/all_applications.txt"

while IFS= read -r application; do
    python3 code2dfd.py --github_path "$application"
done < "$APPLICATIONS_FILE"

