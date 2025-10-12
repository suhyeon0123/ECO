import sys
import time
import random
import json
import os
from datetime import datetime
from ollama import Client
import logging
import argparse
from transformers import AutoTokenizer

# import the modules
sys.path.append('.')
from inference_module.utils import get_prompt_template
from detection_module_rule_based.prompt_utils import generate_rule_prompt
from detection_module_LLM_based.prompt import generate_LLM_prompt, generate_basic_retrieval_prompt, generate_retrieval_prompt, generate_random_retrieval_prompt, load_code_pair, load_distilled_data
from detection_module_LLM_based.vector_store import DiskBackedVectorStore
from detection_module_LLM_based.embedding_processor import EmbeddingProcessor

# list of supported prompt strategies
PROMPT_STRATEGIES = [
    "base",
    "rules",
    "CoT",
    "ICL",
    "retrieve_basic",
    "retrieve_LLM_codesim",
    "retrieve_LLM_NLsim",
    "hybrid",
    "hybrid_after_rules",
    "retrieve_random_strategy"
]

RAG_STORE_PATH_CODE      = "./BRIDGE_data/rag_store/hq_snippet"
RAG_STORE_PATH_STRATEGE  = "./BRIDGE_data/rag_store/distilled_deepseek"
EMBEDDER_MODEL_NAME = "Qodo/Qodo-Embed-1-1.5B"
TRAIN_DATA_PATH = './BRIDGE_data/HQ_data.jsonl'


# logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# declare the global variable for the tokenizer
_tokenizer = None

def get_data(data_path):
    with open(data_path, 'r') as file:
        data = [json.loads(line) for line in file]
    return data



def call_LLM(client, model, prompt, temperature=0, system_prompt=None):
    
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': prompt})

    response = client.chat(
        model=model,
        messages=messages,
        options = {
            "temperature": temperature,
            "num_ctx": 8192  # set the context length to 4096
        }
    )
    return response

def setup_retrieval_resources(prompt_strategy):
    """function to setup the resources needed for the retrieval-based prompt"""
    if prompt_strategy == 'retrieve_basic' or prompt_strategy == 'retrieve_LLM_codesim' or prompt_strategy == 'retrieve_random_strategy':
        store = DiskBackedVectorStore(RAG_STORE_PATH_CODE, model_name=EMBEDDER_MODEL_NAME)
        embedder = EmbeddingProcessor(model_name=EMBEDDER_MODEL_NAME)
        code_pair = load_code_pair(TRAIN_DATA_PATH)
        distilled_data = load_distilled_data(RAG_STORE_PATH_STRATEGE)
        logger.info(f"Rag storage: {RAG_STORE_PATH_CODE}, {EMBEDDER_MODEL_NAME}")
        logger.info(f"Embedder model: {EMBEDDER_MODEL_NAME}")
    elif prompt_strategy == 'retrieve_LLM_NLsim' or prompt_strategy == 'hybrid' or prompt_strategy == 'hybrid_after_rules':
        store = DiskBackedVectorStore(RAG_STORE_PATH_STRATEGE, model_name=EMBEDDER_MODEL_NAME)
        embedder = EmbeddingProcessor(model_name=EMBEDDER_MODEL_NAME)
        code_pair = load_code_pair(TRAIN_DATA_PATH)
        distilled_data = load_distilled_data(RAG_STORE_PATH_STRATEGE)
        logger.info(f"Rag storage: {RAG_STORE_PATH_STRATEGE}, {EMBEDDER_MODEL_NAME}")
        logger.info(f"Embedder model: {EMBEDDER_MODEL_NAME}")
    elif prompt_strategy == 'ICL':
        store = None
        embedder = None
        code_pair = load_code_pair(TRAIN_DATA_PATH)
        logger.info(f"Code pair length: {len(code_pair)}")
        distilled_data = None
    else:
        return None, None, None, None
    
    
    
    return store, embedder, code_pair, distilled_data

def count_tokens(text, model_name):
    """function to count the number of tokens in the text"""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
    return len(_tokenizer.encode(text))


