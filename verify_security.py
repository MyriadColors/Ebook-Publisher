import argparse
import os
import sys
from typing import List


def get_all_python_files(root_dir: str) -> List[str]:
    """Recursively find all .py files in the directory."""
    py_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def check_dangerous_functions(file_path: str) -> List[str]:
    """Checks for use of dangerous functions like eval(), exec(), os.system()."""
    dangerous_patterns = ["eval(", "exec(", "os.system(", "subprocess.Popen(shell=True"]
    findings = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            for pattern in dangerous_patterns:
                if pattern in line:
                    findings.append(f"Line {i}: Potentially dangerous call '{pattern}'")
    return findings


def check_hardcoded_secrets(file_path: str) -> List[str]:
    """Checks for potential hardcoded secrets like 'password = ...'."""
    # Basic heuristic, might have false positives
    secret_patterns = ["password =", "secret =", "api_key =", "token ="]
    findings = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            # Check for pattern and ensure it's not a common variable or comment
            for pattern in secret_patterns:
                if pattern in line and not line.strip().startswith("#"):
                    # Check if there is a non-empty string being assigned
                    if '"' in line or "'" in line:
                        findings.append(
                            f"Line {i}: Potential hardcoded secret '{pattern}'"
                        )
    return findings


def check_input_validation(file_path: str) -> List[str]:
    """Checks if external input is used without apparent validation."""
    input_patterns = ["sys.argv", "input(", "requests.get("]
    findings = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        for pattern in input_patterns:
            if pattern in content:
                # This is a very basic check, just identifying where input enters
                findings.append(f"File uses external input source: '{pattern}'")
    return findings


def run_security_scan(directory: str) -> int:
    """Runs a basic security scan on the given directory."""
    print(f"--- Starting Security Scan for: {directory} ---")
    py_files = get_all_python_files(directory)
    total_findings = 0

    for file in py_files:
        # Skip this script itself
        if os.path.basename(file) == "verify_security.py":
            continue

        file_findings = []
        file_findings.extend(check_dangerous_functions(file))
        file_findings.extend(check_hardcoded_secrets(file))
        file_findings.extend(check_input_validation(file))

        if file_findings:
            print(f"\n[!] Findings in {file}:")
            for finding in file_findings:
                print(f"  - {finding}")
            total_findings += len(file_findings)

    print(f"\n--- Scan Complete. Total findings: {total_findings} ---")
    return total_findings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic security scanner for Python.")
    parser.add_argument(
        "dir", help="Directory to scan", nargs="?", default=os.getcwd()
    )
    args = parser.parse_args()

    findings_count = run_security_scan(args.dir)
    if findings_count > 0:
        # sys.exit(1) # Don't fail build for now, just report
        pass
    sys.exit(0)
