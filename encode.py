#!/usr/bin/env python3
"""
encode.py - Main encoding script (Zip → QR Codes)

This script processes a ZIP file and converts all contained files into QR codes
with XML payload wrapping. Each QR code contains metadata and base64-encoded content.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import load_config, setup_logging, ensure_directory, save_json
from src.zip_processor import ZipProcessor
from src.qr_encoder import QREncoder


class ZipToQREncoder:
    def __init__(self, config):
        self.config = config
        self.zip_processor = ZipProcessor(config)
        self.qr_encoder = QREncoder(config)
        
    def process_zip_file(self, zip_path, output_dir):
        """Main processing function."""
        logging.info(f"Starting processing of {zip_path}")
        
        # Validate ZIP file
        if not self.zip_processor.validate_zip_file(zip_path):
            logging.error("ZIP file validation failed")
            return None
        
        # Create output directory
        ensure_directory(output_dir)
        
        try:
            # Extract ZIP file
            extracted_files = self.zip_processor.extract_zip(zip_path)
            
            if not extracted_files:
                logging.error("No files extracted from ZIP")
                return None
            
            # Encode files to QR codes
            manifest, qr_files = self.qr_encoder.encode_all_files(extracted_files, output_dir)
            
            # Update manifest with source info
            manifest["source_zip"] = zip_path
            manifest["creation_timestamp"] = datetime.now().isoformat()
            
            # Save updated manifest
            manifest_path = os.path.join(output_dir, "manifest.json")
            save_json(manifest, manifest_path)
            
            # Clean up temporary files
            if self.config.get("cleanup_temp", True):
                self.zip_processor.cleanup_temp_files()
            
            logging.info(f"Processing complete! Generated {manifest['total_qr_codes']} QR codes")
            return manifest
            
        except Exception as e:
            logging.error(f"Error during processing: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Convert ZIP file to QR codes")
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
    parser.add_argument("--silent", 
                       action="store_true",
                       help="Suppress progress bars")
    parser.add_argument("--no-cleanup", 
                       action="store_true",
                       help="Don't cleanup temporary files")
    
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
    if args.no_cleanup:
        config["cleanup_temp"] = False
    
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
    encoder = ZipToQREncoder(config)
    
    try:
        manifest = encoder.process_zip_file(zip_path, output_dir)
        
        if manifest:
            if args.agent_mode:
                print(f"SUCCESS: {manifest['total_qr_codes']} QR codes generated")
            else:
                print(f"Encoding complete!")
                print(f"Generated {manifest['total_qr_codes']} QR codes in {output_dir}")
                print(f"Processed {len(manifest['files'])} files")
                print(f"Manifest saved: {os.path.join(output_dir, 'manifest.json')}")
            sys.exit(0)
        else:
            if args.agent_mode:
                print("FAILED: Encoding failed")
            else:
                print("Encoding failed - check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Encoding interrupted by user")
        print("Encoding interrupted")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.agent_mode:
            print(f"FAILED: {e}")
        else:
            print(f"Encoding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