def trim_retrieved_examples(retrieved_examples, max_tokens, template, args, model_name):
    """function to trim the retrieved examples to the maximum number of tokens"""
    global _tokenizer
    
    # calculate the number of tokens in the base prompt excluding the retrieved_examples
    temp_args = args.copy()
    temp_args['retrieved_code_examples'] = ""
    base_prompt = template['prompt'].format(**temp_args)
    base_tokens = count_tokens(base_prompt, model_name)
    
    # the maximum number of tokens available for retrieved_examples
    available_tokens = max_tokens - base_tokens - 3  # reserve 3 tokens for "..."
    
    if available_tokens <= 0:
        return ""
    
    # tokenize the retrieved_examples
    tokens = _tokenizer.encode(retrieved_examples)
    
    if len(tokens) <= available_tokens:
        return retrieved_examples
    
    # trim the retrieved_examples to the maximum number of tokens
    trimmed_text = _tokenizer.decode(tokens[:available_tokens])
    
    final_tokens = count_tokens(trimmed_text + "...", model_name)
    logger.info(f"Trimmed retrieved examples tokens: {final_tokens}")
    logger.info(f"Tokens removed: {len(tokens) - final_tokens}")
    
    return trimmed_text + "..."

def adjust_args_for_max_tokens(args, template, model_name, MAX_TOKENS=4096):
    """function to adjust the arguments for the maximum number of tokens"""
    
    # only process if retrieved_code_examples is in the arguments
    if 'retrieved_code_examples' in args:
        # use the existing trim_retrieved_examples logic
        args['retrieved_code_examples'] = trim_retrieved_examples(
            args['retrieved_code_examples'],
            MAX_TOKENS,
            template,
            args,
            model_name
        )
    return args

