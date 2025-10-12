#!/bin/bash


workspace="./workspace"
cpg_path="./cpgs"
result_folder="./detect_results"

# create the result folder if not exists
if [ ! -d "$result_folder" ]; then
  echo "create the result folder..."
  mkdir -p "$result_folder"
fi

if [ ! -d "tmp" ]; then
  mkdir -p "tmp"
fi

# Step2.
echo "Starting singularity container to processing detecting by rules"
CMD="singularity exec \
  --bind tmp:/tmp \
  --bind ${cpg_path}:/cpgs \
  --bind ${result_folder}:/results \
  --bind ./detect_algorithm_sc/process_inside_container.sh:/process_inside_container.sh \
  joern.sif \
  /process_inside_container.sh"
echo "CMD: $CMD"
eval $CMD



# input_path="s004830098.cpg"
# # input_path="$workspace/s004830098.cpg"
# # input_path="$workspace/s004830098.cpg/s004830098.cpg.bin"
# output_path="$result_folder/s004830098"



# # create the result folder if not exists
# if [ ! -d "$output_path" ]; then
#   echo "create the result folder..."
#   mkdir -p "$output_path"
# fi


# # Joern script to run
# echo "Joern script to run..."
# singularity exec \
#   --bind ./tmp:/tmp \
#   --bind $result_folder:/results \
#   --bind $cpg_path:/cpgs \
#   joern.sif joern \
#   --script detect_algorithm_sc/test.sc \
#   --param cpgPath="$cpg_path/$input_path" \
#   --param outputPath="$output_path" \
#   --import detect_algorithm_sc/rules_algorithms.sc \
#   --import detect_algorithm_sc/rules_library_usage.sc \
#   --import detect_algorithm_sc/rules_data_structure.sc \
#   --import detect_algorithm_sc/rules_others.sc
  


echo "analysis is completed. the results are in $output_path"