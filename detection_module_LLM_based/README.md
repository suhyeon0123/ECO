# ROI Retriever (LLM-based) 

This directory contains the **retrieval module** of ECO, which provides performance-relevant optimization guidance through explicit strategy extraction and semantic retrieval. Unlike traditional retrieval methods that perform surface-level similarity matching between input code and slow-fast pairs, this module extracts explicit optimization strategies from high-quality code pairs and provides performance-relevant strategies along with corresponding slow-fast code examples to Code-LLMs.

The module leverages **DeepSeek-R1:32B** reasoning model for strategy extraction and **Qodo-Embed-1.5B** for vectorization, running through Ollama with Singularity container support.

---

## 1. Directory Layout

### 1.1 Strategy Extraction

| Path | Purpose |
| --- | --- |
| **`make_analysis.py`** | Core script that uses LLM to analyze slow-fast code pairs and extract optimization strategies<br>Uses DeepSeek-R1:32B to generate detailed performance analysis |
| **`templates/`** | Prompt template for runtime bottleneck analysis<br>Guides the LLM to identify performance issues and optimization opportunities |
| **`extract_optimization_knowledge.sh`** | Main orchestration script that sets up Ollama environment and executes strategy extraction<br>Handles SSL certificates and model management |

### 1.2 Vector Database and Retrieval

| Path | Purpose |
| --- | --- |
| **`vector_store.py`** | Disk-backed vector database implementation for strategy storage and retrieval<br>Supports embedding storage in .npz format with JSON metadata<br>Enables performance-relevant similarity search using cosine similarity |
| **`embedding_processor.py`** | Handles text embedding using Qodo-Embed-1.5B model<br>Supports multiple embedding modes: 'full', 'think_tail', 'bullet' |

### 1.3 Prompt Generation

| Path | Purpose |
| --- | --- |
| **`prompt.py`** | Generates optimization directives for Code-LLMs<br>Combines retrieved strategies with slow-fast code pairs<br>Configurable output format (bullet points, code examples, few-shot count) |

---

## 2. Two-Stage Workflow

### Stage 1: Strategy Extraction
Extract explicit optimization strategies from HQ dataset using reasoning LLM:

```bash
# Extract optimization knowledge from HQ slow-fast pairs
sh extract_optimization_knowledge.sh \
    deepseek-r1:32b \
    ../ECO_data/HQ_data.jsonl
```

This process:
1. Sets up Ollama with Singularity container
2. Uses DeepSeek-R1:32B with `templates/` prompt
3. Analyzes each slow-fast pair to extract optimization strategies
4. Outputs results to `../ECO_data/distilled_rationales/`

### Stage 2: Vector Database Creation
Convert extracted strategies into searchable vector database:

```bash
# Build vector store from distilled strategies
python vector_store.py \
    --analysis_data_path ../ECO_data/distilled_rationales \
    --store_dir ../ECO_data/rag_store/distilled_deepseek \
    --model_name Qodo/Qodo-Embed-1.5B \
    --data_type analysis
```

This creates the StrategyDB referenced in `../ECO_data/rag_store/`.

---

## 3. Quick Start

### Prerequisites
- **Singularity** with Ollama container support
- **Python ≥ 3.9** with required packages
- **DeepSeek-R1:32B** model (pulled automatically)
- **Qodo-Embed-1.5B** embedding model

### Complete Pipeline
```bash
# 1. Navigate to the LLM-based detection module
cd detection_module_LLM_based

# 2. Extract optimization strategies (Stage 1)
sh extract_optimization_knowledge.sh \
    deepseek-r1:32b \
    ../ECO_data/HQ_data.jsonl

# 3. Build vector database (Stage 2)
python vector_store.py \
    --analysis_data_path ../ECO_data/distilled_rationales \
    --store_dir ../ECO_data/rag_store/distilled_deepseek \
    --model_name Qodo/Qodo-Embed-1.5B

# 4. Generate optimization directives for input code
python prompt.py --query_code input.cpp --fewshot_k 3
```

---

## 4. Examples

### 4.1 Strategy Extraction Prompt

The `templates/` template guides strategy extraction:



### 4.2 Generated Optimization Directives

Example output from `prompt.py`:

```
1. Input Method: The slow code uses cin >> s, which is slower due to C++ stream overhead. The fast
code replaces with direct getchar() calls, ...
2. String Handling: The slow code uses std::string, which adds memory and function call overhead,
unlike the fixed-size array in the fast code.
3. Output Method: Replacing cout with printf in the fast code results in faster output operations.
```

### 4.3 Retrieval Usage

```python
from detection_module_LLM_based import (
    EmbeddingProcessor, DiskBackedVectorStore, prompt
)

# Initialize components
embedder = EmbeddingProcessor()
store = DiskBackedVectorStore(
    '../ECO_data/rag_store/distilled_deepseek',
    embedder.model_name
)

# Generate performance-relevant optimization directives
input_cpp_code = open('example.cpp').read()
optimization_directives = prompt.generate_retrieval_prompt(
    query=input_cpp_code,
    query_type='code',
    store=store,
    embedder=embedder,
    fewshot_k=3
)

print(optimization_directives)
```

---

## 5. Directory Structure

```
detection_module_LLM_based/
├── README.md                          # This file
├── extract_optimization_knowledge.sh  # Main orchestration script
├── make_analysis.py                   # Strategy extraction with LLM
├── templates/       # Prompt template for analysis
│
├── vector_store.py                    # Vector database implementation
├── embedding_processor.py             # Text embedding utilities
├── prompt.py                          # Optimization directive generation
│
└── (outputs)
    ├── ../ECO_data/distilled_rationales/  # Extracted strategies (Stage 1)
    └── ../ECO_data/rag_store/             # Vector database (Stage 2)
```

---

## Key Features

### Performance-Relevant Retrieval
- **Semantic Strategy Matching**: Retrieves optimization strategies based on performance analysis rather than surface code similarity
- **Explicit Knowledge Extraction**: Uses reasoning LLM to explicitly extract "how-to-optimize" knowledge
- **Combined Strategy + Code**: Provides both optimization strategies and corresponding slow-fast code examples

### Scalable Vector Database
- **Disk-backed Storage**: Efficient storage of embeddings and metadata
- **Fast Similarity Search**: Cosine similarity-based retrieval with parallel processing
- **Flexible Embedding Modes**: Supports different text processing strategies for optimal retrieval

### Integration with ECO Pipeline
- **StrategyDB Creation**: Populates the StrategyDB referenced in `ECO_data/rag_store/`
- **Inference Module Ready**: Generates directives compatible with Code-LLM inference
- **Container Support**: Runs with Singularity/Ollama for reproducible execution

---

## References

- **Ollama**: Local LLM inference framework
- **Qodo-Embed**: High-quality embedding model for code analysis  
- **DeepSeek-R1**: Advanced reasoning model for strategy extraction
- **ECO Paper**: For detailed methodology and evaluation results

---

This retrieval module enables ECO to provide sophisticated, performance-aware optimization guidance by combining explicit strategy extraction with semantic vector search capabilities.