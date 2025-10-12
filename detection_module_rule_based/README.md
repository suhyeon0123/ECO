# Symbolic Advisor (Rule-based)

This directory contains the **symbolic module** of ECO, which performs static analysis on C++ code to identify performance bottlenecks and generate optimization directives. The module operates in two stages: (1) rule-based graph queries to extract bottlenecks from Code Property Graphs (CPGs), and (2) template-based generation of explainable natural language optimization directives that can be fed to Code-LLMs.

The module leverages [Joern](https://joern.io/), a powerful static analysis tool, running within a Singularity container to ensure reproducible analysis across different environments.

---

## 1. Directory Layout

### 1.1 Data Preprocessing

| Path | Purpose |
| --- | --- |
| **`data_preprocessing/`** | Scripts to extract source codes from evaluation datasets and generate CPG files<br>• Processes PIE_test and codeforce_test datasets<br>• Outputs: `cpgs/` folder (parsed CPG files) and `workspace/` folder |

### 1.2 Bottleneck Detection

| Path | Purpose |
| --- | --- |
| **`detect_algorithm_sc/`** | Scala graph query implementations for bottleneck detection<br>• `rules_algorithms.sc`: Algorithmic inefficiencies (recursion, arithmetic operations)<br>• `rules_data_structure.sc`: Suboptimal container usage (vectors, maps)<br>• `rules_library_usage.sc`: Slow I/O and library calls<br>• `rules_others.sc`: Miscellaneous patterns (loop-invariant operations)<br>• `test.sc`: Entry-point script that dispatches to rule files<br>• `test.sh`: Main launcher script |

### 1.3 Directive Generation

| Path | Purpose |
| --- | --- |
| **`NL_descriptions.json`** | Templates for converting detected bottlenecks into natural language directives<br>Maps bottleneck categories to explainable optimization suggestions |
| **`prompt_utils.py`** | Python utility to generate final optimization directives<br>Combines detection results with templates to produce LLM-ready prompts |

### 1.4 Container and Outputs

| Path | Purpose |
| --- | --- |
| **`joern.sif`** | Singularity container image for Joern static analysis tool |
| **`detect_results/`** | Output directory containing bottleneck detection results<br>Each source file gets a subdirectory with JSON files for each rule category |
| **`cpgs/`** | Generated Code Property Graph files (created by data preprocessing) |
| **`workspace/`** | Joern workspace directory (created by data preprocessing) |

---

## 2. Quick Start

### Prerequisites
Ensure you have Singularity installed and the evaluation datasets available.

```bash
# 1. Navigate to the detection module directory
cd detection_module_rule_based

# 2. Build the Joern container image
singularity build joern.sif docker://ghcr.io/joernio/joern:master

# 3. Generate CPG files from evaluation datasets
sh data_preprocessing/run.sh

# 4. Run bottleneck detection on all CPG files
sh detect_algorithm_sc/test.sh

# 5. Generate optimization directives for a specific source file
python prompt_utils.py <code_id>
```

---

## 3. Examples

### 3.1 Graph Query Example

Here's an example of a Scala graph query that detects recursive functions without memoization:

```scala
def detectSlowRecursive(cpg: Cpg): List[Method] = {
  // Find methods that call themselves (recursive)
  val recursiveMethods = cpg.method
    .filter(m => !m.isExternal && m.name != "<global>")
    .filter(func => func.ast.isCall.name(func.name).nonEmpty)
    .l

  // Filter methods that don't use memoization patterns
  recursiveMethods.filter { method =>
    val hasIndirectAccess = method.ast.isCall.name("<operator>.indirectIndexAccess")
      .filter(call => !call.astParent.assignment.exists(assign => assign.argument(1) == call))
      .nonEmpty
    
    !hasIndirectAccess  // No memoization detected
  }
}
```

### 3.2 Optimization Directive Examples

When bottlenecks are detected, the system generates natural language directives like these:

**Example 1: Recursive Function Detection**
```
The following methods appear to be purely recursive:
- Method: fibonacci, Lines 15–25
Memoization or DP optimization can significantly reduce the time complexity of recursive functions.
```

**Example 2: I/O Library Optimization**
```
The following IO library such as cin, cout, or stringstream usage relies on slow operations:
- Variable: cin, Line: 12
- Variable: cout, Line: 18
In such cases, replacing them with faster alternatives such as scanf, printf can improve performance.
```

**Example 3: Bitwise Operation Opportunities**
```
The following operations can be replaced with faster bitwise equivalents:
- Operator: *, Line: 42
- Operator: %, Line: 45
Certain arithmetic operations such as multiplication, division, and modulo can be replaced by faster bitwise operations (e.g., shift, AND).
```

---

## 4. Directory Structure

```
detection_module_rule_based/
├── README.md                           # This file
├── joern.sif                          # Joern container image
├── prompt_utils.py                     # Directive generation utility
├── NL_descriptions.json               # Optimization directive templates
│
├── data_preprocessing/                 # CPG generation from datasets
│   ├── run.sh                         # Main preprocessing script
│   ├── extract_source.py              # Source code extraction
│   ├── import_cpg.sc                  # Joern CPG import script
│   └── process_inside_container.sh    # Container execution helper
│
├── detect_algorithm_sc/               # Bottleneck detection rules
│   ├── test.sh                       # Main detection launcher
│   ├── test.sc                       # Entry-point Joern script
│   ├── rules_algorithms.sc           # Algorithmic inefficiencies
│   ├── rules_data_structure.sc       # Container usage patterns
│   ├── rules_library_usage.sc        # I/O and library optimizations
│   ├── rules_others.sc               # Miscellaneous patterns
│   └── process_inside_container.sh   # Container execution helper
│
├── cpgs/                             # Generated CPG files (auto-created)
├── workspace/                        # Joern workspace (auto-created)
└── detect_results/                   # Detection output (auto-created)
    └── <code_id>/                    # Per-file results
        ├── slow_recursive.json       # Recursive function results
        ├── cin_cout.json            # I/O optimization results
        ├── slow_vectors.json        # Vector usage results
        └── ...                      # Other rule category results
```

---

## References

- **Joern**: [https://joern.io/](https://joern.io/) - Open-source code analysis platform
- **Singularity**: Container runtime for HPC environments
- **ECO Paper**: For detailed methodology and evaluation results

---

This symbolic module provides the foundation for ECO's static analysis capabilities, enabling automated detection of performance bottlenecks and generation of actionable optimization guidance for Code-LLMs.