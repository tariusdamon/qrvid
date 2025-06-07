#!/usr/bin/env python3
"""
encode_direct.py - Direct ZIP to QR conversion (no extraction)

This script converts a ZIP file directly to QR codes without extracting it.
The entire ZIP file is treated as binary data and chunked into QR codes.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import load_config, setup_logging, ensure_directory, save_json, calculate_checksum
from src.qr_encoder import QREncoder
from src.xml_wrapper import XMLWrapper


class DirectZipToQREncoder:
    def __init__(self, config):
        self.config = config
        self.qr_encoder = QREncoder(config)
        self.xml_wrapper = XMLWrapper(config)
        
    def process_zip_direct(self, zip_path, output_dir):
        """Process ZIP file directly without extraction."""
        logging.info(f"Starting direct processing of {zip_path}")
        
        # Validate ZIP file exists
        if not os.path.exists(zip_path):
            logging.error(f"ZIP file not found: {zip_path}")
            return None
        
        # Create output directory
        ensure_directory(output_dir)
        
        try:
            # Read entire ZIP file
            logging.info("Reading ZIP file...")
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            zip_size = len(zip_data)
            logging.info(f"ZIP file size: {zip_size:,} bytes")
            
            # Calculate checksum
            zip_checksum = calculate_checksum(zip_data)
            logging.info(f"ZIP checksum: {zip_checksum}")
            
            # Get filename from path
            zip_filename = os.path.basename(zip_path)
            
            # Create file info structure for encoding
            file_info = {
                "path": zip_filename,
                "content": zip_data,
                "size": zip_size,
                "checksum": zip_checksum
            }
            
            # Encode to QR codes
            qr_files = self.qr_encoder.encode_file_to_qr_codes(file_info, output_dir)
            
            if not qr_files:
                logging.error("Failed to generate QR codes")
                return None
            
            # Create manifest
            manifest = {
                "total_qr_codes": len(qr_files),
                "source_file": zip_path,
                "source_filename": zip_filename,
                "source_size": zip_size,
                "source_checksum": zip_checksum,
                "creation_timestamp": datetime.now().isoformat(),
                "chunk_size": self.config.get("max_chunk_size", 2048),
                "encoding_type": "direct_zip",
                "qr_codes": [qr["page_num"] for qr in qr_files]
            }
            
            # Save manifest
            manifest_path = os.path.join(output_dir, "manifest.json")
            save_json(manifest, manifest_path)
            
            logging.info(f"Direct processing complete! Generated {manifest['total_qr_codes']} QR codes")
            return manifest
            
        except Exception as e:
            logging.error(f"Error during direct processing: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Convert ZIP file directly to QR codes (no extraction)")
    parser.add_argument("--input-zip", 
                       help="Path to input ZIP file")
    parser.add_argument("--output-dir", 
                       help="Output directory for QR codes")
    parser.add_argument("--config", 
                       default="config.yaml",
                       help="Configuration file path")
    parser.add_argument("--chunk-size", 
                       type=int,
                       help="Maximum chunk size for QR codes")
    parser.add_argument("--log-level", 
                       default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    parser.add_argument("--log-file", 
                       help="Log file path")
    parser.add_argument("--agent-mode", 
                       action="store_true",
                       help="Run in agent mode (minimal output)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.input_zip:
        config["zip_path"] = args.input_zip
    if args.output_dir:
        config["qr_output_directory"] = args.output_dir
    if args.chunk_size:
        config["max_chunk_size"] = args.chunk_size
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(args.log_file, log_level)
    
    if args.agent_mode:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Validate required parameters
    zip_path = config.get("zip_path")
    output_dir = config.get("qr_output_directory", "images")
    
    if not zip_path:
        logging.error("No input ZIP file specified")
        sys.exit(1)
    
    if not os.path.exists(zip_path):
        logging.error(f"ZIP file not found: {zip_path}")
        sys.exit(1)
    
    # Create encoder and process
    encoder = DirectZipToQREncoder(config)
    
    try:
        manifest = encoder.process_zip_direct(zip_path, output_dir)
        
        if manifest:
            if args.agent_mode:
                print(f"SUCCESS: {manifest['total_qr_codes']} QR codes generated")
            else:
                print(f"Direct encoding complete!")
                print(f"Generated {manifest['total_qr_codes']} QR codes in {output_dir}")
                print(f"Source file: {manifest['source_filename']} ({manifest['source_size']:,} bytes)")
                print(f"Checksum: {manifest['source_checksum']}")
                print(f"Manifest saved: {os.path.join(output_dir, 'manifest.json')}")
            sys.exit(0)
        else:
            if args.agent_mode:
                print("FAILED: Direct encoding failed")
            else:
                print("Direct encoding failed - check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Direct encoding interrupted by user")
        print("Direct encoding interrupted")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.agent_mode:
            print(f"FAILED: {e}")
        else:
            print(f"Direct encoding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
