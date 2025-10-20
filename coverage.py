#!/usr/bin/env python3
import os
import re
from prettytable import PrettyTable

# === Config ===
CODE_DIR = "."
TEST_FILES = ["routing_healthcheck.py", "network_tests", "test_ipvalidate.py", "test_password_rotation.py", "test_healthcheck.py"]


def get_functions_from_file(filepath):
    functions = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                match = re.match(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line)
                if match:
                    functions.append(match.group(1))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return functions


def get_all_code_files(directory):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".py") and file not in TEST_FILES and file != "coverage_tool.py":
            files.append(file)
    return files


def get_all_test_content():
    content = ""
    for test_file in TEST_FILES:
        if os.path.exists(test_file):
            with open(test_file, "r") as f:
                content += f.read()
    return content


def calculate_coverage():
    test_content = get_all_test_content()
    code_files = get_all_code_files(CODE_DIR)
    table = PrettyTable(["Module", "Total Functions", "Tested Functions", "Coverage %"])

    for file in code_files:
        functions = get_functions_from_file(file)
        total = len(functions)
        tested = 0
        for func in functions:
            if re.search(rf"\b{func}\b", test_content):
                tested += 1
        coverage = round((tested / total * 100), 2) if total > 0 else 0
        table.add_row([file, total, tested, f"{coverage}%"])
    return table


if __name__ == "__main__":
    print("\n=== Test Coverage Report ===")
    report = calculate_coverage()
    print(report)
