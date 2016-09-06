#!/bin/bash

# 1. Discover directories names
# 2. Validate directories as bags
# 3. Log results
# 4. Email

dateCreated=$(date "+%Y%m%d")

for line in $(ls -d */); do
  bagit.py --validate $line 2>> validate_${dateCreated}.log
done