def generate_prompt(item, prompt_strategy, sampling='greedy', sample_count=1, store=None, embedder=None, code_pair=None, distilled_data=None, client=None, temperature=None, model_name=None):
    """function to generate the prompt based on the prompt strategy
    
    Args:
        item: the source code item
        prompt_strategy: the prompt strategy
        sampling: the sampling method ('greedy' or 'k_sample')
        sample_count: the number of samples to generate in the k_sample mode
        store: the vector store object
        embedder: the embedding processor object
        code_pair: the code pair data
        distilled_data: the code analysis data
    Returns:
        prompts_list: the list of prompts [(prompt, prompt_after_immediate_response), ...]
    """
    code_id = item['src_id']
    src_code = item['src_code']
    prompts_list = []


    categories = ['recursive', 'bit_manipulation', 'vector', 'non_hash', 'IO_library', 'pow_library', 'literal_math', 'loop_invariant_math', 'expensive_std_in_loop', 'string_concat_in_loop']
    
    # non-retrieval-based strategies always generate only one prompt
    if prompt_strategy in ['base', 'rules', 'CoT']:
        if prompt_strategy == 'base':
            args = {'src_code': src_code}
            template = get_prompt_template(prompt_strategy)
            args = adjust_args_for_max_tokens(args, template, model_name)
            
        elif prompt_strategy == 'rules':
            detect_prompts = generate_rule_prompt(code_id=code_id, categories=categories)
            logger.info(f"detect_prompts: {detect_prompts}")
            args = {'src_code': src_code, 'detect_prompts': detect_prompts}
            template = get_prompt_template('rules')
            args = adjust_args_for_max_tokens(args, template, model_name)
        
        elif prompt_strategy == 'CoT':
            args = {'src_code': src_code}
            template = get_prompt_template(prompt_strategy)
            args = adjust_args_for_max_tokens(args, template, model_name)
        
        
        prompt = template['prompt'].format(**args)
        # non-retrieval-based strategies copy the element to prompt_list sample_count times
        for _ in range(sample_count):
            system_prompt = template['system_prompt'] if 'system_prompt' in template else None
            prompts_list.append({'prompt': prompt, 'system_prompt': system_prompt})
    
    elif prompt_strategy == 'ICL':
        fewshot_k = 2

        for _ in range(sample_count):

            selected_code_pairs = random.sample(code_pair, fewshot_k)

            retrieved_code_examples = ""
            for idx, pair in enumerate(selected_code_pairs):
                slow_code = pair[0]  # the original slow code
                fast_code = pair[1]  # the optimized fast code
                part = f"\n\n### Original Example Code{idx+1}:\n```\n{slow_code}\n```\n### Optimized Example Code{idx+1}:\n```\n{fast_code}\n```"
                retrieved_code_examples += part
            
            args = {'src_code': src_code, 'retrieved_code_examples': retrieved_code_examples}
            template = get_prompt_template(prompt_strategy)
            args = adjust_args_for_max_tokens(args, template, model_name)
            prompt = template['prompt'].format(**args)

            system_prompt = template['system_prompt'] if 'system_prompt' in template else None
            prompts_list.append({'prompt': prompt, 'system_prompt': system_prompt})

        
        
        

    # retrieval-based strategies can generate various prompts based on the sampling method
    elif prompt_strategy in ['retrieve_basic', 'retrieve_LLM_codesim', 'retrieve_LLM_NLsim', 'retrieve_random_strategy']:
        # set the diversity parameter (higher diversity for k_sample)
        # diversity_factor = 0.7 if sampling == 'k_sample' else 0.0
        
        for _ in range(sample_count):
            start_time = time.time()
            
            if prompt_strategy == 'retrieve_basic':
                retrieved_code_examples = generate_retrieval_prompt(
                    query=src_code,
                    query_type='code',
                    store=store,
                    embedder=embedder,
                    fewshot_k=2,
                    enable_modes=['full'],
                    code_pair=code_pair,
                    distill_data=None,
                    retrieve_additional_info=False,
                    given_code_analysis=None
                    # diversity_factor=diversity_factor  # add the diversity parameter
                )
            elif prompt_strategy == 'retrieve_LLM_codesim':
                retrieved_code_examples = generate_retrieval_prompt(
                    query=src_code,
                    query_type='code',
                    store=store,
                    embedder=embedder,
                    fewshot_k=2,
                    enable_modes=['full'],  ## query가 src_code 이므로 full mode로 설정
                    code_pair=code_pair,
                    distill_data=distilled_data,
                    retrieve_additional_info=True,
                    given_code_analysis=None
                    # diversity_factor=diversity_factor  # add the diversity parameter
                )

            elif prompt_strategy == 'retrieve_LLM_NLsim':
                
                with open('detection_module_LLM_based/get_runtime_bottleneck.txt', 'r') as file:
                    initial_prompt = file.read()
                given_code_analysis = call_LLM(client, model_name, prompt=src_code, system_prompt=initial_prompt, temperature=temperature).message.content

                retrieved_code_examples = generate_retrieval_prompt(
                    query=src_code,
                    query_type='NL',
                    store=store,
                    embedder=embedder,
                    fewshot_k=2,
                    enable_modes=['think_tail'],
                    code_pair=code_pair,
                    distill_data=distilled_data,
                    retrieve_additional_info=True,
                    given_code_analysis=given_code_analysis
                    # diversity_factor=diversity_factor  # add the diversity parameter
                )
            elif prompt_strategy == 'retrieve_random_strategy':
                retrieved_code_examples = generate_random_retrieval_prompt(
                    fewshot_k=2,
                    code_pair=code_pair,
                    distill_data=distilled_data,
                    retrieve_additional_info=True,
                )
                
            elapsed_time = time.time() - start_time
            logger.info(f"code example search time: {elapsed_time:.2f}s")
            
            args = {'src_code': src_code, 'retrieved_code_examples': retrieved_code_examples}
            template = get_prompt_template('retrieve')
            args = adjust_args_for_max_tokens(args, template, model_name)
            prompt = template['prompt'].format(**args)
            system_prompt = template['system_prompt'] if 'system_prompt' in template else None
            prompts_list.append({'prompt': prompt, 'system_prompt': system_prompt})
            
            # # use different seeds for diversity (only for k_sample)
            # if sampling == 'k_sample':
            #     # increase diversity by searching different examples in the next iteration
            #     diversity_factor = min(diversity_factor + 0.1, 0.9)
    
    elif prompt_strategy == 'hybrid':

        # which is same as rules prompt
        detect_prompts = generate_rule_prompt(code_id=code_id, categories=categories)
        logger.info(f"detect_prompts: {detect_prompts}")
        args = {'src_code': src_code, 'detect_prompts': detect_prompts}

        # which is same as LLM_NLsim prompt
        for _ in range(sample_count):
            start_time = time.time()

            with open('detection_module_LLM_based/get_runtime_bottleneck.txt', 'r') as file:
                initial_prompt = file.read()
            
            given_code_analysis = call_LLM(client, model_name, prompt=src_code, system_prompt=initial_prompt, temperature=temperature).message.content
            retrieved_code_examples = generate_retrieval_prompt(
                query=src_code,  # use given_code_analysis instead of src_code
                query_type='NL',
                store=store,
                embedder=embedder,
                fewshot_k=2,
                enable_modes=['think_tail'],
                code_pair=code_pair,
                distill_data=distilled_data,
                retrieve_additional_info=True,
                given_code_analysis=given_code_analysis
                # diversity_factor=diversity_factor  # add the diversity parameter
            )
            elapsed_time = time.time() - start_time
            logger.info(f"code example search time: {elapsed_time:.2f}s")
            args['retrieved_code_examples'] = retrieved_code_examples

            # Hybrid prompt
            template = get_prompt_template('hybrid')
            args = adjust_args_for_max_tokens(args, template, model_name)
            prompt = template['prompt'].format(**args)
            system_prompt = template['system_prompt'] if 'system_prompt' in template else None

            prompts_list.append({'prompt': prompt, 'system_prompt': system_prompt})

    elif prompt_strategy == 'hybrid_after_rules':
        generated_answers = item['generated_answers']
        original_src_code = item['src_code'] 
        
        for generated_answer in generated_answers:
        
            with open('detection_module_LLM_based/get_runtime_bottleneck.txt', 'r') as file:
                initial_prompt = file.read()
            given_code_analysis = call_LLM(client, model_name, prompt=generated_answer, system_prompt=initial_prompt, temperature=temperature).message.content

            retrieved_code_examples = generate_retrieval_prompt(
                query=src_code, ## It will replaced by given_code_analsyis
                query_type='NL',
                store=store,
                embedder=embedder,
                fewshot_k=2,
                enable_modes=['think_tail'],
                code_pair=code_pair,
                distill_data=distilled_data,
                retrieve_additional_info=True,
                given_code_analysis=given_code_analysis
                # diversity_factor=diversity_factor  # add the diversity parameter
            )

            args = {
                'src_code': original_src_code,  # the original src code
                'rules_optimization': generated_answer,  # the rules optimization result
                'retrieved_code_examples': retrieved_code_examples
            }
            template = get_prompt_template('hybrid_after_rules')  # use the dedicated template
            args = adjust_args_for_max_tokens(args, template, model_name)
            prompt = template['prompt'].format(**args)
            system_prompt = template['system_prompt'] if 'system_prompt' in template else None
            prompts_list.append({'prompt': prompt, 'system_prompt': system_prompt})
            
    return prompts_list


