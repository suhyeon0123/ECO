from datasets import load_dataset
import pdb
from tqdm import tqdm
import random 
import json
import os



# Calculate statistics for each key
from collections import Counter

def print_statistics():
    # Source distribution
    source_dist = Counter(problem['source'] for problem in filtered_test)
    print("\nSource Distribution:")
    for source, count in sorted(source_dist.items()):
        print(f"Source {source}: {count} problems ({count/len(filtered_test)*100:.2f}%)")

    # Difficulty distribution
    diff_dist = Counter(problem['difficulty'] for problem in filtered_test)
    print("\nDifficulty Distribution:")
    for diff, count in sorted(diff_dist.items()):
        print(f"Difficulty {diff}: {count} problems ({count/len(filtered_test)*100:.2f}%)")

    # CF Contest ID distribution
    contest_dist = Counter(problem['cf_contest_id'] for problem in filtered_test)
    print("\nContest ID Distribution:")
    print(f"Number of unique contests: {len(contest_dist)}")
    
    # CF Rating distribution
    rating_dist = Counter(problem['cf_rating'] for problem in filtered_test)
    print("\nCF Rating Distribution:")
    for rating, count in sorted(rating_dist.items()):
        print(f"Rating {rating}: {count} problems ({count/len(filtered_test)*100:.2f}%)")

    # CF Tags distribution
    all_tags = []
    for problem in filtered_test:
        all_tags.extend(problem['cf_tags'])
    tags_dist = Counter(all_tags)
    print("\nCF Tags Distribution:")
    for tag, count in sorted(tags_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"Tag '{tag}': {count} occurrences")

    # Time limit distribution
    time_dist = Counter(problem['time_limit']['seconds'] for problem in filtered_test)
    print("\nTime Limit Distribution (seconds):")
    for time, count in sorted(time_dist.items()):
        print(f"{time} seconds: {count} problems ({count/len(filtered_test)*100:.2f}%)")

def filter_n_tc(problem, n_tc=10):
    public_tests = problem.get('public_tests', {'input': [], 'output': []})
    private_tests = problem.get('private_tests', {'input': [], 'output': []})

    public_tests_n = len(public_tests['input'])
    private_tests_n = len(private_tests['input'])

    if public_tests_n + private_tests_n < n_tc:
        return False

    return True


def filter_time_limit(problem, max_time_limit=2):
    time_limit = problem.get('time_limit', {'seconds': 0})
    if time_limit['seconds'] > max_time_limit:
        return False
    return True

def filter_solutions_types(problem, language=2):
    solutions_dict = problem.get('solutions', {})
    
    # if the solution information is not available, return the problem as is
    if not solutions_dict or 'solution' not in solutions_dict:
        return problem

    # create a new list to store only C++ solutions
    cpp_solutions = []
    cpp_languages = []

    # zip to iterate over solution codes and language codes together
    for code, lang in zip(solutions_dict['solution'], solutions_dict['language']):
        if int(lang) == language:  # if the language code is 2 (C++)
            cpp_solutions.append(code)
            cpp_languages.append(lang)
            
    # replace the list in the 'solutions' dictionary with the filtered list
    problem['solutions']['solution'] = cpp_solutions
    problem['solutions']['language'] = cpp_languages
    
    return problem

def select_test_cases(problem, n_tc=10, seed=42):
    """Select 10 test cases from public and private tests using random seed"""
    random.seed(seed)
    
    public_tests = problem.get('public_tests', {'input': [], 'output': []})
    private_tests = problem.get('private_tests', {'input': [], 'output': []})
    
    public_inputs = public_tests['input']
    public_outputs = public_tests['output']
    private_inputs = private_tests['input']
    private_outputs = private_tests['output']
    
    selected_inputs = []
    selected_outputs = []
    
    # First, select from public tests (up to n_tc)
    if len(public_inputs) >= n_tc:
        # Randomly select 10 from public tests
        indices = random.sample(range(len(public_inputs)), n_tc)
        selected_inputs = [public_inputs[i] for i in indices]
        selected_outputs = [public_outputs[i] for i in indices]
    else:
        # Take all public tests and fill remaining from private tests
        selected_inputs = public_inputs.copy()
        selected_outputs = public_outputs.copy()
        
        remaining = n_tc - len(public_inputs)
        if len(private_inputs) >= remaining:
            indices = random.sample(range(len(private_inputs)), remaining)
            selected_inputs.extend([private_inputs[i] for i in indices])
            selected_outputs.extend([private_outputs[i] for i in indices])
        else:
            # If not enough private tests, take all available
            selected_inputs.extend(private_inputs)
            selected_outputs.extend(private_outputs)
    
    return selected_inputs[:n_tc], selected_outputs[:n_tc]

