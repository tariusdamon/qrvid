#!/usr/bin/env python3
"""
decode.py - Main decoding script (QR Codes → Files)

This script scans QR codes and reconstructs the original files from
the XML-wrapped content chunks.
"""

import os
import sys
import argparse
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import load_config, setup_logging, ensure_directory, load_json
from src.qr_decoder import QRDecoder
from src.file_assembler import FileAssembler


class QRToFileDecoder:
    def __init__(self, config):
        self.config = config
        self.qr_decoder = QRDecoder(config)
        self.file_assembler = FileAssembler(config)
        
    def decode_qr_codes_to_files(self, qr_dir, output_dir, manifest_path=None):
        """Main decoding function."""
        logging.info(f"Starting QR decoding from {qr_dir}")
        
        # Ensure output directory exists
        ensure_directory(output_dir)
        
        try:
            # Scan all QR codes
            if not self.qr_decoder.scan_all_qr_codes(qr_dir):
                logging.error("Failed to scan QR codes")
                return None
            
            # Get scan statistics
            stats = self.qr_decoder.get_scan_statistics()
            logging.info(f"Scanned {stats['total_qr_codes']} QR codes for {stats['total_files']} files")
            
            # Verify scan integrity
            is_complete, incomplete_files = self.qr_decoder.verify_scan_integrity()
            
            if not is_complete and not self.config.get("allow_partial_reconstruction", False):
                logging.error("Incomplete scan data found - some chunks are missing")
                for file_info in incomplete_files:
                    logging.error(f"  {file_info['filename']}: missing chunks {file_info['missing_chunks']}")
                
                if not self.config.get("force_reconstruction", False):
                    return None
            
            # Load manifest data if available
            manifest_data = None
            if manifest_path and os.path.exists(manifest_path):
                manifest_data = load_json(manifest_path)
                logging.info("Loaded manifest data for verification")
            elif os.path.exists(os.path.join(qr_dir, "manifest.json")):
                manifest_data = load_json(os.path.join(qr_dir, "manifest.json"))
                logging.info("Loaded manifest data from QR directory")
            
            # Reconstruct files
            file_chunks = dict(self.qr_decoder.file_chunks)
            report = self.file_assembler.save_reconstructed_files(
                file_chunks, output_dir, manifest_data
            )
            
            logging.info("Decoding complete!")
            return report
            
        except Exception as e:
            logging.error(f"Error during decoding: {e}")
            return None
    
    def diagnose_qr_codes(self, qr_dir):
        """Diagnose QR code directory for issues."""
        logging.info(f"Diagnosing QR codes in {qr_dir}")
        
        if not os.path.exists(qr_dir):
            logging.error(f"QR directory not found: {qr_dir}")
            return False
        
        # Scan QR codes
        if not self.qr_decoder.scan_all_qr_codes(qr_dir):
            logging.error("Failed to scan QR codes")
            return False
        
        # Get detailed statistics
        stats = self.qr_decoder.get_scan_statistics()
        
        print(f"\nDiagnostic Report for {qr_dir}")
        print("=" * 50)
        print(f"Total QR codes scanned: {stats['total_qr_codes']}")
        print(f"Total files found: {stats['total_files']}")
        print()
        
        complete_files = 0
        incomplete_files = 0
        
        for filename, file_stats in stats['files'].items():
            status = "COMPLETE" if file_stats['complete'] else "INCOMPLETE"
            print(f"{status}: {filename}")
            print(f"  Chunks: {file_stats['chunks_found']}/{file_stats['total_chunks']}")
            
            if file_stats['missing_chunks']:
                print(f"  Missing: {file_stats['missing_chunks']}")
                incomplete_files += 1
            else:
                complete_files += 1
            print()
        
        print(f"Summary: {complete_files} complete, {incomplete_files} incomplete")
        return True


def main():
    parser = argparse.ArgumentParser(description="Reconstruct files from QR codes")
    parser.add_argument("--qr-dir", 
                       help="Directory containing QR codes")
    parser.add_argument("--output-dir", 
                       help="Output directory for reconstructed files")
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
    parser.add_argument("--verify-integrity", 
                       action="store_true",
                       help="Verify file integrity with checksums")
    parser.add_argument("--allow-partial", 
                       action="store_true",
                       help="Allow partial reconstruction of incomplete files")
    parser.add_argument("--force-reconstruct", 
                       action="store_true",
                       help="Force reconstruction even with missing chunks")
    parser.add_argument("--skip-verification", 
                       action="store_true",
                       help="Skip integrity verification")
    parser.add_argument("--diagnose", 
                       action="store_true",
                       help="Diagnose QR codes and report status")
    parser.add_argument("--qr-library", 
                       choices=["pyzbar", "opencv"],
                       help="QR code reading library to use")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.qr_dir:
        config["qr_input_directory"] = args.qr_dir
    if args.output_dir:
        config["file_output_directory"] = args.output_dir
    if args.verify_integrity:
        config["verify_integrity"] = True
    if args.allow_partial:
        config["allow_partial_reconstruction"] = True
    if args.force_reconstruct:
        config["force_reconstruction"] = True
    if args.skip_verification:
        config["verify_integrity"] = False
    
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
    decoder = QRToFileDecoder(config)
    
    try:
        if args.diagnose:
            # Run diagnostic mode
            if decoder.diagnose_qr_codes(qr_dir):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            # Run normal decoding
            report = decoder.decode_qr_codes_to_files(qr_dir, output_dir, args.manifest)
            
            if report:
                if args.agent_mode:
                    print(f"SUCCESS: {report['successful']} files reconstructed")
                    if report['partial'] > 0:
                        print(f"PARTIAL: {report['partial']} files partially reconstructed")
                    if report['failed'] > 0:
                        print(f"FAILED: {report['failed']} files failed")
                else:
                    print(f"Decoding complete!")
                    print(f"Successful: {report['successful']} files")
                    if report['partial'] > 0:
                        print(f"Partial: {report['partial']} files")
                    if report['failed'] > 0:
                        print(f"Failed: {report['failed']} files")
                    print(f"Output directory: {output_dir}")
                    print(f"Report saved: {os.path.join(output_dir, 'reconstruction_report.json')}")
                
                # Exit with appropriate code
                if report['failed'] > 0 and report['successful'] == 0:
                    sys.exit(1)  # Complete failure
                else:
                    sys.exit(0)  # Success or partial success
            else:
                if args.agent_mode:
                    print("FAILED: Decoding failed")
                else:
                    print("Decoding failed - check logs for details")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logging.info("Decoding interrupted by user")
        print("Decoding interrupted")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.agent_mode:
            print(f"FAILED: {e}")
        else:
            print(f"Decoding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
