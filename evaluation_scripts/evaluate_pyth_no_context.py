import os
import subprocess
import re

def execute_pyth_code(code: str, input_data: str = "", check_compilation_only: bool = False) -> tuple:
    """
    Executes Pyth code and returns the output and compilation status.
    """
    try:
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Write code to a temporary file
        temp_file = os.path.join(current_dir, 'temp.pyth')
        with open(temp_file, 'w') as f:
            f.write(code)

        # Create the command to run the code
        pyth_interpreter = os.path.join(current_dir, 'Pyth/pyth/pyth.py')
        cmd = ['python3', pyth_interpreter, temp_file]
        
        # If we're just checking compilation, add -c flag
        if check_compilation_only:
            cmd = ['python3', pyth_interpreter, '-c', temp_file]

        # Run the command and capture output
        result = subprocess.run(
            cmd,
            input=input_data.encode() if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5  # 5 second timeout
        )

        # Clean up the temporary file
        os.remove(temp_file)

        # Check if compilation was successful (we assume it's successful if there's no error)
        compilation_successful = result.returncode == 0
        
        return result.stdout.decode().strip(), compilation_successful

    except subprocess.TimeoutExpired:
        return "Error: Execution timed out", False
    except Exception as e:
        return f"Error during execution: {str(e)}", False

