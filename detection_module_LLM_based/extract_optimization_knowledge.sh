#!/bin/bash

# sh detection_module_LLM_based/extract_optimization_knowledge.sh deepseek-r1:32b BRIDGE_data/HQ_data.jsonl

model=$1
file_path=$2
LLM_server=./ollama


# Certificate
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
if [ ! -f "./host_cert.crt" ]; then
    echo "[INFO] Copying SSL cert from container"
    singularity exec --writable $LLM_server \
        cp /etc/ssl/certs/ca-certificates.crt ./host_cert.crt
fi
export SSL_CERT_FILE=$(pwd)/host_cert.crt


echo "activate ollama"
singularity exec --writable --nv ollama ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
while ! singularity exec --writable --nv ollama ollama list &>/dev/null; do
    sleep 5
done
echo "Ollama is ready!"

if ! singularity exec --writable --nv ollama ollama list | grep -q $model; then
    singularity exec --writable --nv ollama ollama pull $model
    echo "Model pulled successfully!"
else
    echo "Model $model already exists!"
fi

python3 detection_module_LLM_based/make_analysis.py --model $model --input_file_path $file_path

