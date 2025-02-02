from pathlib import Path
import os

# Get the absolute base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Define file mappings with absolute paths
file_mapping = {
    "sql": BASE_DIR / "Examples/SQLTestDouble.txt",
    "cds": BASE_DIR / "Examples/CDSTestDouble.txt",
    "ooabap": BASE_DIR / "Examples/OO-AbapTestDouble.txt",
    "func": BASE_DIR / "Examples/FuncModuleTestDouble.txt",
    "authcheck": BASE_DIR / "Examples/AuthCheckController.txt",
    "testseams": BASE_DIR / "Examples/TestSeams.txt",
}

test_double_type ="sql"

# Get the file path
file_path = file_mapping[test_double_type]

print(file_path)

# Ensure file exists and is accessible
if not file_path.exists():
    raise FileNotFoundError(f"File not found: {file_path}")
if not os.access(file_path, os.R_OK):  # Check read permissions
    raise PermissionError(f"Permission denied: {file_path}")

print(f"BASE_DIR: {BASE_DIR}")
print(f"File Mapping: {file_mapping}")
