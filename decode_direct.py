#!/usr/bin/env python3
"""
decode_direct.py - Direct QR to ZIP reconstruction

This script reconstructs a ZIP file directly from QR codes without
extracting individual files. The QR codes contain the raw ZIP data.
"""

import os
import sys
import argparse
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import load_config, setup_logging, ensure_directory, load_json, calculate_checksum
from src.qr_decoder import QRDecoder
from src.file_assembler import FileAssembler


class DirectQRToZipDecoder:
    def __init__(self, config):
        self.config = config
        self.qr_decoder = QRDecoder(config)
        self.file_assembler = FileAssembler(config)
        
    def decode_qr_to_zip_direct(self, qr_dir, output_dir, manifest_path=None):
        """Reconstruct ZIP file directly from QR codes."""
        logging.info(f"Starting direct QR decoding from {qr_dir}")
        
        # Ensure output directory exists
        ensure_directory(output_dir)
        
        try:
            # Scan all QR codes
            if not self.qr_decoder.scan_all_qr_codes(qr_dir):
                logging.error("Failed to scan QR codes")
                return None
            
            # Load manifest data if available
            manifest_data = None
            if manifest_path and os.path.exists(manifest_path):
                manifest_data = load_json(manifest_path)
                logging.info("Loaded manifest data for verification")
            elif os.path.exists(os.path.join(qr_dir, "manifest.json")):
                manifest_data = load_json(os.path.join(qr_dir, "manifest.json"))
                logging.info("Loaded manifest data from QR directory")
            
            # Get the files from scanned data
            files = self.qr_decoder.get_all_files()
            
            if not files:
                logging.error("No files found in QR codes")
                return None
            
            if len(files) > 1:
                logging.warning(f"Multiple files found, expected single ZIP file: {files}")
            
            # Use the first (and should be only) file
            zip_filename = files[0]
            chunks = self.qr_decoder.get_file_chunks(zip_filename)
            
            logging.info(f"Reconstructing ZIP file: {zip_filename}")
            logging.info(f"Found {len(chunks)} chunks")
            
            # Verify chunk integrity
            is_complete, missing_chunks = self.file_assembler.verify_file_integrity(
                zip_filename, chunks
            )
            
            if not is_complete:
                logging.error(f"Missing chunks: {missing_chunks}")
                if not self.config.get("force_reconstruction", False):
                    return None
                logging.warning("Proceeding with partial reconstruction (forced)")
            
            # Reconstruct the ZIP file
            zip_content, actual_checksum = self.file_assembler.reconstruct_file(zip_filename, chunks)
            
            if zip_content is None:
                logging.error("Failed to reconstruct ZIP file")
                return None
            
            # Determine output filename
            output_filename = zip_filename
            if manifest_data and "source_filename" in manifest_data:
                output_filename = manifest_data["source_filename"]
            
            output_path = os.path.join(output_dir, output_filename)
            
            # Save the reconstructed ZIP file
            try:
                with open(output_path, 'wb') as f:
                    f.write(zip_content)
                
                logging.info(f"Saved reconstructed ZIP: {output_path}")
                
                # Verify against manifest checksum if available
                checksum_match = True
                if manifest_data and "source_checksum" in manifest_data:
                    expected_checksum = manifest_data["source_checksum"]
                    if actual_checksum == expected_checksum:
                        logging.info("Checksum verification PASSED")
                    else:
                        logging.error("Checksum verification FAILED")
                        logging.error(f"Expected: {expected_checksum}")
                        logging.error(f"Actual: {actual_checksum}")
                        checksum_match = False
                
                # Create reconstruction report
                report = {
                    "status": "success",
                    "output_file": output_path,
                    "original_filename": zip_filename,
                    "reconstructed_size": len(zip_content),
                    "chunks_used": len(chunks),
                    "checksum": actual_checksum,
                    "checksum_match": checksum_match,
                    "complete_reconstruction": is_complete,
                    "missing_chunks": missing_chunks if not is_complete else []
                }
                
                # Save report
                from src.utils import save_json
                report_path = os.path.join(output_dir, "reconstruction_report.json")
                save_json(report, report_path)
                
                logging.info("Direct reconstruction complete!")
                return report
                
            except Exception as e:
                logging.error(f"Failed to save ZIP file: {e}")
                return None
            
        except Exception as e:
            logging.error(f"Error during direct decoding: {e}")
            return None
    
    def verify_reconstructed_zip(self, zip_path):
        """Verify that the reconstructed ZIP file is valid."""
        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Test the ZIP file
                bad_file = zf.testzip()
                if bad_file:
                    logging.error(f"Corrupted file in reconstructed ZIP: {bad_file}")
                    return False
                
                # List contents
                file_list = zf.namelist()
                logging.info(f"Reconstructed ZIP contains {len(file_list)} files")
                return True
                
        except zipfile.BadZipFile:
            logging.error("Reconstructed file is not a valid ZIP archive")
            return False
        except Exception as e:
            logging.error(f"Error verifying ZIP file: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Reconstruct ZIP file directly from QR codes")
    parser.add_argument("--qr-dir", 
                       help="Directory containing QR codes")
    parser.add_argument("--output-dir", 
                       help="Output directory for reconstructed ZIP file")
    parser.add_argument("--config", 
                       default="config.yaml",
                       help="Configuration file path")
    parser.add_argument("--manifest", 
                       help="Path to manifest.json file for verification")
    parser.add_argument("--log-level", 
                       default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    parser.add_argument("--log-file", 
                       help="Log file path")
    parser.add_argument("--agent-mode", 
                       action="store_true",
                       help="Run in agent mode (minimal output)")
    parser.add_argument("--force-reconstruct", 
                       action="store_true",
                       help="Force reconstruction even with missing chunks")
    parser.add_argument("--verify-zip", 
                       action="store_true",
                       help="Verify reconstructed ZIP file integrity")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.qr_dir:
        config["qr_input_directory"] = args.qr_dir
    if args.output_dir:
        config["file_output_directory"] = args.output_dir
    if args.force_reconstruct:
        config["force_reconstruction"] = True
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(args.log_file, log_level)
    
    if args.agent_mode:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Validate required parameters
    qr_dir = config.get("qr_input_directory", config.get("qr_output_directory", "images"))
    output_dir = config.get("file_output_directory", "output")
    
    if not qr_dir:
        logging.error("No QR directory specified")
        sys.exit(1)
    
    if not os.path.exists(qr_dir):
        logging.error(f"QR directory not found: {qr_dir}")
        sys.exit(1)
    
    # Create decoder
    decoder = DirectQRToZipDecoder(config)
    
    try:
        # Run decoding
        report = decoder.decode_qr_to_zip_direct(qr_dir, output_dir, args.manifest)
        
        if report:
            # Verify ZIP if requested
            if args.verify_zip:
                is_valid = decoder.verify_reconstructed_zip(report["output_file"])
                report["zip_valid"] = is_valid
                
                if is_valid:
                    logging.info("ZIP file verification PASSED")
                else:
                    logging.error("ZIP file verification FAILED")
            
            if args.agent_mode:
                if report["status"] == "success":
                    print(f"SUCCESS: ZIP file reconstructed")
                    if not report.get("checksum_match", True):
                        print("WARNING: Checksum mismatch")
                    if not report.get("complete_reconstruction", True):
                        print(f"WARNING: Partial reconstruction, missing {len(report['missing_chunks'])} chunks")
                else:
                    print("FAILED: Reconstruction failed")
            else:
                print(f"Direct reconstruction complete!")
                print(f"Status: {report['status']}")
                print(f"Output file: {report['output_file']}")
                print(f"Size: {report['reconstructed_size']:,} bytes")
                print(f"Checksum: {report['checksum']}")
                if report.get("checksum_match", True):
                    print("✓ Checksum verification passed")
                else:
                    print("✗ Checksum verification failed")
                if report.get("complete_reconstruction", True):
                    print("✓ Complete reconstruction")
                else:
                    print(f"⚠ Partial reconstruction (missing {len(report['missing_chunks'])} chunks)")
                print(f"Report saved: {os.path.join(output_dir, 'reconstruction_report.json')}")
            
            # Exit code based on success
            if report["status"] == "success":
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            if args.agent_mode:
                print("FAILED: Direct reconstruction failed")
            else:
                print("Direct reconstruction failed - check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Direct reconstruction interrupted by user")
        print("Direct reconstruction interrupted")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.agent_mode:
            print(f"FAILED: {e}")
        else:
            print(f"Direct reconstruction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
