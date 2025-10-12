#!/bin/bash

# sh inference_module/run_ollama_inference.sh qwen2.5-coder:7b BRIDGE_data/PIE_test.jsonl hybrid k_sample

# LLM server info
OLLAMA_CONTAINER=./ollama 
OLLAMA_CACHE="${OLLAMA_DIR:=$HOME/.ollama}"


model=$1
file_path=$2
prompt_strategy=$3
sampling=$4
port=$5
sample_num=$6

# Certificate
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
if [ ! -f "./host_cert.crt" ]; then
    echo "[INFO] Copying SSL cert from container"
    singularity exec --writable $OLLAMA_CONTAINER \
        cp /etc/ssl/certs/ca-certificates.crt ./host_cert.crt
fi
export SSL_CERT_FILE=$(pwd)/host_cert.crt


echo "activate ollama"

# Singularity environment port setting
# set the environment variable clearly and output
export OLLAMA_HOST=0.0.0.0:$port
echo "OLLAMA_HOST environment variable is set to '$OLLAMA_HOST'"

# Singularity execution command simplification
singularity exec --writable --nv \
    --bind $OLLAMA_CACHE:$HOME/.ollama \
    $OLLAMA_CONTAINER ollama serve &

OLLAMA_PID=$!
echo "Ollama started (PID: $OLLAMA_PID)"
echo "Ollama started on port $port"

echo "Waiting for Ollama to be ready..."
sleep 10  # default waiting time

# check the port status using grep
echo "Check the port status of Ollama:"
echo "-----------------------------------"
echo "1. 11434 port status (default Ollama port):"
netstat -tuln 2>/dev/null | grep ":11434" || echo "netstat result not found"

echo "2. $port port status (requested Ollama port):"
netstat -tuln 2>/dev/null | grep ":$port" || echo "netstat result not found"

echo "3. Ollama process information:"
ps aux | grep "ollama serve" | grep -v grep || echo "Ollama process not found"


echo "Waiting for Ollama to be ready..."
while ! singularity exec --writable --nv --bind $OLLAMA_CACHE:$HOME/.ollama $OLLAMA_CONTAINER ollama list &>/dev/null; do
    sleep 5
done
echo "Ollama is ready!"

    

if ! singularity exec --writable --nv --bind $OLLAMA_CACHE:$HOME/.ollama $OLLAMA_CONTAINER ollama list | grep -q $model; then
    singularity exec --writable --nv --bind $OLLAMA_CACHE:$HOME/.ollama $OLLAMA_CONTAINER ollama pull $model
    echo "Model pulled successfully!"
else
    echo "Model $model already exists!"
fi

python3 inference_module/main_inference.py \
    --model_name $model \
    --test_data_path $file_path \
    --prompt_strategy $prompt_strategy \
    --sampling $sampling \
    --port $port \
    --sample_num $sample_num


# result processing script execution
echo "Result formatting processing starts..."
model_name_formatted=$(echo $model | sed 's/:/_/g')
test_name=$(basename "$file_path" | sed 's/_test\.jsonl$//')
folder_name="${test_name}/${prompt_strategy}/${model_name_formatted}_${sampling}"
output_dir="results/inference_results/${folder_name}"
output_file="${output_dir}/sampled_results.jsonl"
echo "output_file: $output_file"

if [ ! -f "$output_file" ]; then
    echo "Output file does not exist. Running output formatting..."
    echo "Executing: python3 inference_module/output_format.py $file_path $output_dir $output_file"
    python3 inference_module/output_format.py $file_path $output_dir $output_file
    echo "Output formatting completed successfully."
else
    echo "Output file already exists: $output_file"
    echo "Skipping output formatting process."
fi
echo "All processing is complete."


# python3 inference_module/output_format.py BRIDGE_data/PIE_test.jsonl results/inference_results/hybrid_qwen2.5-coder:7b_k_sample/results.jsonl

# singularity exec --writable --nv $LLM_server python3 inference_module/main_inference.py $model $file_path $prompt_strategy $sampling
