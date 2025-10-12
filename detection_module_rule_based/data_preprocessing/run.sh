#!/bin/bash

# Check current directory
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*detection_module_rule_based$ ]]; then
  echo "ERROR: This script must be run from the detection_module folder."
  echo "Current path: $CURRENT_DIR"
  echo "Usage: cd path/to/detection_module && sh ./data_preprocessing/run.sh"
  exit 1
fi


JSONL_FOLDERS=("../../BRIDGE_data/codeforce_test.jsonl" "../../BRIDGE_data/PIE_test.jsonl")
SOURCE_FOLDERS=("../../BRIDGE_data/codeforce_sourcecodes" "../../BRIDGE_data/PIE_sourcecodes")

for i in "${!JSONL_FOLDERS[@]}"; do
  JSONL_FOLDER="${JSONL_FOLDERS[$i]}"
  SOURCE_FOLDER="${SOURCE_FOLDERS[$i]}"

  # Step1. Save source code
  python data_preprocessing/extract_source.py $JSONL_FOLDER $SOURCE_FOLDER

  CPGS_FOLDER="./cpgs"
  WORK_DIR="./workspace"

  if [ ! -d "$CPGS_FOLDER" ]; then
    mkdir -p "$CPGS_FOLDER"
  fi

  if [ ! -d "$WORK_DIR" ]; then
    mkdir -p "$WORK_DIR"
  fi

  if [ ! -d "tmp" ]; then
    mkdir -p "tmp"
  fi


  # Step2. Generate temporary CPG files using c2cpg
  echo "Starting singularity container to process all files..."
  CMD="singularity exec \
    --bind tmp:/tmp \
    --bind ${SOURCE_FOLDER}:/source \
    --bind ${CPGS_FOLDER}:/cpgs \
    --bind ./data_preprocessing/process_inside_container.sh:/process_inside_container.sh \
    joern.sif \
    /process_inside_container.sh"
  echo "CMD: $CMD"
  eval $CMD

done

  
# Step3. Save to workspace using importCpg
echo "Starting singularity container to process all files..."
CMD="singularity exec \
  --bind tmp:/tmp \
  --bind ${CPGS_FOLDER}:/cpgs \
  --bind ./data_preprocessing/process_inside_container2.sh:/process_inside_container2.sh \
  joern.sif \
  /process_inside_container2.sh"
echo "CMD: $CMD"
eval $CMD


echo "All datasets processed!"