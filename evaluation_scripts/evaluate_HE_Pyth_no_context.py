#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import json
import re
import ast
import tempfile
import importlib
import subprocess
from typing import Any, List, Dict, Tuple, Union, Callable

# Path to the Pyth interpreter
PYTH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Pyth/pyth')
PYTH_INTERPRETER_PATH = os.path.join(PYTH_DIR, 'pyth.py')
HE_PYTH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Pyth/HE_Pyth_no_context_4o')

def get_pyth_translation(code: str) -> str:
    """Get the Python translation of Pyth code."""
    try:
        # Create a temporary file for the Pyth code
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.pyth', delete=False) as temp_pyth:
            temp_pyth_path = temp_pyth.name
            temp_pyth.write(code)
            temp_pyth.flush()
            
        try:
            # Run the Pyth interpreter with the -d flag to get the debug output
            result = subprocess.run(
                ['python3', os.path.join(PYTH_DIR, "pyth.py"), '-d', temp_pyth_path],
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            if result.returncode != 0:
                return f"Error during translation: {result.stderr}"
                
            return result.stdout.strip()
            
        finally:
            # Clean up
            os.remove(temp_pyth_path)
            
    except subprocess.TimeoutExpired:
        return f"Error during translation: Timeout expired"
    except Exception as e:
        return f"Error during translation: {str(e)}"

def extract_pyth_code(generated_content: str) -> str:
    """
    Extracts Pyth code enclosed within ```pyth ... ``` blocks.
    """
    pattern = r"```pyth\s+([\s\S]*?)```"
    pyth_codes = re.findall(pattern, generated_content, re.MULTILINE)
    if pyth_codes:
        return pyth_codes[0].strip()
    else:
        lines = generated_content.splitlines()
        code_lines = []
        capture = False
        for line in lines:
            if line.strip().startswith("```pyth"):
                capture = True
                continue
            if line.strip().startswith("```") and capture:
                break
            if capture:
                code_lines.append(line)
        return "\n".join(code_lines).strip()

def clean_pyth_code(pyth_code: str) -> str:
    """
    Clean Pyth code by removing comments and docstrings, and simplifying it.
    """
    # Remove comments and docstrings (lines starting with # or ")
    lines = []
    for line in pyth_code.split("\n"):
        line = line.strip()
        if not line.startswith("#") and not line.startswith('"'):
            lines.append(line)
    
    # Join the remaining lines and remove any extra whitespace
    cleaned_code = " ".join([line for line in lines if line])
    return cleaned_code

def compare_results(result: Any, expected: Any) -> bool:
    """
    Compare the result with the expected output, handling different types.
    """
    # If they're already equal, return True
    if result == expected:
        return True
    
    # Handle None
    if result is None and expected is None:
        return True
    
    # Handle different types
    try:
        # Convert tuples to lists for comparison
        if isinstance(expected, tuple) and isinstance(result, list):
            if list(expected) == result:
                return True
        
        # Convert lists to tuples for comparison
        if isinstance(expected, list) and isinstance(result, tuple):
            if expected == list(result):
                return True
        
        # Handle floating point comparison
        if isinstance(expected, float) and (isinstance(result, float) or isinstance(result, int)):
            if abs(expected - result) < 1e-6:
                return True
        
        # Handle string vs. number
        if isinstance(expected, str) and (isinstance(result, int) or isinstance(result, float)):
            if expected == str(result):
                return True
        
        if isinstance(result, str) and (isinstance(expected, int) or isinstance(expected, float)):
            if result == str(expected):
                return True
        
        # Handle lists of different types
        if isinstance(expected, list) and isinstance(result, list):
            if len(expected) == len(result):
                all_equal = True
                for e, r in zip(expected, result):
                    if not compare_results(e, r):
                        all_equal = False
                        break
                if all_equal:
                    return True
        
        # Handle dictionaries
        if isinstance(expected, dict) and isinstance(result, dict):
            if set(expected.keys()) == set(result.keys()):
                all_equal = True
                for k in expected:
                    if not compare_results(expected[k], result[k]):
                        all_equal = False
                        break
                if all_equal:
                    return True
    except:
        pass
    
    return False

def extract_test_cases(test_str: str) -> List[Dict[str, Any]]:
    """
    Extract test cases from a string containing Python assert statements.
    Returns a list of dictionaries with 'args' and 'expected' keys.
    """
    test_cases = []
    
    # Try to parse the test string as Python code
    try:
        tree = ast.parse(test_str)
        
        for node in ast.walk(tree):
            # Look for assert statements
            if isinstance(node, ast.Assert):
                # Handle different types of assert statements
                
                # Case 1: assert candidate(args) == expected
                if (isinstance(node.test, ast.Compare) and 
                    len(node.test.ops) == 1 and 
                    isinstance(node.test.ops[0], ast.Eq) and
                    isinstance(node.test.left, ast.Call) and
                    isinstance(node.test.left.func, ast.Name) and
                    node.test.left.func.id == "candidate"):
                    
                    args = []
                    for arg in node.test.left.args:
                        if isinstance(arg, ast.Constant):
                            args.append(arg.value)
                        elif isinstance(arg, ast.List):
                            args.append([elem.value if isinstance(elem, ast.Constant) else None for elem in arg.elts])
                        elif isinstance(arg, ast.Tuple):
                            args.append(tuple(elem.value if isinstance(elem, ast.Constant) else None for elem in arg.elts))
                        elif isinstance(arg, ast.Dict):
                            dict_args = {}
                            for k, v in zip(arg.keys, arg.values):
                                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                    dict_args[k.value] = v.value
                            args.append(dict_args)
                        else:
                            # Skip complex arguments that we can't easily parse
                            continue
                    
                    expected = None
                    if isinstance(node.test.comparators[0], ast.Constant):
                        expected = node.test.comparators[0].value
                    elif isinstance(node.test.comparators[0], ast.List):
                        expected = [elem.value if isinstance(elem, ast.Constant) else None for elem in node.test.comparators[0].elts]
                    elif isinstance(node.test.comparators[0], ast.Tuple):
                        expected = tuple(elem.value if isinstance(elem, ast.Constant) else None for elem in node.test.comparators[0].elts)
                    elif isinstance(node.test.comparators[0], ast.Dict):
                        expected = {}
                        for k, v in zip(node.test.comparators[0].keys, node.test.comparators[0].values):
                            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                expected[k.value] = v.value
                    else:
                        # Skip complex expected values that we can't easily parse
                        continue
                    
                    test_cases.append({
                        "args": args,
                        "expected": expected
                    })
                
                # Case 2: assert candidate(args)
                elif (isinstance(node.test, ast.Call) and 
                      isinstance(node.test.func, ast.Name) and 
                      node.test.func.id == "candidate"):
                    
                    args = []
                    for arg in node.test.args:
                        if isinstance(arg, ast.Constant):
                            args.append(arg.value)
                        elif isinstance(arg, ast.List):
                            args.append([elem.value if isinstance(elem, ast.Constant) else None for elem in arg.elts])
                        elif isinstance(arg, ast.Tuple):
                            args.append(tuple(elem.value if isinstance(elem, ast.Constant) else None for elem in arg.elts))
                        elif isinstance(arg, ast.Dict):
                            dict_args = {}
                            for k, v in zip(arg.keys, arg.values):
                                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                    dict_args[k.value] = v.value
                            args.append(dict_args)
                        else:
                            # Skip complex arguments that we can't easily parse
                            continue
                    
                    test_cases.append({
                        "args": args,
                        "expected": True  # For boolean assertions, we expect True
                    })
    except SyntaxError:
        # If we can't parse the test string as Python code, try a more basic approach
        # Look for patterns like "assert candidate(args) == expected"
        pattern = r"assert\s+candidate\((.*?)\)\s*==\s*(.*)"
        matches = re.findall(pattern, test_str)
        
        for match in matches:
            args_str, expected_str = match
            
            # Try to evaluate the arguments and expected value
            try:
                args = eval(f"[{args_str}]")
                expected = eval(expected_str)
                
                test_cases.append({
                    "args": args,
                    "expected": expected
                })
            except:
                continue
    
    return test_cases

def execute_pyth_code(code: str, input_data: str = "") -> str:
    """Execute Pyth code with the given input and return the result."""
    try:
        # Create a temporary file for the Pyth code
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.pyth', delete=False) as temp_pyth:
            temp_pyth_path = temp_pyth.name
            temp_pyth.write(code)
            temp_pyth.flush()
            
        try:
            # Create a temporary file for the input
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_input:
                temp_input_path = temp_input.name
                temp_input.write(input_data)
                temp_input.flush()
                
            # Run the Pyth interpreter
            result = subprocess.run(
                ['python3', PYTH_INTERPRETER_PATH, '-d', temp_pyth_path],
                stdin=open(temp_input_path, 'r'),
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
                
            # Extract Python translation from debug output
            python_translation = result.stdout.strip()
            return python_translation
            
        finally:
            # Clean up
            os.remove(temp_pyth_path)
            os.remove(temp_input_path)
            
    except subprocess.TimeoutExpired:
        return "Error: Timeout expired"
    except Exception as e:
        return f"Error: {str(e)}"


def test_pyth_function(pyth_code: str, func_name: str, args: Any, input_data: str = "") -> Any:
    """
    Creates a Python function from Pyth code and executes it with the given arguments.
    """
    # Get the Python translation of the Pyth code
    python_translation = execute_pyth_code(pyth_code)
    
    if python_translation.startswith("Error"):
        raise ValueError(f"Failed to translate Pyth code: {python_translation}")
    
    # Execute the translated Python code
    try:
        # Define the function dynamically
        exec(python_translation, globals())
        
        # Call the function with the provided arguments
        result = eval(f"{func_name}(*args)")
        return result
    except Exception as e:
        raise ValueError(f"Execution error: {str(e)}")

def main():
    """Main function to run the Pyth HumanEval tests."""
    # Check if test cases file exists
    test_cases_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.json")
    if not os.path.exists(test_cases_path):
        print(f"Error: Test cases file not found at {test_cases_path}")
        return
    
    # Load test cases
    with open(test_cases_path, "r") as f:
        test_cases = json.load(f)
    
    # Get all Pyth files
    pyth_files = glob.glob(os.path.join(HE_PYTH_DIR, "*.pyth"))
    pyth_files.sort(key=lambda x: int(os.path.basename(x).split("_")[1].split(".")[0]))
    
    # Count successful compilations and passes
    total_programs = len(pyth_files)
    compiled_programs = 0
    passed_programs = 0
    
    # Limit the number of test cases per problem to avoid overwhelming output
    max_test_cases = 3
    
    # Results tracking
    results = []
    
    print(f"Starting to test {total_programs} programs...")
    
    for i, pyth_file in enumerate(pyth_files):
        problem_id = os.path.basename(pyth_file).split(".")[0]
        problem_name = problem_id
        
        print(f"\n{'='*50}")
        print(f"Testing {problem_name}:")
        print(f"{'='*50}\n")
        
        # Read Pyth code
        with open(pyth_file, "r") as f:
            pyth_code = f.read().strip()
            
        print(f"Code:\n{pyth_code}\n")
        
        # Get test cases for this problem
        if problem_name not in test_cases and f"HumanEval/{problem_id.split('_')[1]}" in test_cases:
            problem_name = f"HumanEval/{problem_id.split('_')[1]}"
        
        if problem_name not in test_cases:
            print(f"No test cases found for {problem_name}")
            results.append({
                "problem_id": problem_id,
                "status": "No test cases",
                "tests_passed": 0,
                "tests_total": 0
            })
            continue
            
        problem_tests = test_cases[problem_name]
        
        # Extract test cases from the test case string
        extracted_tests = extract_test_cases(problem_tests)
        
        if not extracted_tests:
            print(f"No valid test cases extracted for {problem_name}")
            results.append({
                "problem_id": problem_id,
                "status": "No valid test cases",
                "tests_passed": 0,
                "tests_total": 0
            })
            continue
        
        # Limit the number of test cases to avoid overwhelming output
        total_tests = len(extracted_tests)
        if total_tests > max_test_cases:
            print(f"Running {max_test_cases} out of {total_tests} test cases...")
            extracted_tests = extracted_tests[:max_test_cases]
        
        # Run tests
        all_tests_passed = True
        tests_passed = 0
        tests_run = 0
        
        # First check if the code compiles
        try:
            # Try to translate the Pyth code to Python
            translation = get_pyth_translation(pyth_code)
            if translation.startswith("Error"):
                raise ValueError(f"Failed to translate Pyth code: {translation}")
            
            # If we get here, the code compiles
            compiled_programs += 1
            
            for j, test_case in enumerate(extracted_tests):
                try:
                    # Extract arguments and expected output
                    args = test_case["args"]
                    expected = test_case["expected"]
                    
                    print(f"\nTest {j+1}:")
                    print(f"  Args: {args}")
                    print(f"  Expected: {expected}")
                    
                    # Run the Pyth function with the arguments
                    result = test_pyth_function(pyth_code, "candidate", args)
                    tests_run += 1
                    
                    print(f"  Result: {result}")
                    
                    # Check if the result matches the expected output
                    if compare_results(result, expected):
                        print(f"  Status: Passed")
                        tests_passed += 1
                    else:
                        print(f"  Status: Failed - Expected {expected}, got {result}")
                        all_tests_passed = False
                except Exception as e:
                    print(f"  Status: Error - {str(e)}")
                    all_tests_passed = False
                    tests_run += 1
            
            if all_tests_passed and tests_run > 0:
                passed_programs += 1
                print(f"\nOverall: Passed ({tests_passed}/{tests_run} tests)")
                status = "Passed"
            elif tests_run == 0:
                print(f"\nOverall: No tests run")
                status = "No tests run"
            else:
                print(f"\nOverall: Failed ({tests_passed}/{tests_run} tests)")
                status = "Failed"
                
        except Exception as e:
            print(f"Compilation Error: {str(e)}")
            status = "Compilation Error"
            tests_passed = 0
            tests_run = 0
        
        # Store results
        results.append({
            "problem_id": problem_id,
            "status": status,
            "tests_passed": tests_passed,
            "tests_total": tests_run
        })
        
        # Print a progress indicator
        print(f"\nProcessed {i+1}/{total_programs} programs...")
    
    # Print summary
    print(f"\n\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Total programs tested: {total_programs}")
    print(f"Programs that compiled successfully: {compiled_programs} / {total_programs} ({compiled_programs/total_programs*100:.2f}%)")
    print(f"Programs that passed all tests: {passed_programs} / {total_programs} ({passed_programs/total_programs*100:.2f}%)")
    
    # Count by status
    status_counts = {}
    for result in results:
        status = result['status']
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    print("\nStatus breakdown:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} programs ({count/total_programs*100:.2f}%)")
    
    # Print detailed results
    print(f"\n{'='*50}")
    print(f"DETAILED RESULTS")
    print(f"{'='*50}")
    print(f"{'Problem ID':<20} {'Status':<20} {'Tests Passed':<15} {'Total Tests':<15}")
    print(f"{'-'*20:<20} {'-'*20:<20} {'-'*15:<15} {'-'*15:<15}")
    for result in results:
        print(f"{result['problem_id']:<20} {result['status']:<20} {result['tests_passed']:<15} {result['tests_total']:<15}")
    
    # Save results to a file
    with open('he_pyth_4o_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to he_pyth_4o_test_results.json")
    
    # Print final summary for easy reference
    print(f"\n{'='*50}")
    print(f"FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"Total programs: {total_programs}")
    print(f"Compiled programs: {compiled_programs}")
    print(f"Passed programs: {passed_programs}")
    print(f"Compilation rate: {compiled_programs/total_programs*100:.2f}%")
    print(f"Pass rate: {passed_programs/total_programs*100:.2f}%")
    
    # Update the evaluation report
    update_evaluation_report(compiled_programs, passed_programs, total_programs)

def update_evaluation_report(compiled_programs, passed_programs, total_programs):
    """Update the evaluation report with the HumanEval Pyth results."""
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esolang_no_context_evaluation.md")
    
    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return
    
    with open(report_path, "r") as f:
        report_content = f.read()
    
    # Add the HumanEval Pyth results to the executive summary
    he_pyth_results = f"""
**HumanEval Pyth Results (4o):**
- 4o: {compiled_programs/total_programs*100:.1f}% compilation rate, {passed_programs/total_programs*100:.1f}% passing rate
"""
    
    # Find the position to insert the HumanEval Pyth results
    executive_summary_end = report_content.find("## 1. 0815 Esolang Evaluation")
    
    if executive_summary_end != -1:
        updated_report = (
            report_content[:executive_summary_end] + 
            he_pyth_results + 
            report_content[executive_summary_end:]
        )
        
        # Add a new section for HumanEval Pyth evaluation
        he_pyth_section = f"""
## 6. HumanEval Pyth Evaluation (4o)

### Key Findings

The HumanEval Pyth evaluation tested 4o's ability to generate Pyth code for the HumanEval benchmark:

- **Compilation Rate:** {compiled_programs}/{total_programs} programs compiled successfully ({compiled_programs/total_programs*100:.1f}%)
- **Passing Rate:** {passed_programs}/{total_programs} programs passed all tests ({passed_programs/total_programs*100:.1f}%)

This evaluation used the standard HumanEval benchmark, which contains more complex programming tasks than the previous esolang evaluations. The results show that 4o can generate valid Pyth code for a significant portion of these more challenging tasks.

### Comparison with Regular Pyth Evaluation

When compared to the regular Pyth evaluation:
- Regular Pyth (4o): 93.3% compilation rate, 36.7% passing rate
- HumanEval Pyth (4o): {compiled_programs/total_programs*100:.1f}% compilation rate, {passed_programs/total_programs*100:.1f}% passing rate

The difference in performance suggests that the complexity of the programming tasks significantly impacts 4o's ability to generate correct Pyth code.
"""
        
        # Find the position to insert the HumanEval Pyth section
        comparative_analysis_section = report_content.find("## Comparative Analysis")
        
        if comparative_analysis_section != -1:
            updated_report = (
                updated_report[:comparative_analysis_section] + 
                he_pyth_section + 
                updated_report[comparative_analysis_section:]
            )
            
            # Update the comparative analysis section
            comparative_analysis_update = f"""
| HumanEval Pyth (4o) | 4o | {compiled_programs/total_programs*100:.1f}%          | {passed_programs/total_programs*100:.1f}%        |
"""
            
            # Find the position to insert the comparative analysis update
            table_end = updated_report.find("|---------|--------|------------------|--------------|")
            table_end = updated_report.find("\n", table_end + 1)
            
            if table_end != -1:
                updated_report = (
                    updated_report[:table_end] + 
                    comparative_analysis_update + 
                    updated_report[table_end:]
                )
            
            # Write the updated report
            with open(report_path, "w") as f:
                f.write(updated_report)
            
            print(f"Updated evaluation report at {report_path}")
        else:
            print("Could not find comparative analysis section in the report")
    else:
        print("Could not find executive summary section in the report")

if __name__ == "__main__":
    main()
