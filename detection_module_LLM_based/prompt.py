"""
Function: generate_prompt
Purpose: Generate a prompt for code optimization using retrieved few-shot examples
Configurable options:
- include_bullet_only: include only natural language optimization bullets (default: True)
- include_code_pair: optionally include full original slow-fast code example for each bullet
- fewshot_k: number of retrieved examples to include (1-3 typical)
"""

from typing import List, Literal, Optional
import json
import sys
import os   
import random


sys.path.append('.')
from detection_module_LLM_based.embedding_processor import EmbeddingProcessor, EmbeddingMode 
from detection_module_LLM_based.vector_store import DiskBackedVectorStore


import re

def remove_c_cpp_comments(code):
    """
    get rid of all comments in C / C++ code
    (except for string internal comments)
    """

    # protect the string first
    pattern = r'(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*)'

    def replacer(match):
        if match.group(2) is not None:
            return ''  # if it is a comment, remove it
        else:
            return match.group(1)  # if it is a string, keep it

    return re.sub(pattern, replacer, code, flags=re.DOTALL)



def load_code_pair(train_data_path: str) -> dict:
    data = []
    with open(train_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    
    code_pair = []
    for d in data:
        code_pair.append((remove_c_cpp_comments(d['src_code']), remove_c_cpp_comments(d['tgt_code'])))
    return code_pair

def load_distilled_data(rag_store_path):
    data_path = os.path.join(rag_store_path, 'metadata.json')
    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    distill_data = {}
    for d in data:
        analysis_id = d['analysis_id'].split('.')[0]
        if analysis_id not in distill_data:
            distill_data[analysis_id] = {
                d['mode'] : d['text']
            }
        else:
            distill_data[analysis_id][d['mode']] = d['text']

    return distill_data


def get_code_pair(r, code_pair):
    if not isinstance(r['analysis_id'], int) and '.json' in r['analysis_id'] :
        analysis_id = int(r['analysis_id'].split('.')[0]) - 1    # 1-based
    else:
        analysis_id = int(r['analysis_id'])

    slow_code = code_pair[analysis_id][0]
    fast_code = code_pair[analysis_id][1]
    return slow_code, fast_code

def generate_retrieval_prompt(
    query: str,
    query_type: Literal['code', 'NL'],
    store,  # instance of DiskBackedVectorStore
    embedder,  # instance of EmbeddingGenerator
    fewshot_k: int = 2,
    enable_modes: List[EmbeddingMode] = ['full', 'think_tail', 'bullet'],
    code_pair: dict = None,
    distill_data: dict = None,
    retrieve_additional_info: bool = False,
    given_code_analysis: str = None
) -> str:
    """
    Generate prompt for optimization using retrieved bullet/code examples.

    Args:
        query_code (str): The code to be optimized
        store (DiskBackedVectorStore): Retrieved vector store
        embedder (EmbeddingGenerator): Model to embed the query
        fewshot_k (int): Number of examples to retrieve (default: 3)
        enable_modes (List[EmbeddingMode]): List of modes to use or None
        code_pair (dict): 

    Returns:
        str: Formatted prompt (ready to fill in {retrieved_optimizations})
    """

    if query_type == 'NL':
        query = given_code_analysis
        
        # query = src analysis nl


    # retrieved = store.search(
    retrieved = store.search_parallel(
        query=query,
        embedder=embedder,
        mode_filter=enable_modes,
        retreived_k=fewshot_k,
        n_workers=4
    )                   # text, similarity, entry_id, mode, analysis_id, index


    parts = []
    for idx, r in enumerate(retrieved):
        # Code pair
        slow_code, fast_code = get_code_pair(r, code_pair)
        
        part = f"\n\n### Original Example Code{idx+1}:\n```\n{slow_code}\n```\n### Optimized Example Code{idx+1}:\n```\n{fast_code}\n```"
        parts.append(part.strip())

        # Additional info (Analysis results)
        if retrieve_additional_info:

            if query_type == 'code':
                text = distill_data[str(r['analysis_id']+1)]['think_tail']  # +1 cause analysis_id is 1-based
                part = text
                parts.append(part.strip())
                
                
            elif query_type == 'NL':
                text = r['text']
                # if the text is a list, process it
                if isinstance(text, list):
                    text = ' '.join(text)
                part = text
                parts.append(part.strip())
    return '\n\n'.join(parts)
    
    
def generate_random_retrieval_prompt(
    fewshot_k: int = 2,
    code_pair: dict = None,
    distill_data: dict = None,
    retrieve_additional_info: bool = False
) -> str:
    """
    Generate prompt for optimization using randomly selected code pair examples.

    Args:
        fewshot_k (int): Number of random examples to retrieve (default: 2)
        code_pair (dict): Dictionary of code pairs (slow, fast) 
        distill_data (dict): Distilled analysis data
        retrieve_additional_info (bool): Whether to include additional analysis info

    Returns:
        str: Formatted prompt with random code examples
    """
    
    # Get total number of code pairs
    total_pairs = len(code_pair)
    
    # Random sampling of indices without replacement
    selected_indices = random.sample(range(total_pairs), fewshot_k)
    
    parts = []
    for display_idx, original_idx in enumerate(selected_indices):
        # Get the code pair using the original index
        slow_code, fast_code = code_pair[original_idx]
        
        # Code pair
        part = f"\n\n### Original Example Code{display_idx+1}:\n```\n{slow_code}\n```\n### Optimized Example Code{display_idx+1}:\n```\n{fast_code}\n```"
        parts.append(part.strip())

        # Additional info (Analysis results) if requested
        if retrieve_additional_info and distill_data:
            analysis_key = str(original_idx + 1)
            text = distill_data[analysis_key]['think_tail']
            parts.append(text.strip())

                
    return '\n\n'.join(parts)
    


def generate_basic_retrieval_prompt(
    query_code: str,
    store,  # instance of DiskBackedVectorStore
    embedder,  # instance of EmbeddingGenerator
    fewshot_k: int = 3,
    enable_modes: List[EmbeddingMode] = ['full', 'think_tail', 'bullet'],
    code_pair: dict = None
) -> str:
    """
    Generate prompt for optimization using retrieved bullet/code examples.

    Args:
        query_code (str): The code to be optimized
        store (DiskBackedVectorStore): Retrieved vector store
        embedder (EmbeddingGenerator): Model to embed the query
        fewshot_k (int): Number of examples to retrieve (default: 3)
        enable_modes (List[EmbeddingMode]): List of modes to use or None
        code_pair (dict): 

    Returns:
        str: Formatted prompt (ready to fill in {retrieved_optimizations})
    """

    # retrieved = store.search(
    retrieved = store.search_parallel(
        query=query_code,
        embedder=embedder,
        mode_filter=enable_modes,
        retreived_k=fewshot_k,
        n_workers=4
    )

    parts = []
    for idx, r in enumerate(retrieved):
        slow_code, fast_code = get_code_pair(r, code_pair)
        part = f"\n\n### Original Example Code{idx+1}:\n```\n{slow_code}\n```\n### Optimized Example Code{idx+1}:\n```\n{fast_code}\n```"
        parts.append(part.strip())

    return '\n\n'.join(parts)


def generate_LLM_prompt(
    query_code: str,
    store,  # instance of DiskBackedVectorStore
    embedder,  # instance of EmbeddingGenerator
    fewshot_k: int = 3,
    enable_modes: List[EmbeddingMode] = ['full', 'think_tail', 'bullet'],
    code_pair: dict = None
) -> str:
    """
    Generate prompt for optimization using retrieved bullet/code examples.

    Args:
        query_code (str): The code to be optimized
        store (DiskBackedVectorStore): Retrieved vector store
        embedder (EmbeddingGenerator): Model to embed the query
        fewshot_k (int): Number of examples to retrieve (default: 3)
        enable_modes (List[EmbeddingMode]): List of modes to use or None
        code_pair (dict): 

    Returns:
        str: Formatted prompt (ready to fill in {retrieved_optimizations})
    """

    

    parts = []
    for idx, r in enumerate(retrieved):
        slow_code, fast_code = get_code_pair(r, code_pair)
        part = f"\n\n### Original Example Code{idx+1}:\n```\n{slow_code}\n```\n### Optimized Example Code{idx+1}:\n```\n{fast_code}\n```"
        parts.append(part.strip())
        
        text = r['text']
        # if the text is a list, process it
        if isinstance(text, list):
            text = ' '.join(text)
        part = text
        parts.append(part.strip())

    return '\n\n'.join(parts)


# Example usage
if __name__ == '__main__':


    store = DiskBackedVectorStore('./BRIDGE_data/rag_store/distilled_deepseek', model_name='Qodo/Qodo-Embed-1-1.5B')
    embedder = EmbeddingProcessor(model_name='Qodo/Qodo-Embed-1-1.5B')

    code_pair = load_code_pair('./BRIDGE_data/HQ_data.jsonl')

    example_code = """
    int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
    }
    """

    # fewshot_text = generate_LLM_prompt(
    #     query_code=example_code,
    #     store=store,
    #     embedder=embedder,
    #     fewshot_k=2,
    #     enable_modes=['full', 'think_tail', 'bullet'],
    #     code_pair=None
    # )

    fewshot_text = generate_basic_retrieval_prompt(
        query_code=example_code,
        store=store,
        embedder=embedder,
        fewshot_k=2,
        enable_modes=['full', 'think_tail', 'bullet'],
        code_pair=code_pair
    )

    print("--- Retrieved Optimization Examples ---")
    print(fewshot_text)