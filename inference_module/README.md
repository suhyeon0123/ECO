# Inference Module

This directory contains the **inference module** of ECO, which serves as the central orchestrator for code optimization using various prompting strategies. The module integrates guidance from both the symbolic (rule-based) and retrieval (LLM-based) modules to generate optimized code through Code-LLMs, while also supporting generic prompting techniques for comprehensive evaluation.

The ECO approach provides **complementary optimization directives** derived from the input code through both detection modules, which are then combined and fed to Code-LLMs as guidance for generating functionally equivalent but more efficient code.

---

## 1. Directory Layout

### 1.1 Core Inference Components

| Path | Purpose |
| --- | --- |
| **`main_inference.py`** | Main inference engine that orchestrates different prompting strategies<br>Handles model communication, prompt generation, and result collection |
| **`run_ollama_inference.sh`** | Shell script for running inference with Ollama/Singularity environment<br>Manages container setup, model loading, and batch processing |

### 1.2 Output Processing

| Path | Purpose |
| --- | --- |
| **`output_format.py`** | Post-processing utilities for extracting and formatting generated code<br>Handles code block extraction from LLM responses and result standardization |
| **`utils.py`** | Utility functions for loading prompt templates and data processing |

### 1.3 Prompt Templates

| Path | Purpose |
| --- | --- |
| **`templates/`** | JSON templates for different prompting strategies<br>• `base.json`: Instruction-only baseline<br>• `rules.json`: Symbolic module integration<br>• `ICL.json`: In-context learning with examples<br>• `hybrid.json`: Combined symbolic + retrieval guidance<br>• Additional CoT and retrieval variants |

---

## 2. Supported Prompting Strategies

### 2.1 Baseline Approaches

| Strategy | Description | Template |
| --- | --- | --- |
| **`base`** | Instruction-only baseline without any guidance | `base.json` |
| **`CoT`** | Chain-of-thought reasoning for step-by-step optimization | `CoT.json` |
| **`ICL`** | In-context learning with random slow-fast code pair examples | `ICL.json` |
| **`retrieve_basic`** | Basic similarity-based retrieval (RAG) using code embeddings | HQ_data.jsonl |


### 2.3 ECO Framework Components

| Strategy | Description | Integration |
| --- | --- | --- |
| **`rules`** | Symbolic module guidance using rule-based bottleneck detection | detection_module_rule_based |
| **`retrieve_LLM_NLsim`** | Retrieval module with performance-relevant strategy matching | detection_module_LLM_based |
| **`hybrid`** | **Complete ECO approach** combining both symbolic and retrieval modules | Both detection modules |


---

## 3. Key Parameters

### 3.1 Required Arguments

| Parameter | Description | Example Values |
| --- | --- | --- |
| **`--model_name`** | Code-LLM model to use for optimization | `codellama:7b`, `qwen2.5coder:7b` |
| **`--test_data_path`** | Path to evaluation dataset | `../ECO_data/PIE_test.jsonl` |
| **`--prompt_strategy`** | Optimization approach to use | `base`, `rules`, `hybrid` |
| **`--sampling`** | Sampling strategy for generation | `greedy`, `k_sample` |


---

## 4. Quick Start

### Prerequisites
- **Singularity** with Ollama container support
- **Evaluation datasets** available in `../ECO_data/`
- **Detection modules** properly set up (for ECO strategies)

### Basic Usage
```bash
# Navigate to inference module
cd inference_module

# Run instruction-only baseline
sh run_ollama_inference.sh \
    codellama:7b \
    ../ECO_data/PIE_test.jsonl \
    base \
    greedy \
    11434

# Run ECO hybrid approach
sh run_ollama_inference.sh \
    codellama:7b \
    ../ECO_data/PIE_test.jsonl \
    hybrid \
    greedy \
    11434

# Run symbolic module only
sh run_ollama_inference.sh \
    codellama:7b \
    ../ECO_data/PIE_test.jsonl \
    rules \
    greedy \
    11434
```

### Direct Python Usage
```bash
# Direct inference without shell wrapper
python main_inference.py \
    --model_name codellama:7b \
    --test_data_path ../ECO_data/PIE_test.jsonl \
    --prompt_strategy hybrid \
    --sampling greedy \
    --port 11434
```

---

## 5. Examples

### 5.1 Prompt Strategy Comparison

**Base (Instruction-only):**
```
Optimize the program and provide a more efficient version.

### Original Code:
[input code]

### Optimized Code:
```

**Rules (Symbolic Module):**
```
Given a program and optimization tips, optimize the program and provide a more efficient version.

The following IO library such as cin, cout, or stringstream usage relies on slow operations:
- Variable: cin, Line: 12
In such cases, replacing them with faster alternatives such as scanf, printf can improve performance.

### Original code:
[input code]

### Optimized Code:
```

**Hybrid (Complete ECO):**
```
Given a program and optimization tips, optimize the program and provide a more efficient version.

Followings are retrieved examples for optimization.

### Strategy 1: I/O Optimization
- Replace cin/cout with scanf/printf for faster input/output
[slow-fast code example]

### Strategy 2: Algorithm Enhancement  
- Use memoization to avoid redundant recursive calls
[slow-fast code example]

Optimization tips for the given code:
[Symbolic module guidance]

Now, optimize the following code.

### Original code:
[input code]

### Optimized Code:
```



## 6. Directory Structure

```
inference_module/
├── README.md                    # This file
├── main_inference.py           # Core inference engine
├── run_ollama_inference.sh     # Execution wrapper script
├── output_format.py            # Result processing utilities
├── utils.py                    # Helper functions
│
├── templates/                  # Prompt templates for different strategies
│   ├── base.json              # Instruction-only baseline
│   ├── rules.json             # Symbolic module integration
│   ├── ICL.json               # In-context learning
│   ├── hybrid.json            # Complete ECO approach
│   └── ...
│
└── (outputs)
    └── results/inference_results/  # Generated optimization results
        └── [strategy]/[model]_[sampling]/  # Organized by configuration
```


---

This inference module serves as the final integration point for ECO, demonstrating how complementary optimization guidance can be effectively combined to enhance Code-LLM performance on optimization tasks.
