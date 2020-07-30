#!/bin/bash

# 1. Discover directories names
# 2. Validate directories as bags
# 3. Log results

dir_of_bags=$PWD
log_dir=$HOME

while getopts 'd:l:' flag; do
  case "${flag}" in
    d) dir_of_bags=${OPTARG} ;;
    l) log_dir=${OPTARG} ;;
    *) error "Unexpected option ${flag}" ;;
  esac
done

dateCreated=$(date "+%Y%m%d_%H%M%S")
bags=$(ls -1 -d $dir_of_bags/*/)
log_path="$log_dir/validate_$dateCreated.log"
i=0

for line in $bags; do
  echo $(date "+%H:%M:%S")": checking" $line
  python3 -m bagit --validate $line 2>> $log_path
  ((i++))
  [ "$(($i % 10))" -eq 0 ] && echo $i "bags checked"
done

echo $i "bags checked. Results written to ${log_path}."
