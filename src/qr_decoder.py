"""
QR code decoder for reading QR codes and extracting content.
"""
import cv2
import os
import logging
from pyzbar import pyzbar
from tqdm import tqdm
from collections import defaultdict
from .xml_wrapper import XMLWrapper


class QRDecoder:
    def __init__(self, config):
        self.config = config
        self.xml_wrapper = XMLWrapper(config)
        self.scanned_data = {}
        self.file_chunks = defaultdict(dict)
        
    def scan_qr_code(self, image_path):
        """Scan and decode QR code from image."""
        try:
            # Try with OpenCV first
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Could not read image: {image_path}")
                return None
                
            # Decode QR codes using pyzbar
            qr_codes = pyzbar.decode(image)
            
            if not qr_codes:
                # Try with different preprocessing
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                qr_codes = pyzbar.decode(gray)
                
                if not qr_codes:
                    logging.warning(f"No QR code found in {image_path}")
                    return None
                
            # Return the first QR code data
            qr_data = qr_codes[0].data.decode('utf-8')
            logging.debug(f"Scanned QR code from {image_path}")
            return qr_data
            
        except Exception as e:
            logging.error(f"Error scanning {image_path}: {e}")
            return None
    
    def scan_qr_code_alternative(self, image_path):
        """Alternative QR scanning using different methods."""
        try:
            # Use PIL for reading image
            from PIL import Image
            
            pil_image = Image.open(image_path)
            qr_codes = pyzbar.decode(pil_image)
            
            if qr_codes:
                return qr_codes[0].data.decode('utf-8')
            else:
                logging.warning(f"No QR code found in {image_path} (PIL method)")
                return None
                
        except Exception as e:
            logging.error(f"Error with alternative scanning of {image_path}: {e}")
            return None
    
    def scan_all_qr_codes(self, qr_dir):
        """Scan all QR codes in directory."""
        if not os.path.exists(qr_dir):
            logging.error(f"QR directory not found: {qr_dir}")
            return False
        
        # Get all PNG files and sort numerically
        qr_files = [f for f in os.listdir(qr_dir) if f.endswith('.png')]
        try:
            qr_files.sort(key=lambda x: int(x.split('.')[0]))
        except ValueError:
            qr_files.sort()  # Fallback to alphabetical sort
        
        logging.info(f"Found {len(qr_files)} QR code files")
        
        successful_scans = 0
        with tqdm(total=len(qr_files), desc="Scanning QR codes") as pbar:
            for qr_file in qr_files:
                qr_path = os.path.join(qr_dir, qr_file)
                
                # Scan QR code
                xml_data = self.scan_qr_code(qr_path)
                
                # Try alternative method if first fails
                if xml_data is None:
                    xml_data = self.scan_qr_code_alternative(qr_path)
                
                if xml_data:
                    # Parse XML
                    parsed_data = self.xml_wrapper.parse_xml_payload(xml_data)
                    if parsed_data:
                        page_num = parsed_data["page"]
                        self.scanned_data[page_num] = parsed_data
                        
                        # Organize by file
                        filename = parsed_data["file"]
                        chunk_id = parsed_data["chunk"]
                        self.file_chunks[filename][chunk_id] = parsed_data
                        
                        successful_scans += 1
                        logging.debug(f"Processed QR {qr_file}: {filename} chunk {chunk_id}")
                    else:
                        logging.error(f"Failed to parse XML from {qr_file}")
                else:
                    logging.error(f"Failed to scan QR code: {qr_file}")
                
                pbar.update(1)
                
        logging.info(f"Successfully scanned {successful_scans}/{len(qr_files)} QR codes")
        return successful_scans > 0
    
    def get_scan_statistics(self):
        """Get statistics about scanned data."""
        stats = {
            "total_qr_codes": len(self.scanned_data),
            "total_files": len(self.file_chunks),
            "files": {}
        }
        
        for filename, chunks in self.file_chunks.items():
            total_chunks = max(chunk["total"] for chunk in chunks.values()) if chunks else 0
            stats["files"][filename] = {
                "chunks_found": len(chunks),
                "total_chunks": total_chunks,
                "complete": len(chunks) == total_chunks,
                "missing_chunks": [i for i in range(1, total_chunks + 1) if i not in chunks]
            }
        
        return stats
    
    def verify_scan_integrity(self):
        """Verify integrity of scanned data."""
        stats = self.get_scan_statistics()
        
        incomplete_files = []
        for filename, file_stats in stats["files"].items():
            if not file_stats["complete"]:
                incomplete_files.append({
                    "filename": filename,
                    "missing_chunks": file_stats["missing_chunks"],
                    "found": file_stats["chunks_found"],
                    "total": file_stats["total_chunks"]
                })
        
        if incomplete_files:
            logging.warning(f"Found {len(incomplete_files)} incomplete files")
            for file_info in incomplete_files:
                logging.warning(f"  {file_info['filename']}: {file_info['found']}/{file_info['total']} chunks")
        else:
            logging.info("All files have complete chunks")
        
        return len(incomplete_files) == 0, incomplete_files
    
    def get_file_chunks(self, filename):
        """Get all chunks for a specific file."""
        return self.file_chunks.get(filename, {})
    
    def get_all_files(self):
        """Get list of all files found in QR codes."""
        return list(self.file_chunks.keys())
    
    def clear_scanned_data(self):
        """Clear all scanned data."""
        self.scanned_data.clear()
        self.file_chunks.clear()
        logging.info("Cleared all scanned data")
