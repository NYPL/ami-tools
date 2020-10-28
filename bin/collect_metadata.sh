#!/bin/bash

# 1. Discover directories names
# TODO
# 2. Validate directories as bags
# 3. Log results
# 4. Email


find . -iname "*.xlsx" -exec rsync {} ~/dev/bags/excel \;

find . -iname "*.json" -exec rsync {} ~/dev/bags/json \;
