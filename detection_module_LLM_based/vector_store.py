"""
Disk-backed vector store that stores:
- metadata in JSON
- embeddings in .npz

Supports: insert from response, query by similarity, and persistent reload.
"""
import os
import json
import numpy as np
import glob
import concurrent.futures
from typing import List, Dict, Literal, Optional
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.append('.')
from detection_module_LLM_based.embedding_processor import EmbeddingProcessor, EmbeddingMode




class DiskBackedVectorStore:
    def __init__(self, storage_path: str, model_name: str):
        os.makedirs(storage_path, exist_ok=True)
        self.meta_path = os.path.join(storage_path, 'metadata.json')
        self.vec_path = os.path.join(storage_path, 'vectors.npz')
        self.model_name = model_name

        self.metadata: List[Dict] = []
        self.vectors: Dict[str, np.ndarray] = {}
        self.next_id = 0

        self._load()

    def _load(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            self.next_id = max([m['entry_id'] for m in self.metadata], default=-1) + 1
        if os.path.exists(self.vec_path):
            self.vectors = dict(np.load(self.vec_path, allow_pickle=False))
            
            

    def _save(self):
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        np.savez_compressed(self.vec_path, **self.vectors)

    def add_encoded_segments(self, segments: List[Dict], analysis_id: str):
        """add encoded segments to the store"""
        for s in segments:
            entry_id = self.next_id
            self.next_id += 1

            self.metadata.append({
                'entry_id': entry_id,
                'response_id': s.get('response_id', -1),
                'analysis_id': analysis_id,
                'mode': s['mode'],
                'index': s['index'],
                'text': s['text']
            })
            self.vectors[str(entry_id)] = s['vector']

        self._save()

    def add_response(self, response: str, embedder: EmbeddingProcessor, analysis_id: str, modes: List[EmbeddingMode] = ['full']):
        """
        this method is kept for backward compatibility,
        but it is better to use encode_response_segments and add_encoded_segments instead.
        """
        segments = embedder.encode_segments(response, modes[0], analysis_id)
        self.add_encoded_segments(segments, analysis_id)

    def _process_chunk(self, chunk, mode_filter):
        """process the metadata chunk and return the filtered metadata and vectors"""
        local_metas, local_vecs = [], []
        for meta in chunk:
            if mode_filter is None or meta['mode'] in mode_filter:
                eid = str(meta['entry_id'])
                if eid in self.vectors:
                    local_metas.append(meta)
                    local_vecs.append(self.vectors[eid])
        return local_metas, local_vecs

    def search_parallel(self, query: str, embedder: EmbeddingProcessor, mode_filter: List[EmbeddingMode] = None, retreived_k: int = 3, n_workers: int = None) -> List[Dict]:
        query_vec = embedder.model.encode([query])[0]
        
        # define the number of workers and the chunk size
        n_workers = n_workers or (os.cpu_count() or 4)
        chunk_size = max(100, len(self.metadata) // n_workers)
        chunks = [self.metadata[i:i+chunk_size] for i in range(0, len(self.metadata), chunk_size)]
        
        # directly process (instead of multiprocessing)
        metas, vecs = [], []
        for chunk in chunks:
            local_metas, local_vecs = self._process_chunk(chunk, mode_filter)
            metas.extend(local_metas)
            vecs.extend(local_vecs)
        
        # the rest of the logic is the same
        if not vecs:
            return []
        
        vec_matrix = np.stack(vecs)
        sims = cosine_similarity([query_vec], vec_matrix)[0]
        
        ranked = sorted(zip(metas, sims), key=lambda x: x[1], reverse=True)[:retreived_k]
        return [
            {
                'text': m['text'],
                'similarity': score,
                'entry_id': m['entry_id'],
                'mode': m['mode'],
                'analysis_id': m['analysis_id'],
                'index': m['index']
            }
            for m, score in ranked
        ]

    def search(self, query: str, embedder: EmbeddingProcessor, mode_filter: List[EmbeddingMode] = None, retreived_k: int = 3) -> List[Dict]:
        query_vec = embedder.model.encode([query])[0]

        metas, vecs = [], []
        for meta in self.metadata:
            if mode_filter is None or meta['mode'] in mode_filter:
                eid = str(meta['entry_id'])
                if eid in self.vectors:
                    metas.append(meta)
                    vecs.append(self.vectors[eid])

        if not vecs:
            return []

        vec_matrix = np.stack(vecs)
        sims = cosine_similarity([query_vec], vec_matrix)[0]

        ranked = sorted(zip(metas, sims), key=lambda x: x[1], reverse=True)[:retreived_k]
        return [
            {
                'text': m['text'],
                'similarity': score,
                'entry_id': m['entry_id'],
                'mode': m['mode'],
                'analysis_id': m['analysis_id'],
                'index': m['index']
            }
            for m, score in ranked
        ]

    def has_analysis_id(self, analysis_id: str) -> bool:
        """check if the specified analysis_id is already in the store"""
        return any(meta['analysis_id'] == analysis_id for meta in self.metadata)


def load_analysis_data(analysis_data_path: str) -> List[tuple]:
    """
    read the analysis result files and return the list of response and analysis_id pairs.
    
    Args:
        analysis_data_path: the path to the analysis result JSON files
        the analysis result files should be saved in the format of 'analysis_1.json', 'analysis_2.json', etc.
        each JSON file should be in the following format:
        {
            "prompt": "Identify optimization points in this slow code...",
            "response": "<think>\nOkay, I need to figure out the optimization points...",
            "elapsed_time": 32.5,
            "model": "deepseek-r1:32b"
        }
            
    Returns:
        List[tuple]: (response, analysis_id, file_path) tuple list
    """
    analysis_files = glob.glob(os.path.join(analysis_data_path, '*.json'))
    result_data = []
    
    for idx, analysis_file in enumerate(analysis_files):
        analysis_id = os.path.basename(analysis_file).split('_')[1]
        
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            result_data.append((analysis_data['response'], analysis_id, analysis_file))
        except Exception as e:
            print(f"error: {e} - file: {analysis_file}")
            continue
            
    return result_data

def load_snippet_data(snippet_data_path: str) -> List[tuple]:
    """
    read the code snippet data and return the list of response and analysis_
    """
    assert snippet_data_path.endswith('.jsonl'), "the code snippet data should be a JSONL file."

    result_data = []
    with open(snippet_data_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            result_data.append((data['src_code'], idx, None))
    return result_data
    

def populate_vector_store(analysis_data_path: str, store_dir: str, model_name: str, data_type: Literal['analysis', 'snippet']) -> DiskBackedVectorStore:
    """
    read the analysis result files and add them to the vector store.
    
    Args:
        analysis_data_path: the path to the analysis result JSON files
        store_dir: the path to the vector store data
        model_name: the name of the embedding model to use
    
    Returns:
        DiskBackedVectorStore: the populated vector store instance
    """
    if not os.path.exists(store_dir):
        os.makedirs(store_dir)

    embedder = EmbeddingProcessor(model_name=model_name)
    storage = DiskBackedVectorStore(storage_path=store_dir, model_name=model_name)
    
    if data_type == 'analysis': 
        data_list = load_analysis_data(analysis_data_path)
    elif data_type == 'snippet':
        data_list = load_snippet_data(snippet_data_path)
    
    for idx, (response, analysis_id, file_path) in enumerate(data_list):
        # if the analysis_id is already processed, skip
        if storage.has_analysis_id(analysis_id):
            print(f"skip {idx+1}/{len(data_list)}: {file_path} (already processed)")
            continue
            
        print(f"processing {idx+1}/{len(data_list)}: {file_path}")
        if data_type == 'analysis':
            modes = ['full', 'think_tail', 'bullet']
        elif data_type == 'snippet':
            modes = ['full']

        segments = []
        for mode in modes:
            segments.extend(embedder.encode_segments(response, mode, analysis_id=analysis_id))
            

        storage.add_encoded_segments(segments, analysis_id)
    
    return storage


# Example usage
if __name__ == '__main__':     
    # sample_response = """
    # <think>
    # This is reasoning text...
    # </think>

    # 1. **Memoization**: Avoid redundant recursion.
    # 2. **Loop Unrolling**: Reduce iteration overhead.
    # """
    # store.add_response(sample_response, embedder, analysis_id='abc123', modes=['full', 'think_tail', 'bullet'])

    # Example 1: Populate vector store from analysis data
    analysis_data_path = './BRIDGE_data/distilled_rationales'  
    store_dir = './BRIDGE_data/rag_store/distilled_deepseek'
    model_name = 'Qodo/Qodo-Embed-1-1.5B'
    storage = populate_vector_store(analysis_data_path, store_dir, model_name, data_type='analysis')


    # # Example 2: Populate vector store from snippet data
    # snippet_data_path = './BRIDGE_data/HQ_data.jsonl'
    # store_dir = './BRIDGE_data/rag_store/hq_snippet'
    # model_name = 'Qodo/Qodo-Embed-1-1.5B'
    # storage = populate_vector_store(snippet_data_path, store_dir, model_name, data_type='snippet')

    embedder = EmbeddingProcessor(model_name='Qodo/Qodo-Embed-1-1.5B')
    
    example_code = """#include <iostream>
    using namespace std;

    int main() {
        int n; cin >> n;
        int sum = 0;
        for (int i = 1; i <= n; ++i)
            sum += i;
        cout << sum << endl;
        return 0;
    }
    """

    results = storage.search(example_code, embedder, mode_filter='bullet')
    for r in results:
        print(f"[{r['similarity']:.3f}] #{r['entry_id']} ({r['mode']}): {r['text'][:60]}...")
