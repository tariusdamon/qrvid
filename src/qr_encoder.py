"""
QR code encoder for converting file content to QR codes.
"""
import qrcode
import base64
import os
import logging
from pathlib import Path
from tqdm import tqdm
from .xml_wrapper import XMLWrapper
from .utils import ensure_directory, calculate_checksum


class QREncoder:
    def __init__(self, config):
        self.config = config
        self.xml_wrapper = XMLWrapper(config)
        self.qr_counter = 1
        
    def generate_qr_code(self, data, filename):
        """Generate QR code from data."""
        try:
            qr = qrcode.QRCode(
                version=self.config.get("qr_version"),  # Auto-detect if None
                error_correction=self._get_error_correction(),
                box_size=self.config.get("qr_box_size", 10),
                border=self.config.get("qr_border", 4),
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filename)
            logging.debug(f"Generated QR code: {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Error generating QR code {filename}: {e}")
            return False
    
    def _get_error_correction(self):
        """Get error correction level from config."""
        level = self.config.get("qr_error_correction", "M")
        error_levels = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H
        }
        return error_levels.get(level, qrcode.constants.ERROR_CORRECT_M)
    
    def chunk_file_content(self, content, filename):
        """Split file content into optimal chunks."""
        # Convert to base64 for binary safety
        if isinstance(content, str):
            content = content.encode('utf-8')
        b64_content = base64.b64encode(content).decode('ascii')
        
        chunks = []
        # Calculate max content size per chunk (accounting for XML wrapper overhead)
        xml_overhead = len(self.xml_wrapper.template.format(
            page_num="999", 
            filename=filename, 
            chunk_id="999", 
            total_chunks="999", 
            content=""
        ))
        max_content_per_chunk = self.config.get("max_chunk_size", 2048) - xml_overhead
        
        if max_content_per_chunk <= 0:
            logging.error(f"XML overhead ({xml_overhead}) exceeds chunk size")
            return []
        
        # Split content into chunks
        for i in range(0, len(b64_content), max_content_per_chunk):
            chunk = b64_content[i:i + max_content_per_chunk]
            chunks.append(chunk)
            
        logging.debug(f"Split {filename} into {len(chunks)} chunks")
        return chunks
    
    def encode_file_to_qr_codes(self, file_info, output_dir):
        """Encode a single file to QR codes."""
        filename = file_info["path"]
        content = file_info["content"]
        
        logging.info(f"Encoding {filename} ({len(content)} bytes)")
        
        # Chunk the content
        chunks = self.chunk_file_content(content, filename)
        if not chunks:
            logging.error(f"Failed to chunk file: {filename}")
            return []
        
        total_chunks = len(chunks)
        qr_files = []
        
        # Generate QR codes for each chunk
        for chunk_id, chunk in enumerate(chunks, 1):
            # Create XML payload
            xml_payload = self.xml_wrapper.create_xml_payload(
                content=chunk,
                page_num=self.qr_counter,
                filename=filename,
                chunk_id=chunk_id,
                total_chunks=total_chunks
            )
            
            if xml_payload is None:
                logging.error(f"Failed to create XML payload for {filename} chunk {chunk_id}")
                continue
            
            # Generate QR code
            qr_filename = os.path.join(output_dir, f"{self.qr_counter}.png")
            if self.generate_qr_code(xml_payload, qr_filename):
                qr_files.append({
                    "qr_file": qr_filename,
                    "page_num": self.qr_counter,
                    "chunk_id": chunk_id,
                    "total_chunks": total_chunks,
                    "filename": filename
                })
                self.qr_counter += 1
            else:
                logging.error(f"Failed to generate QR code for {filename} chunk {chunk_id}")
        
        logging.info(f"Generated {len(qr_files)} QR codes for {filename}")
        return qr_files
    
    def encode_all_files(self, extracted_files, output_dir):
        """Encode all extracted files to QR codes."""
        ensure_directory(output_dir)
        
        all_qr_files = []
        manifest = {
            "total_qr_codes": 0,
            "files": {},
            "creation_timestamp": "",
            "source_zip": "",
            "chunk_size": self.config.get("max_chunk_size", 2048)
        }
        
        # Import datetime here to set timestamp
        from datetime import datetime
        manifest["creation_timestamp"] = datetime.now().isoformat()
        
        logging.info(f"Starting QR code generation for {len(extracted_files)} files")
        
        with tqdm(total=len(extracted_files), desc="Encoding files to QR") as pbar:
            for file_path, file_info in extracted_files.items():
                try:
                    # Create file info structure
                    file_data = {
                        "path": file_path,
                        "content": file_info["content"],
                        "size": file_info["size"],
                        "checksum": file_info.get("checksum")
                    }
                    
                    # Encode file to QR codes
                    qr_files = self.encode_file_to_qr_codes(file_data, output_dir)
                    
                    if qr_files:
                        all_qr_files.extend(qr_files)
                        
                        # Add to manifest
                        manifest["files"][file_path] = {
                            "original_size": file_info["size"],
                            "checksum": file_info.get("checksum"),
                            "chunks": len(qr_files),
                            "qr_codes": [qr["page_num"] for qr in qr_files]
                        }
                    
                except Exception as e:
                    logging.error(f"Error encoding {file_path}: {e}")
                
                pbar.update(1)
        
        # Update manifest totals
        manifest["total_qr_codes"] = self.qr_counter - 1
        
        # Save manifest
        from .utils import save_json
        manifest_path = os.path.join(output_dir, "manifest.json")
        save_json(manifest, manifest_path)
        
        logging.info(f"QR encoding complete! Generated {manifest['total_qr_codes']} QR codes")
        return manifest, all_qr_files
