import random
import numpy as np
from faker import Faker
import json
import csv
import yaml
from pathlib import Path
import shutil

# Global Faker instance
fake = Faker()

def setup_seeds(seed: int):
    """Set the seeds for reproducibility across random libraries."""
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)
    fake.seed_instance(seed)

def create_output_directories(base_dir: str):
    """Creates the standard directory tree for OrgMemory-10K."""
    base_path = Path(base_dir)
    
    # List of subdirectories
    subdirs = [
        "employees",
        "architecture",
        "github",
        "jira",
        "meetings",
        "deployments",
        "monitoring",
        "incidents",
        "feedback",
        "customers",
        "hindsight",
        "benchmark",
        "generator"
    ]
    
    # Create base path
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirs
    for subdir in subdirs:
        (base_path / subdir).mkdir(parents=True, exist_ok=True)
        
    return base_path

def write_json(data, file_path: Path):
    """Write data to a JSON file with pretty printing."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def write_csv(data, headers, file_path: Path):
    """Write list of dicts to a CSV file."""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in data:
            # Flatten or format dictionary values for CSV output
            clean_row = {}
            for k in headers:
                val = row.get(k, "")
                if isinstance(val, (list, dict)):
                    clean_row[k] = json.dumps(val)
                else:
                    clean_row[k] = val
            writer.writerow(clean_row)

def write_yaml(data, file_path: Path):
    """Write data to a YAML file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def write_markdown(content: str, file_path: Path):
    """Write string content to a Markdown file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def copy_generator_code(src_dir: str, dest_dir: Path):
    """Copy the generator files to the output directory to make it self-contained."""
    src_path = Path(src_dir)
    # Ensure source generator dir exists
    if src_path.exists():
        # Copy python files
        for p in src_path.glob("**/*.py"):
            rel_p = p.relative_to(src_path)
            target = dest_dir / "generator" / rel_p
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
        
        # Copy requirements.txt
        req_file = src_path / "requirements.txt"
        if req_file.exists():
            shutil.copy2(req_file, dest_dir / "generator" / "requirements.txt")