def process_item(client, item, args, output_dir, retrieval_resources):
    """function to process each data item"""
    code_id = item['src_id']
    
    
    # create the output file path (different based on the sampling method)
    output_file = os.path.join(output_dir, f"{code_id}.jsonl")
    
    # check if the file already exists
    if os.path.exists(output_file):
        logger.info(f"File {output_file} already exists. Skipping.")
        return

    # generate the prompt
    prompts_list = generate_prompt(
        item, args.prompt_strategy, args.sampling, args.sample_count, *retrieval_resources, client=client, temperature=args.temperature, model_name=args.model_name
    )
    

    all_results = []  # the list to save all the results

    for sample_idx, dics in enumerate(prompts_list):
        prompt = dics['prompt']
        system_prompt = dics['system_prompt']

        # call the LLM
        start_time = time.time()
        response = call_LLM(client, args.model_name, prompt, args.temperature, system_prompt)
        elapsed_time = time.time() - start_time
        
        # print the result
        logger.info(f"time for sample {sample_idx+1}: {elapsed_time:.2f}s")
        
        # save the result
        result = {
            "prompt": prompt,
            "response": response.message.content,
            "elapsed_time": elapsed_time,
            "model": args.model_name,
            "sample_id": sample_idx + 1,
            "input_length": len(prompt),
        }
        all_results.append(result)

    # save all the results to a JSONL file
    with open(output_file, "w", encoding="utf-8") as f:
        for result in all_results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    logger.info(f"File {output_file} created")

