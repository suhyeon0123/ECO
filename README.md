# ECO - Code Optimization Framework via Performance-Aware Prompting

**ECO** is a performance-aware prompting framework for **fast code optimization**. 
It equips code-LLMs with optimization insights tailored to the input code.
Unlike traditional approaches that rely on instruction-based prompting or simple slow-fast code pair examples, ECO offers **explicit optimization guidance** through two specialized detection modules.

## ECO's performance-aware prompting
![motivation](https://github.com/user-attachments/assets/00c3a48b-3fe6-4623-8f46-0ba3805c7a01)


ECO directly provides two complementary forms of guidance: 
1. **Bottleneck Diagnosis**—pinpoints where inefficiencies occur and what type of transformation is required.
2. **Runtime Optimization Instructions** (ROIs)—retrieves concrete, performance-relevant examples distilled from past optimizations.
---

## 🚀 Key Features

- **Performance-aware prompting:** Distills runtime optimization knowledge and composes it into targeted prompts, moving beyond generic instructions.
- **Complementary module design:** Combines a rule-based symbolic advisor for deterministic bottleneck detection and an ROI retriever for context-aware, generalizable guides
- **Model-agnostic, plug-in framework:** Requires no fine-tuning or model-specific adaptation


---

# 🔄 Framework Workflow
![fig2 (1)](https://github.com/user-attachments/assets/4efb88e8-7ae8-430a-84dd-ef37576f270b)
## 1. ROI Distillation
Construct a database of runtime optimization instructions (ROIs) that can serve as prior knowledge for later performance-aware prompting.
- **HQ Code Pairs**: 4,085 high-quality slow–fast code pairs used as historical optimization examples.
- **Distilled ROIs**: Abstracted rationales capturing what changed and why the changes improve efficiency.
- **ROI DB**: A vector-indexed repository of optimization knowledge extracted from the HQ corpus.

Examples of extracted ROIs (runtime optimization instructions)
```
1. **Replacing ‘cout’ with ‘printf’:**
The slow code uses ‘cout’, which involves more overhead due to its object−oriented nature,
while the fast code uses ‘printf’, a function from the C standard library that is more efficient for I/O operations.

2. **Precomputing Multiplication Result:**
In the slow code, the multiplication is done inline within the output statement,
whereas in the fast code, it’s precomputed and stored in a variable (‘mt‘).
This avoids recalculating the result multiple times.

3. **Efficient Loop Conditions:**
The fast code uses ‘i < 10’ instead of ‘i <= 9’, which is slightly more efficient
as comparing against 10 might be faster, though this is a minor optimization.

4. **Reduced Whitespace and Improved Code Structure:**
While not affecting runtime, the fast code has cleaner formatting,
enhancing readability without impacting performance.
```


## 2. Performance-Aware Prompt Generation

### Symbolic Advisor (Rule-based Detection)
- **Static Analysis**: Uses Joern to generate Code Property Graphs (CPGs)
- **Bottleneck Detection**: Graph queries identify performance issues (I/O, algorithms, data structures)
- **Directive Generation**: Converts detected patterns into natural language optimization guidance

#### 🧩 Example of optimization by utilizing Bottleneck Diagnosis from Symbolic Advisor

<table>
<tr>
  <th style="text-align:center;">🐢 Slow Recursive (Before)</th>
  <th style="text-align:center;">⚡ Fast Memoized (After)</th>
</tr>

<tr>
<td style="vertical-align:top; width:50%;">

<pre><code class="language-cpp">
int fib(int n) { 
    if (n <= 1) return n; 
    return fib(n-1) + fib(n-2);
}
</code></pre>

</td>

<td style="vertical-align:top; width:50%;">

<pre><code class="language-cpp">
int fib(int n) { 
    if (n <= 1) return n;
    if (dp[n] != -1) 
        return dp[n];
    dp[n] = fib(n-1) + fib(n-2);
    return dp[n];
}
</code></pre>

</td>
</tr>

<!-- Bottleneck Diagnosis section -->
<tr>
  <th colspan="2" style="text-align:center; padding-top:1em;">🔍 Bottleneck Diagnosis — Recursion Without Memoization</th>
</tr>

<tr>
<td colspan="2" style="padding:0.5em 1em;">
<div style="background:#f9f9f9; border-left:5px solid #2196f3; padding:12px; font-size:90%;">
The following methods are purely recursive: <code>fib()</code> (lines 1–4).<br>
Applying <b>memoization</b> or <b>dynamic programming</b> can significantly reduce execution time.<br><br>
</div>
</td>
</tr>
</table>

---

### ROI Retriever (LLM-based optimization instructions retriever)
- **Optimization Instructions Extraction**: Uses DeepSeek-R1:32B to extract optimization knowledge from slow-fast pairs
- **Vector Database**: Stores strategies using Qodo-Embed-1.5B embeddings
- **Semantic Retrieval**: Retrieves performance-relevant strategies based on input code analysis

#### 🧩 Example: Retrieved ROIs and Coressponding Slow–Fast Code Pair for the input code

<table style="width:100%; table-layout:fixed;">
  <tr>
    <th style="text-align:center; width:33%;">(A) 🧮 Input Code</th>
    <th style="text-align:center; width:33%;">(B-1) 🐢 Retrieved Slow Code</th>
    <th style="text-align:center; width:33%;">(B-2) ⚡ Retrieved Fast Code</th>
  </tr>

  <tr>
    <!-- (A) Input Code -->
    <td style="vertical-align:top; padding:8px;">
<pre><code class="language-cpp">
int main(){
  string s;
  getline(cin, s);
  if ((s.front() == s.back()) ^ (s.length() % 2))
    cout << "Case 1" << endl;
  else
    cout << "Case 2" << endl;
}
</code></pre>
    </td>
    <!-- (B-1) Slow Code -->
    <td style="vertical-align:top; padding:8px;">
<pre><code class="language-cpp">
int main(){
  string s;
  getline(cin, s);
  if ((s.front() == s.back()) ^ (s.length() % 2))
    cout << "Case 1" << endl;
  else
    cout << "Case 2" << endl;
}
</code></pre>
    </td>
    <!-- (B-2) Fast Code -->
    <td style="vertical-align:top; padding:8px;">
<pre><code class="language-cpp">
char s[100005];
int main() {
  int l = 0;
  for (char c = getchar(); c != '\n'; ch = getchar(), l++) {
    s[l] = ch;
  }
  if ((s[0] == s[l-1]) ^ (l % 2))
    printf("Case 1");
  else
    printf("Case 2");
}
</code></pre>
    </td>
  </tr>

  <!-- (C) Runtime Optimization Instruction -->
  <tr>
    <th colspan="3" style="text-align:center; padding-top:12px;">
      (C) 🛠️ Runtime Optimization Instruction
    </th>
  </tr>

  <tr>
    <td colspan="3" style="padding:8px;">
<pre><code class="language-text">
1. Input Method: The slow code uses `cin >> s`, which is slower due to C++ stream overhead. 
   The fast code replaces it with direct `getchar()` calls.
2. String Handling: The slow code uses `std::string`, which adds memory and function call overhead, 
   unlike the fixed-size array in the fast code.
3. Output Method: Replacing `cout` with `printf` in the fast code results in faster output operations.
</code></pre>
    </td>
  </tr>
</table>


---

### 3. Code Optimization
- **Prompt Integration**: Combines guidance from both modules with various prompting strategies
- **LLM Inference**: Generates optimized code using Code-LLMs (Qwen2.5-Coder, CodeLlama, etc.)
- **Output Processing**: Extracts and formats generated code for evaluation

---
## 📊 Evaluation Datasets

### PIE Dataset
- **Source**: Derived from [PIE official repository](https://github.com/LearningOpt/pie) testset
- **Size**: 255 slow codes across 41 algorithmic problems
- **Focus**: In-distribution setting with a similar distribution to the HQ dataset

### Codeforce Dataset
- **Source**: Generated from CodeContest public dataset
- **Size**: 300 slow codes across 30 competitive programming problems
- **Focus**: Out-of-distribution generalization benchmark

---

## 🧠 Experiment Results

### Comparison with Baselines
**Average performance (Best@5).** Inference model: *Qwen2.5-coder:7b*.

| Methods         | ACC (%)            | SP             | OPT (%)          |
|-----------------|--------------------|-----------------|------------------|
| Instruction-only| 68.12 (±1.54)      | 1.44× (±0.03)   | 15.92 (±1.20)    |
| CoT             | 63.61 (±1.21)      | 1.39× (±0.02)   | 15.18 (±0.79)    |
| ICL             | 70.75 (±1.24)      | 1.82× (±0.04)   | 23.10 (±0.94)    |
| RAG             | 64.51 (±1.78)      | 2.51× (±0.12)   | 30.31 (±1.12)    |
| Supersonic      | 14.75 (±0.61)      | 1.01× (±0.01)   | 0.20 (±0.20)     |
| SBLLM           | 55.80 (±3.15)      | 1.22× (±0.04)   | 7.61 (±0.95)     |
| <mark>ECO</mark>| <mark>74.24 (±1.46)</mark> | <mark>3.26× (±0.09)</mark> | <mark>48.04 (±1.17)</mark> |

ECO achieves overwhelmingly superior SP (speedup) and OPT (optimization rate) with minimal loss in correctness!

### Generalizability of ECO
Evaluation on the in-distribution **PIE** and the out-of-distribution **Codeforce**, using closed-source models.

<table>
  <thead>
    <tr>
      <th rowspan="2">Model</th>
      <th rowspan="2">Prompting</th>
      <th colspan="3">PIE (Best@5)</th>
      <th colspan="3">Codeforce (Best@5)</th>
    </tr>
    <tr>
      <th>ACC (%)</th><th>SP</th><th>OPT (%)</th>
      <th>ACC (%)</th><th>SP</th><th>OPT (%)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2"><b>GPT-4o-mini</b></td>
      <td>Instruction-only</td>
      <td>83.53</td><td>1.53×</td><td>19.61</td>
      <td>49.23</td><td>1.01×</td><td>0.33</td>
    </tr>
    <tr>
      <td><mark>ECO</mark></td>
      <td><mark>94.51</mark></td><td><mark>3.97×</mark></td><td><mark>60.78</mark></td>
      <td><mark>59.93</mark></td><td><mark>2.01×</mark></td><td><mark>18.70</mark></td>
    </tr>
    <tr>
      <td rowspan="2"><b>GPT-o4-mini</b></td>
      <td>Instruction-only</td>
      <td><mark>95.29</mark></td><td>1.99×</td><td>36.08</td>
      <td><mark>65.63</mark></td><td>1.41×</td><td>7.33</td>
    </tr>
    <tr>
      <td><mark>ECO</mark></td>
      <td><mark>97.25</mark></td><td><mark>7.81×</mark></td><td><mark>84.71</mark></td>
      <td><mark>73.67</mark></td><td><mark>4.55×</mark></td><td><mark>42.07</mark></td>
    </tr>
  </tbody>
</table>

While instruction-only prompting yields only marginal speedups under 2×, which is the standard way of utilizing LLMs.
ECO improves substantially, with GPT-o4-mini achieving a remarkable **7.81×** speedup on the PIE dataset!!

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


## 📚 Citation
```bibtex
@misc{kim2025eco,
  title={ECO: Enhanced Code Optimization via Performance-Aware Prompting for Code-LLMs},
  author={Kim, Su-Hyeon and Hahn, Joonghyuk and Cha, Sooyoung and Han, Yo-Sub},
  eprint={2510.10517},
  archivePrefix={arXiv},
  url={https://arxiv.org/abs/2510.10517},
  year={2025}
}
```
Paper link: [arXiv:2510.10517](https://arxiv.org/abs/2510.10517)

---

**ECO** provides a comprehensive solution for automated code optimization, combining the precision of static analysis with the intelligence of modern LLMs to deliver fast and reliable optimization results.
