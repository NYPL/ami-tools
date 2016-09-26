#!/bin/bash

# 1. Discover directories names
# 2. Validate directories as bags
# 3. Log results

dateCreated=$(date "+%Y%m%d")
bags=$(ls -d */)
i=0

for line in $bags; do
  echo $(date "+%H:%M:%s")": validating" $line
  bagit.py --validate $line 2>> validate_${dateCreated}.log
  ((i++))
  [ "$(($i % 10))" -eq 0 ] && echo $i "bags validated"
done

echo $i "bags validated"
