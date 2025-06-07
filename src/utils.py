"""
Utility functions for the zip-to-qr converter project.
"""
import os
import hashlib
import json
import yaml
import logging
from pathlib import Path


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found, using defaults")
        return get_default_config()


def get_default_config():
    """Get default configuration."""
    return {
        "zip_path": "C:\\huggingface\\gpt-2-master.zip",
        "qr_output_directory": "images",
        "file_output_directory": "output",
        "temp_directory": "temp",
        "max_chunk_size": 2048,
        "qr_error_correction": "M",
        "qr_box_size": 10,
        "qr_border": 4,
        "qr_version": None,
        "xml_template": '<doc page="{page_num}" x="@tariusdamon" file="{filename}" chunk="{chunk_id}" total="{total_chunks}">{content}</doc>',
        "preserve_structure": True,
        "include_hidden_files": False,
        "compress_before_encoding": True,
        "calculate_checksums": True,
        "verify_integrity": True
    }


def calculate_checksum(data):
    """Calculate SHA-256 checksum of data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def setup_logging(log_file=None, level=logging.INFO):
    """Setup logging configuration."""
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def ensure_directory(path):
    """Ensure directory exists, create if not."""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_json(data, filepath):
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filepath):
    """Load data from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_file_size_mb(filepath):
    """Get file size in MB."""
    return os.path.getsize(filepath) / (1024 * 1024)


def format_bytes(bytes_count):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} TB"