def read_pyth_code(task_id, folder_name):
    """
    Reads Pyth code from a test file for a given task_id.
    
    Args:
        task_id (str): The task ID
        folder_name (str): The folder to read from
    """
    # Format task_id to match file naming conventions in each folder
    if folder_name == "Pyth_no_context_claude":
        # Claude folder may use 01.pyth, 02.pyth, etc.
        if int(task_id) < 10:
            formatted_task_id = f"0{task_id}"
        else:
            formatted_task_id = f"{task_id}"
    else:
        # 4o folder uses 1.pyth, 2.pyth, etc.
        formatted_task_id = f"{task_id}"
        
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"Pyth/{folder_name}/{formatted_task_id}.pyth")
    try:
        with open(test_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Test file not found: {test_file}")
        return ""

def validate_output(actual, expected):
    """
    Validates if the actual output matches the expected output
    """
    # Normalize both outputs for comparison
    actual = actual.strip().lower()
    expected = expected.strip().lower()
    
    # Handle special cases
    if expected.startswith('[') and expected.endswith(']'):
        # For list outputs, try to convert both to lists and compare
        try:
            actual_list = eval(actual) if actual else []
            expected_list = eval(expected)
            return actual_list == expected_list
        except:
            pass
    
    # For boolean outputs
    if expected in ["true", "false"]:
        return expected in actual
        
    # For numeric outputs
    if expected.isdigit() and any(num == expected for num in re.findall(r'\d+', actual)):
        return True
        
    # Default string comparison
    return expected in actual

problems = [
    {
        'task_id': "1",
        'prompt': 'print hello world',
        "tests": [{'input': '', 'output': 'Hello, World!'}]
    },
    {
        'task_id': "2",
        'prompt': 'given a number n input, return the nth factorial number',
        "tests": [{'input': '5', 'output': '120'}]
    },
    {
        'task_id': "3",
        'prompt': 'given a number n, return "Even" if n is even, else "Odd"',
        "tests": [{'input': '4', 'output': 'Even'}]
    },
    {
        'task_id': "4",
        'prompt': 'given two numbers a and b, return their sum',
        "tests": [{'input': '2\n3', 'output': '5'}]
    },
    {
        'task_id': "5",
        'prompt': 'given a number n, return True if it is prime, else False',
        "tests": [{'input': '11', 'output': 'True'}]
    },
    {
        'task_id': "6",
        'prompt': 'given a string s, return the reversed string',
        "tests": [{'input': 'hello', 'output': 'olleh'}]
    },
     {
        'task_id': "7",
        'prompt': 'print "Hello, Pyth!"',
        "tests": [{'input': '', 'output': 'Hello, Pyth!'}]
    },
    {
        'task_id': "8",
        'prompt': 'given two numbers a and b, return their product',
        "tests": [{'input': '2\n3', 'output': '6'}]
    },
    {
        'task_id': "9",
        'prompt': 'given a number n, return True if it is positive, else False',
        "tests": [{'input': '10', 'output': 'True'}]
    },
    {
        'task_id': "10",
        'prompt': 'given two strings s1 and s2, return their concatenation',
        "tests": [{'input': '"foo", "bar"', 'output': 'foobar'}]
    },
    {
        'task_id': "11",
        'prompt': 'given a number n, return its square',
        "tests": [{'input': '4', 'output': '16'}]
    },
    {
        'task_id': "12",
        'prompt': 'given a string s, return the number of characters in the string',
        "tests": [{'input': '"hello"', 'output': '5'}]
    },
    {
        'task_id': "13",
        'prompt': 'given two numbers a and b, return the smaller number',
        "tests": [{'input': '3\n7', 'output': '3'}]
    },
    {
        'task_id': "14",
        'prompt': 'given a string s, return True if all characters in the string are vowels, else False',
        "tests": [{'input': '"aeiou"', 'output': 'True'}]
    },
    {
        'task_id': "15",
        'prompt': 'given two numbers a and b, return the absolute difference between them',
        "tests": [{'input': '7\n3', 'output': '4'}]
    },
    {
        'task_id': "16",
        'prompt': 'given a string s and a number n, return the string repeated n times',
        "tests": [{'input': '"abc", 3', 'output': 'abcabcabc'}]
    },
    {
      'task_id': "17",
      'prompt': 'given a number n, return the Fibonacci sequence up to the nth term',
      "tests": [{'input': '5', 'output': '[0, 1, 1, 2, 3]'}]
    },
    {
      'task_id': "18",
      'prompt': 'given a list of numbers, return the maximum number',
      "tests": [{'input': '[3, 1, 4, 1, 5, 9]', 'output': '9'}]
    },
    {
      'task_id': "19",
      'prompt': 'given a string s, return True if it is a palindrome, else False',
      "tests": [{'input': '"racecar"', 'output': 'True'}]
    },
    {
      'task_id': "20",
      'prompt': 'given two numbers a and b, return their greatest common divisor',
      "tests": [{'input': '8\n12', 'output': '4'}]
    },
    {
      'task_id': "21",
      'prompt': 'given a list of numbers, return the list sorted in ascending order',
      "tests": [{'input': '[4, 2, 5, 1]', 'output': '[1, 2, 4, 5]'}]
    },
    {
      'task_id': "22",
      'prompt': 'given a number n, return True if it is a perfect square, else False',
      "tests": [{'input': '16', 'output': 'True'}]
    },
    {
      'task_id': "23",
      'prompt': 'given a string s, return the number of vowels in the string',
      "tests": [{'input': '"hello"', 'output': '2'}]
    },
    {
      'task_id': "24",
      'prompt': 'given a list of numbers, return the sum of all numbers in the list',
      "tests": [{'input': '[1, 2, 3, 4]', 'output': '10'}]
    },
    {
      'task_id': "25",
      'prompt': 'given a number n, return its binary representation as a string',
      "tests": [{'input': '10', 'output': '1010'}]
    },
    {
      'task_id': "26",
      'prompt': 'given two strings s1 and s2, return True if s1 is an anagram of s2, else False',
      "tests": [{'input': '"listen", "silent"', 'output': 'True'}]
    },
    {
      'task_id': "27",
      'prompt': 'given a number n, return the sum of digits in n',
      "tests": [{'input': '1234', 'output': '10'}]
    },
    {
      'task_id': "28",
      'prompt': 'given a list of numbers, return True if all numbers are even, else False',
      "tests": [{'input': '[2, 4, 6, 8]', 'output': 'True'}]
    },
    {
      'task_id': "29",
      'prompt': 'given a string s, return the string in title case',
      "tests": [{'input': '"hello world"', 'output': 'Hello World'}]
    },
    {
      'task_id': "30",
      'prompt': 'given two numbers a and b, return True if a is divisible by b, else False',
      "tests": [{'input': '10\n2', 'output': 'True'}]
    }
]

def main():
    """
    Main function to evaluate Pyth_no_context folders.
    """
    folders = ["Pyth_no_context_4o", "Pyth_no_context_claude"]
    
    # Results for each folder
    results = {}
    
    for folder in folders:
        print(f"\n\n=== Evaluating {folder} ===\n")
        
        # Statistics
        total_programs = len(problems)
        compilable_programs = 0
        passing_programs = 0
        passing_tasks = []
        
        for problem in problems:
            task_id = problem['task_id']
            tests = problem['tests']
            
            print(f"\nTask {task_id}: {problem['prompt']}")
            
            # Read Pyth code
            code = read_pyth_code(task_id, folder)
            if not code:
                print(f"No code found for task {task_id}")
                continue
            
            print("\nCode:")
            print(code)
            
            # Check compilation first
            _, compilation_successful = execute_pyth_code(code, check_compilation_only=True)
            
            if compilation_successful:
                compilable_programs += 1
                print("Compilation: SUCCESS")
            else:
                print("Compilation: FAILED")
                continue
            
            print("\nRunning tests:")
            
            all_passed = True
            for i, test in enumerate(tests):
                input_data = test.get('input', '')
                expected_output = test.get('output', '')
                
                print(f"\nTest {i + 1}:")
                print(f"Input: {input_data}")
                print(f"Expected Output: {expected_output}")
                
                actual_output, _ = execute_pyth_code(code, input_data)
                print(f"Actual Output: {actual_output}")
                
                if validate_output(actual_output, expected_output):
                    print("✓ Test passed!")
                else:
                    print("✗ Test failed!")
                    all_passed = False
            
            if all_passed:
                print(f"\n✓ All tests passed for Task {task_id}!")
                passing_programs += 1
                passing_tasks.append(task_id)
            else:
                print(f"\n✗ Some tests failed for Task {task_id}")
        
        # Store results for this folder
        results[folder] = {
            'total': total_programs,
            'compilable': compilable_programs,
            'passing': passing_programs,
            'passing_tasks': passing_tasks
        }
    
    # Print summary for all folders
    print("\n\n=== Summary ===")
    for folder, stats in results.items():
        compilable_rate = stats['compilable'] / stats['total'] * 100 if stats['total'] > 0 else 0
        passing_rate = stats['passing'] / stats['total'] * 100 if stats['total'] > 0 else 0
        pass_rate_compiled = stats['passing'] / stats['compilable'] * 100 if stats['compilable'] > 0 else 0
        
        print(f"\n{folder}:")
        print(f"  Total programs: {stats['total']}")
        print(f"  Compilable programs: {stats['compilable']} ({compilable_rate:.1f}%)")
        print(f"  Passing programs: {stats['passing']} ({passing_rate:.1f}%)")
        if stats['compilable'] > 0:
            print(f"  Pass rate among compiled programs: {pass_rate_compiled:.1f}%")
        print(f"  Passing tasks: {', '.join(stats['passing_tasks'])}")
    
    return results

if __name__ == "__main__":
    main()
