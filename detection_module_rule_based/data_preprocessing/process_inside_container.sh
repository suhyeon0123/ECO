#!/bin/bash

SOURCE_DIR="/source"
CPGS_DIR="/cpgs"
WORK_DIR="/workspace"
MAX_PARALLEL_JOBS=${1:-16}  

total_files=$(find ${SOURCE_DIR} -name "*.cpp" | wc -l)
current=0

process_file() {
  local cpp_file=$1
  local current=$2
  local total=$3
  
  file_name_with_cpp=$(basename "$cpp_file")
  file_name_without_cpp=$(basename "$cpp_file" .cpp)
  echo "Processing: $file_name_with_cpp ($current/$total)"
  
  work_dir_for_file="${WORK_DIR}/${file_name_without_cpp}"
  if [ ! -d "$work_dir_for_file" ]; then
    mkdir -p "$work_dir_for_file"
    echo "Created work directory: $work_dir_for_file"
  fi

  c2cpg.sh ${cpp_file} -o ${CPGS_DIR}/${file_name_without_cpp}.cpg
}

for cpp_file in ${SOURCE_DIR}/*.cpp; do
  if [ -f "$cpp_file" ]; then
    current=$((current + 1))
    
    process_file "$cpp_file" "$current" "$total_files" &
    
    if [ $(jobs -r | wc -l) -ge $MAX_PARALLEL_JOBS ]; then
      wait -n  
    fi
  fi
done

wait 