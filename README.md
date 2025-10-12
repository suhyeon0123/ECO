# ECO - Code Optimization Framework

**ECO** is a comprehensive framework for **fast and reliable C++ code optimization** using Large Language Models (LLMs). The framework combines complementary optimization guidance from static analysis and performance-aware retrieval to enhance Code-LLM optimization capabilities.

Unlike traditional approaches that rely solely on instruction-based prompting, ECO provides **explicit optimization guidance** through two specialized detection modules that identify performance bottlenecks and retrieve relevant optimization strategies.

---

## 🚀 Key Features

- **Dual-Module Architecture**: Combines symbolic static analysis with LLM-based strategy extraction
- **Performance-Aware Guidance**: Provides specific optimization directives rather than generic instructions
- **Comprehensive Evaluation**: Supports multiple prompting strategies for fair comparison
- **Containerized Execution**: Reproducible pipeline with Singularity/Ollama support
- **Scalable Vector Database**: Efficient storage and retrieval of optimization strategies

---

## 📁 Project Structure

```
ECO_code/
├── ECO_data/                     # Datasets and training corpus
│   ├── PIE_test.jsonl           # PIE evaluation dataset (255 samples)
│   ├── codeforce_test.jsonl     # Codeforce evaluation dataset (300 samples)
│   ├── HQ_data.jsonl            # High-quality slow-fast pairs (4,085 pairs)
│   ├── distilled_rationales/    # Extracted optimization strategies
│   └── rag_store/               # Vector database (StrategyDB)
│
├── detection_module_rule_based/  # Symbolic Module (Static Analysis)
│   ├── detect_algorithm_sc/     # Bottleneck detection rules
│   ├── data_preprocessing/      # CPG generation scripts
│   ├── joern.sif               # Joern container image
│   └── prompt_utils.py         # Directive generation
│
├── detection_module_LLM_based/   # Retrieval Module (Strategy Extraction)
│   ├── make_analysis.py         # Strategy extraction with DeepSeek-R1
│   ├── vector_store.py          # Vector database implementation
│   ├── embedding_processor.py   # Text embedding utilities
│   └── prompt.py               # Optimization directive generation
│
└── inference_module/            # Inference Engine (Code Generation)
    ├── main_inference.py        # Core inference orchestrator
    ├── run_ollama_inference.sh  # Execution wrapper
    ├── templates/              # Prompt templates for different strategies
    └── output_format.py        # Result processing utilities
```

---

## 🔄 Framework Workflow

### 1. Data Preparation
- **PIE & Codeforce Datasets**: Curated evaluation benchmarks with test cases
- **HQ Training Corpus**: 4,085 high-quality slow-fast code pairs with performance annotations
- **Strategy Database**: Vector-indexed optimization knowledge extracted from HQ corpus

### 2. Optimization Guidance Generation

#### Symbolic Advisor (Rule-based Detection)
- **Static Analysis**: Uses Joern to generate Code Property Graphs (CPGs)
- **Bottleneck Detection**: Graph queries identify performance issues (I/O, algorithms, data structures)
- **Directive Generation**: Converts detected patterns into natural language optimization guidance

#### ROI Retriever (LLM-based optimization instructions retriever)
- **Optimization Instructions Extraction**: Uses DeepSeek-R1:32B to extract optimization knowledge from slow-fast pairs
- **Vector Database**: Stores strategies using Qodo-Embed-1.5B embeddings
- **Semantic Retrieval**: Retrieves performance-relevant strategies based on input code analysis

### 3. Code Optimization
- **Prompt Integration**: Combines guidance from both modules with various prompting strategies
- **LLM Inference**: Generates optimized code using Code-LLMs (Qwen2.5-Coder, CodeLlama, etc.)
- **Output Processing**: Extracts and formats generated code for evaluation

---

## 🎯 Supported Optimization Strategies

### Baseline Approaches
- **`base`**: Instruction-only optimization without guidance
- **`CoT`**: Chain-of-thought reasoning for step-by-step optimization
- **`ICL`**: In-context learning with random slow-fast examples
- **`retrieve_basic`**: Traditional similarity-based retrieval (RAG)

### ECO Framework Components
- **`rules`**: Symbolic module guidance using static analysis
- **`retrieve_LLM_NLsim`**: Retrieval module with performance-aware strategy matching
- **`hybrid`**: **Complete ECO approach** combining both detection modules

---

## ⚡ Quick Start

### Prerequisites
- **Python ≥ 3.9** with required dependencies
- **Singularity** for containerized execution
- **Ollama** for local LLM inference (or OpenAI API access)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Build Joern container (for symbolic module)
cd detection_module_rule_based
singularity build joern.sif docker://ghcr.io/joernio/joern:master
```

### Basic Usage

#### 1. Prepare Detection Modules
```bash
# Generate CPGs for evaluation datasets
cd detection_module_rule_based
sh data_preprocessing/run.sh

# Extract optimization strategies (one-time setup)
cd ../detection_module_LLM_based
sh extract_optimization_knowledge.sh deepseek-r1:32b ../ECO_data/HQ_data.jsonl

# Build vector database
python vector_store.py \
    --analysis_data_path ../ECO_data/distilled_rationales \
    --store_dir ../ECO_data/rag_store/distilled_deepseek \
    --model_name Qodo/Qodo-Embed-1.5B
```

#### 2. Run Code Optimization
```bash
cd inference_module

# Run instruction-only baseline
sh run_ollama_inference.sh \
    qwen2.5-coder:7b \
    ../ECO_data/PIE_test.jsonl \
    base \
    greedy \
    11434

# Run complete ECO framework
sh run_ollama_inference.sh \
    qwen2.5-coder:7b \
    ../ECO_data/PIE_test.jsonl \
    hybrid \
    greedy \
    11434

# Run symbolic module only
sh run_ollama_inference.sh \
    qwen2.5-coder:7b \
    ../ECO_data/PIE_test.jsonl \
    rules \
    greedy \
    11434
```

---

## 📊 Evaluation Datasets

### PIE Dataset
- **Source**: Derived from [PIE official repository](https://github.com/LearningOpt/pie) testset
- **Size**: 255 evaluation samples with performance annotations
- **Coverage**: 41 algorithmic problems with comprehensive test cases
- **Focus**: Algorithmic optimization and data structure improvements

### Codeforce Dataset
- **Source**: Generated from CodeContest public dataset
- **Size**: 300 evaluation samples across 30 competitive programming problems
- **Coverage**: Diverse optimization scenarios from competitive programming
- **Focus**: Algorithm efficiency and implementation optimization




---

**ECO** provides a comprehensive solution for automated code optimization, combining the precision of static analysis with the intelligence of modern LLMs to deliver fast and reliable optimization results.
