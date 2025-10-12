#!/bin/bash

CPGS_DIR="/cpgs"
WORK_DIR="/workspace"
RESULTS_DIR="/results"
# MAX_PARALLEL_JOBS=${1:-4}  
MAX_PARALLEL_JOBS=1

total_files=$(find ${CPGS_DIR} -name "*.cpg" | wc -l)
current=0

echo "total_files: ${total_files}"

# define the function for processing the file
process_file() {
  local cpg_file=$1
  local current=$2
  local total=$3
  
  file_name_with_ext=$(basename "$cpg_file")
  file_name="${file_name_with_ext%.cpg}"

  echo "Processing: $file_name_with_ext ($current/$total)"

  # create the result directory
  output_path="${RESULTS_DIR}/${file_name}"
  mkdir -p "$output_path"

  joern \
  --script detect_algorithm_sc/test.sc \
  --param cpgPath="${CPGS_DIR}/${file_name_with_ext}" \
  --param outputPath="$output_path" \
  --import detect_algorithm_sc/rules_algorithms.sc \
  --import detect_algorithm_sc/rules_library_usage.sc \
  --import detect_algorithm_sc/rules_data_structure.sc \
  --import detect_algorithm_sc/rules_others.sc

}

# # for debugging
# debug_file="${CPGS_DIR}/s043659085.cpg"
# process_file "$debug_file" 1 1
# exit 0


for cpg_file in ${CPGS_DIR}/*.cpg; do
  if [ -e "$cpg_file" ]; then
    current=$((current + 1))

    echo "current: ${current}"
    
    process_file "$cpg_file" "$current" "$total_files" &
    
    if [ $(jobs -r | wc -l) -ge $MAX_PARALLEL_JOBS ]; then
      wait -n  
    fi
  fi
done

wait 