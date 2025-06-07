"""
File assembler for reconstructing files from QR code chunks.
"""
import base64
import os
import logging
from pathlib import Path
from tqdm import tqdm
from .utils import calculate_checksum, ensure_directory, save_json


class FileAssembler:
    def __init__(self, config):
        self.config = config
        
    def verify_file_integrity(self, filename, chunks, expected_checksum=None):
        """Verify file chunk integrity and completeness."""
        if not chunks:
            logging.error(f"No chunks found for {filename}")
            return False, ["No chunks available"]
        
        total_chunks = max(chunk["total"] for chunk in chunks.values())
        
        # Check if all chunks are present
        missing_chunks = []
        for i in range(1, total_chunks + 1):
            if i not in chunks:
                missing_chunks.append(i)
                
        if missing_chunks:
            logging.warning(f"Missing chunks for {filename}: {missing_chunks}")
            return False, missing_chunks
            
        logging.info(f"All chunks present for {filename}")
        return True, []
    
    def reconstruct_file(self, filename, chunks):
        """Reconstruct file from chunks."""
        try:
            # Sort chunks by chunk ID
            sorted_chunks = sorted(chunks.items())
            
            # Combine base64 content
            combined_b64 = ''.join(chunk_data["content"] for _, chunk_data in sorted_chunks)
            
            # Decode from base64
            try:
                file_content = base64.b64decode(combined_b64)
            except Exception as e:
                logging.error(f"Base64 decode error for {filename}: {e}")
                return None, None
            
            # Calculate checksum
            checksum = calculate_checksum(file_content)
            
            logging.info(f"Reconstructed {filename}: {len(file_content)} bytes, checksum: {checksum[:16]}...")
            
            return file_content, checksum
            
        except Exception as e:
            logging.error(f"Error reconstructing {filename}: {e}")
            return None, None
    
    def save_file(self, filepath, content):
        """Save file content to disk."""
        try:
            # Create directory structure
            directory = os.path.dirname(filepath)
            if directory:
                ensure_directory(directory)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(content)
            
            logging.debug(f"Saved file: {filepath}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving {filepath}: {e}")
            return False
    
    def save_reconstructed_files(self, file_chunks, output_dir, manifest_data=None):
        """Save all reconstructed files."""
        ensure_directory(output_dir)
        
        reconstruction_report = {
            "total_files": len(file_chunks),
            "successful": 0,
            "failed": 0,
            "partial": 0,
            "files": {}
        }
        
        logging.info(f"Starting file reconstruction for {len(file_chunks)} files")
        
        with tqdm(total=len(file_chunks), desc="Reconstructing files") as pbar:
            for filename, chunks in file_chunks.items():
                try:
                    # Get expected checksum from manifest if available
                    expected_checksum = None
                    if manifest_data and filename in manifest_data.get("files", {}):
                        expected_checksum = manifest_data["files"][filename].get("checksum")
                    
                    # Verify integrity
                    is_complete, missing_chunks = self.verify_file_integrity(
                        filename, chunks, expected_checksum
                    )
                    
                    if is_complete or self.config.get("allow_partial_reconstruction", False):
                        # Reconstruct file
                        file_content, checksum = self.reconstruct_file(filename, chunks)
                        
                        if file_content is not None:
                            # Create output file path
                            file_path = os.path.join(output_dir, filename.replace('/', os.sep))
                            
                            # Save file
                            if self.save_file(file_path, file_content):
                                status = "complete" if is_complete else "partial"
                                reconstruction_report["files"][filename] = {
                                    "status": status,
                                    "output_path": file_path,
                                    "size": len(file_content),
                                    "checksum": checksum,
                                    "chunks_used": len(chunks),
                                    "missing_chunks": missing_chunks if not is_complete else []
                                }
                                
                                # Verify checksum if available
                                if expected_checksum and checksum != expected_checksum:
                                    logging.warning(f"Checksum mismatch for {filename}")
                                    reconstruction_report["files"][filename]["checksum_match"] = False
                                else:
                                    reconstruction_report["files"][filename]["checksum_match"] = True
                                
                                if is_complete:
                                    reconstruction_report["successful"] += 1
                                else:
                                    reconstruction_report["partial"] += 1
                                    
                                logging.info(f"Reconstructed {filename} ({status})")
                            else:
                                reconstruction_report["files"][filename] = {
                                    "status": "save_failed",
                                    "error": "Failed to save file"
                                }
                                reconstruction_report["failed"] += 1
                        else:
                            reconstruction_report["files"][filename] = {
                                "status": "reconstruction_failed",
                                "error": "Failed to reconstruct file content"
                            }
                            reconstruction_report["failed"] += 1
                    else:
                        reconstruction_report["files"][filename] = {
                            "status": "incomplete",
                            "missing_chunks": missing_chunks,
                            "chunks_available": len(chunks)
                        }
                        reconstruction_report["failed"] += 1
                        
                except Exception as e:
                    logging.error(f"Error processing {filename}: {e}")
                    reconstruction_report["files"][filename] = {
                        "status": "error",
                        "error": str(e)
                    }
                    reconstruction_report["failed"] += 1
                    
                pbar.update(1)
                
        # Save reconstruction report
        report_path = os.path.join(output_dir, "reconstruction_report.json")
        save_json(reconstruction_report, report_path)
        
        logging.info(f"Reconstruction complete:")
        logging.info(f"  Successful: {reconstruction_report['successful']}")
        logging.info(f"  Partial: {reconstruction_report['partial']}")
        logging.info(f"  Failed: {reconstruction_report['failed']}")
        
        return reconstruction_report
    
    def validate_reconstructed_file(self, filepath, expected_checksum):
        """Validate a reconstructed file against expected checksum."""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            actual_checksum = calculate_checksum(content)
            
            if actual_checksum == expected_checksum:
                logging.info(f"File validation passed: {filepath}")
                return True
            else:
                logging.error(f"File validation failed: {filepath}")
                logging.error(f"  Expected: {expected_checksum}")
                logging.error(f"  Actual: {actual_checksum}")
                return False
                
        except Exception as e:
            logging.error(f"Error validating {filepath}: {e}")
            return False
    
    def create_directory_structure(self, output_dir, file_list):
        """Create directory structure for reconstructed files."""
        directories = set()
        
        for filename in file_list:
            directory = os.path.dirname(filename)
            if directory:
                directories.add(directory)
        
        for directory in directories:
            full_path = os.path.join(output_dir, directory.replace('/', os.sep))
            ensure_directory(full_path)
            
        logging.info(f"Created {len(directories)} directories")
