#!/bin/bash

CPGS_DIR="/cpgs"
WORK_DIR="/workspace"
MAX_PARALLEL_JOBS=${1:-4}  

total_files=$(find ${CPGS_DIR} -name "*.cpg" | wc -l)
current=0

process_file() {
  local cpg_file=$1
  local current=$2
  local total=$3
  
  file_name_with_cpg=$(basename "$cpg_file")
  echo "Processing: $file_name_with_cpg ($current/$total)"

  joern --script data_preprocessing/import_cpg.sc --param cpgPath=${CPGS_DIR}/${file_name_with_cpg}
}



for cpg_file in ${CPGS_DIR}/*.cpg; do
  if [ -f "$cpg_file" ]; then
    current=$((current + 1))
    
    process_file "$cpg_file" "$current" "$total_files" &
    
    if [ $(jobs -r | wc -l) -ge $MAX_PARALLEL_JOBS ]; then
      wait -n  
    fi
  fi
done

wait 