def create_test_case_files(problem_id, inputs, outputs, base_dir="codeforce_test_cases"):
    """Create test case files for a problem"""
    problem_dir = os.path.join(base_dir, f"p{problem_id:05d}")
    os.makedirs(problem_dir, exist_ok=True)
    
    for i, (inp, out) in enumerate(zip(inputs, outputs)):
        # Write input file
        input_file = os.path.join(problem_dir, f"input.{i}.txt")
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(inp.strip() + '\n')
        
        # Write output file
        output_file = os.path.join(problem_dir, f"output.{i}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(out.strip() + '\n')

def generate_codeforce_dataset(filtered_problems, n_problems=30, n_solutions_per_problem=10, seed=42):
    """Generate codeforce_test.jsonl and test case files"""
    random.seed(seed)
    
    # Select 30 problems randomly
    selected_problems = random.sample(filtered_problems, min(n_problems, len(filtered_problems)))
    
    dataset_entries = []
    
    for prob_idx, problem in enumerate(tqdm(selected_problems, desc="Processing problems")):
        problem_id = prob_idx  # 0-based problem ID
        
        # Select test cases for this problem
        inputs, outputs = select_test_cases(problem, n_tc=10, seed=seed + prob_idx)
        
        # Create test case files
        create_test_case_files(problem_id, inputs, outputs)
        
        # Get solutions for this problem
        solutions = problem['solutions']['solution']
        
        # Select 10 solutions (or all if less than 10)
        n_solutions = min(n_solutions_per_problem, len(solutions))
        selected_solutions = random.sample(solutions, n_solutions) if len(solutions) >= n_solutions else solutions
        
        # Create dataset entries
        for sol_idx, solution in enumerate(selected_solutions):
            entry = {
                "src_id": f"cf_{problem_id:05d}_{sol_idx:02d}",
                "problem_id": f"p{problem_id:05d}",
                "src_code": solution,
                "difficulty": problem.get('difficulty', None),
                "cf_rating": problem.get('cf_rating', None),
                "time_limit": problem.get('time_limit', {}).get('seconds', None),
                "cf_tags": problem.get('cf_tags', [])
            }
            dataset_entries.append(entry)
    
    # Write dataset to jsonl file
    with open('codeforce_test.jsonl', 'w', encoding='utf-8') as f:
        for entry in dataset_entries:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Generated {len(dataset_entries)} entries in codeforce_test.jsonl")
    print(f"Created test cases for {len(selected_problems)} problems in codeforce_test_cases/")
    
    return dataset_entries



if __name__ == "__main__":
    # Set random seed for reproducibility
    SEED = 42
    random.seed(SEED)
    
    print("Loading CodeContests dataset...")
    dataset = load_dataset("deepmind/code_contests")
    test = dataset['test']

    solution_with_10_count = 0
    solution_count = 0

    print("Filtering problems...")
    filtered_test = []
    for problem in tqdm(test, desc="Filtering problems"):
        problem = filter_solutions_types(problem, language=2)   # extract only cpp solutions
        valid_n_tc = filter_n_tc(problem, n_tc=10)        # check if the problem has at least 10 test cases
        valid_time_limit = filter_time_limit(problem, max_time_limit=2) # check if the problem has a time limit of less than 2 seconds

        if valid_n_tc and valid_time_limit and len(problem['solutions']['solution']) > 0:
            solution_count += len(problem['solutions']['solution'])
            if len(problem['solutions']['solution']) >= 10:
                solution_with_10_count += 10
            else:
                solution_with_10_count += len(problem['solutions']['solution'])
            filtered_test.append(problem)

    print(f"Total filtered problems: {len(filtered_test)}")
    print(f"Total solutions: {solution_count}")
    print(f"Solutions with 10+ count: {solution_with_10_count}")

    print("\nSample problem keys:", list(filtered_test[0].keys()))
    
    # Print statistics
    print_statistics()
    
    # Generate codeforce dataset
    print(f"\nGenerating codeforce dataset with seed {SEED}...")
    dataset_entries = generate_codeforce_dataset(
        filtered_test, 
        n_problems=30, 
        n_solutions_per_problem=10, 
        seed=SEED
    )
    
    print(f"\nDataset generation completed!")
    print(f"Total entries: {len(dataset_entries)}")
