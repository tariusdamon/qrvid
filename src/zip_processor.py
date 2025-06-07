"""
ZIP file processor for extracting and handling zip contents.
"""
import zipfile
import os
import logging
from pathlib import Path
from tqdm import tqdm
from .utils import calculate_checksum, ensure_directory


class ZipProcessor:
    def __init__(self, config):
        self.config = config
        self.extracted_files = {}
        
    def extract_zip(self, zip_path, extract_to=None):
        """Extract ZIP file and return file information."""
        if extract_to is None:
            extract_to = self.config.get("temp_directory", "temp")
        
        ensure_directory(extract_to)
        
        logging.info(f"Extracting ZIP file: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Filter files if needed
                if not self.config.get("include_hidden_files", False):
                    file_list = [f for f in file_list if not any(part.startswith('.') for part in f.split('/'))]
                
                logging.info(f"Found {len(file_list)} files in ZIP")
                
                with tqdm(total=len(file_list), desc="Extracting files") as pbar:
                    for file_path in file_list:
                        # Skip directories
                        if file_path.endswith('/'):
                            pbar.update(1)
                            continue
                        
                        try:
                            # Extract file
                            zip_ref.extract(file_path, extract_to)
                            
                            # Get full path
                            full_path = os.path.join(extract_to, file_path)
                            
                            # Read file content and calculate checksum
                            with open(full_path, 'rb') as f:
                                content = f.read()
                            
                            checksum = calculate_checksum(content) if self.config.get("calculate_checksums", True) else None
                            
                            # Store file info
                            self.extracted_files[file_path] = {
                                "full_path": full_path,
                                "size": len(content),
                                "checksum": checksum,
                                "content": content
                            }
                            
                            logging.debug(f"Extracted: {file_path} ({len(content)} bytes)")
                            
                        except Exception as e:
                            logging.error(f"Error extracting {file_path}: {e}")
                        
                        pbar.update(1)
                
                logging.info(f"Successfully extracted {len(self.extracted_files)} files")
                return self.extracted_files
                
        except zipfile.BadZipFile:
            logging.error(f"Invalid ZIP file: {zip_path}")
            raise
        except FileNotFoundError:
            logging.error(f"ZIP file not found: {zip_path}")
            raise
        except Exception as e:
            logging.error(f"Error processing ZIP file: {e}")
            raise
    
    def get_file_content(self, zip_path, file_path):
        """Get content of a specific file from ZIP without extracting all."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                with zip_ref.open(file_path) as file:
                    return file.read()
        except Exception as e:
            logging.error(f"Error reading {file_path} from ZIP: {e}")
            return None
    
    def list_zip_contents(self, zip_path):
        """List contents of ZIP file without extracting."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Filter out directories and hidden files if needed
                files = []
                for file_path in file_list:
                    if not file_path.endswith('/'):
                        if self.config.get("include_hidden_files", False) or not any(part.startswith('.') for part in file_path.split('/')):
                            info = zip_ref.getinfo(file_path)
                            files.append({
                                "path": file_path,
                                "size": info.file_size,
                                "compressed_size": info.compress_size,
                                "date_time": info.date_time
                            })
                
                return files
                
        except Exception as e:
            logging.error(f"Error listing ZIP contents: {e}")
            return []
    
    def cleanup_temp_files(self, temp_dir=None):
        """Clean up temporary extracted files."""
        if temp_dir is None:
            temp_dir = self.config.get("temp_directory", "temp")
        
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logging.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logging.warning(f"Error cleaning up temp directory: {e}")
    
    def validate_zip_file(self, zip_path):
        """Validate ZIP file integrity."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                bad_file = zip_ref.testzip()
                if bad_file:
                    logging.error(f"Corrupted file in ZIP: {bad_file}")
                    return False
                logging.info("ZIP file validation passed")
                return True
        except Exception as e:
            logging.error(f"ZIP validation failed: {e}")
            return False
