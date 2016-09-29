#!/bin/bash

# 1. Discover directories names
# 2. Validate directories as bags
# 3. Log results

dir_of_bags=$PWD

while getopts ":d:" opt; do
  case $opt in
    d)
      dir_of_bags=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

dateCreated=$(date "+%Y%m%d_%H%M%S")
bags=$(ls -1 -d $dir_of_bags/*/)
i=0

for line in $bags; do
  echo $(date "+%H:%M:%S")": checking" $line
  bagit.py --validate $line 2>> validate_${dateCreated}.log
  ((i++))
  [ "$(($i % 10))" -eq 0 ] && echo $i "bags checked"
done

echo $i "bags checked. Results written to validate_${dateCreated}.log."
