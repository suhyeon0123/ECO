# ECO_data

This directory bundles all auxiliary data required to **re‑run the experiments in
"ECO: Enhanced Code Optimization via Performance-Aware Prompting for Code-LLMs"**

You can first download data from [Google Drive](https://drive.google.com/drive/folders/1OyM9iqQdmFaOyrJ8r9KysSc7JCqTgXvJ?usp=sharing)

---

## 1. Directory Layout

### 1.1 Evaluation Datasets

This repository contains two evaluation datasets for code optimization benchmarking:

#### PIE Dataset
- **PIE_test.jsonl**: 255 evaluation samples
- **PIE_sourcecodes/**: Input C++ source code files (255 files)
- **PIE_test_cases/**: Test cases for correctness verification (41 problems, 10 test cases per problem)

The PIE dataset is derived from the [PIE official repository](https://github.com/LearningOpt/pie) testset, with additional preprocessing to address data imbalance issues. Details are described in our paper.

#### Codeforce Dataset  
- **codeforce_test.jsonl**: 300 evaluation samples
- **codeforce_sourcecodes/**: Input C++ source code files (300 files)
- **codeforce_test_cases/**: Test cases for correctness verification (30 problems, 10 test cases per problem)

The Codeforce dataset is generated from the CodeContest public dataset, with up to 10 samples derived per problem.

### 1.2 Training and Strategy Data

| Path | Purpose |
| --- | --- |
| **`HQ_data.jsonl`** | 4,085 high‑quality slow‑fast pairs with highest speedup ratios from PIE dataset<br>Each record contains:<br>• `slow_code` & `fast_code` (source code)<br>• `speedup` (Gem5 cycles) |
| **`distilled_rationales/`** | Strategy explanations extracted from HQ dataset using `detection_module_LLM_based/make_analysis.py`<br>Each line contains a concise, LLM‑generated explanation of optimization strategies |
| **`rag_store/`** | Vector database of the distilled strategies (StrategyDB in the paper)<br>Created by embedding the extracted strategies from `distilled_rationales/` |

### 1.3 Preprocessing Scripts

| File | Purpose |
| --- | --- |
| **`preprocess_codeforce.py`** | Preprocessing script to generate the Codeforce dataset from CodeContest public dataset |

---

## 2. File Formats


### 2.1 Test Case Schema

```json
{
  "input":  "5\n1 2 3 4 5\n",
  "output": "15\n"
}
```

### 2.2 Evaluation Dataset Format

#### PIE_test.jsonl / codeforce_test.jsonl
```json
{
  "src_id": "s166226200",
  "problem_id": "p02676", 
  "src_code": "#include<iostream>\n...",
  "time_limit": 2,
  "cf_tags": ["binary search", "implementation", "sortings"]
}
```

---

## 3. Directory Structure

```
ECO_data/
├── README.md                    # This file
├── HQ_data.jsonl               # High-quality slow-fast pairs (4,085 pairs)
├── preprocess_codeforce.py     # Codeforce data preprocessing script
│
├── PIE_test.jsonl              # PIE evaluation set (255 samples)
├── PIE_sourcecodes/            # PIE C++ source code files
├── PIE_test_cases/             # PIE test cases (41 problems × 10 cases)
│
├── codeforce_test.jsonl        # Codeforce evaluation set (300 samples)  
├── codeforce_sourcecodes/      # Codeforce C++ source code files
├── codeforce_test_cases/       # Codeforce test cases (30 problems × 10 cases)
│
├── distilled_rationales/       # Extracted optimization strategies
└── rag_store/                  # StrategyDB - vectorized strategy database
```

---

This data is organized to fully reproduce the experiments described in the BRIDGE paper. For questions or issues, please refer to the paper or open an issue in the repository.