def create_output_directory(args):
    """Output directory creation function"""
    model_name = args.model_name.replace(":", "_")
    test_name = args.test_data_path.split("/")[-1].replace("_test.jsonl", "")
    # folder_name = f"{args.prompt_strategy}/{model_name}_{args.sampling}"
    folder_name = f"{test_name}/{args.prompt_strategy}/{model_name}_{args.sampling}"
    output_dir = f"results/inference_results/{folder_name}"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Output directory created: {output_dir}")
    
    return output_dir


def main():
    
    parser = argparse.ArgumentParser(description='LLM inference for code optimization')
    parser.add_argument('--model_name', type=str, help='model name (e.g. qwen2.5-coder:7b)')
    parser.add_argument('--test_data_path', type=str, help='input data file path (e.g. BRIDGE_data/PIE_test.jsonl)')
    parser.add_argument('--prompt_strategy', type=str, choices=PROMPT_STRATEGIES, 
                        help='prompt strategy (base, rules, CoT, CoT_rules, retrieve_basic, retrieve_LLM_codesim, retrieve_LLM_NLsim)')
    parser.add_argument('--sampling', type=str, choices=['greedy', 'k_sample'], 
                        help='sampling method (greedy or k_sample)')
    parser.add_argument('--sample_num', type=int, default=10, help='number of samples to generate')
    parser.add_argument('--port', type=str, help='Ollama server port')
    parser.add_argument('--start_half', action='store_true', help='start index')
    parser.add_argument('--start_idx', type=int, help='start index')

    
    args = parser.parse_args()
    
    
    # if the sampling method is not k_sample, set the sample_count to 1
    if args.sampling == 'k_sample':
        args.sample_count = args.sample_num

    if args.sampling == 'greedy':
        args.temperature = 0.0
    elif args.sampling == 'k_sample':
        args.temperature = 0.7
    
    # log the input parameters
    logger.info(f"model_name: {args.model_name}")
    logger.info(f"test_data_path: {args.test_data_path}")
    logger.info(f"prompt_strategy: {args.prompt_strategy}")
    logger.info(f"sampling: {args.sampling}")
    logger.info(f"sample_count: {args.sample_count}")
    logger.info(f"temperature: {args.temperature}")
    logger.info(f"port: {args.port}")
    
    
    # create the output directory
    output_dir = create_output_directory(args)
    
    # Ollama client initialization
    client = Client(host=f'http://localhost:{args.port}')
    
    # set the resources for the retrieval-based prompt
    store, embedder, code_pair, distilled_data = setup_retrieval_resources(args.prompt_strategy)
    retrieval_resources = store, embedder, code_pair, distilled_data
    
    # load the data
    data = get_data(args.test_data_path)
    
    # process each item
    for idx, item in enumerate(data):
        if args.start_idx and idx < args.start_idx:
            continue

        if args.start_half and idx < len(data) / 2:
            continue

        logger.info(f"processing item {idx+1}/{len(data)}...")
        try:
            process_item(client, item, args, output_dir, retrieval_resources)
        except Exception as e:
            logger.error(f"error occurred while processing item {idx+1}: {e}")
            continue

if __name__ == "__main__":
    main()






    
    
    
