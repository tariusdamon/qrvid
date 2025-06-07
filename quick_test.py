#!/usr/bin/env python3
"""
quick_test.py - Quick test script for basic functionality
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_zip():
    """Create a small test ZIP file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        with zipfile.ZipFile(tmp.name, 'w') as zf:
            # Add some test files
            zf.writestr('test1.txt', 'Hello, this is test file 1!')
            zf.writestr('test2.txt', 'This is test file 2 with more content.')
            zf.writestr('folder/test3.txt', 'File in subfolder.')
        return tmp.name

def test_encode_decode_cycle():
    """Test complete encode/decode cycle with a small test file."""
    print("Running quick encode/decode test...")
    
    # Create test ZIP
    test_zip = create_test_zip()
    test_qr_dir = tempfile.mkdtemp(prefix='qr_test_')
    test_output_dir = tempfile.mkdtemp(prefix='output_test_')
    
    try:
        from src.utils import get_default_config
        from src.zip_processor import ZipProcessor
        from src.qr_encoder import QREncoder
        from src.qr_decoder import QRDecoder
        from src.file_assembler import FileAssembler
        
        # Setup config
        config = get_default_config()
        config['max_chunk_size'] = 1024  # Smaller for testing
        config['cleanup_temp'] = False
        
        print(f"Test ZIP: {test_zip}")
        print(f"QR output: {test_qr_dir}")
        print(f"File output: {test_output_dir}")
        
        # Test encoding
        print("\n1. Testing ZIP processing...")
        zip_processor = ZipProcessor(config)
        extracted_files = zip_processor.extract_zip(test_zip)
        
        if not extracted_files:
            print("✗ ZIP processing failed")
            return False
        
        print(f"✓ Extracted {len(extracted_files)} files")
        
        print("\n2. Testing QR encoding...")
        qr_encoder = QREncoder(config)
        manifest, qr_files = qr_encoder.encode_all_files(extracted_files, test_qr_dir)
        
        if not qr_files:
            print("✗ QR encoding failed")
            return False
            
        print(f"✓ Generated {len(qr_files)} QR codes")
        
        print("\n3. Testing QR decoding...")
        qr_decoder = QRDecoder(config)
        if not qr_decoder.scan_all_qr_codes(test_qr_dir):
            print("✗ QR scanning failed")
            return False
            
        print(f"✓ Scanned QR codes successfully")
        
        print("\n4. Testing file reconstruction...")
        file_assembler = FileAssembler(config)
        file_chunks = dict(qr_decoder.file_chunks)
        report = file_assembler.save_reconstructed_files(file_chunks, test_output_dir, manifest)
        
        if report['successful'] == 0:
            print("✗ File reconstruction failed")
            return False
            
        print(f"✓ Reconstructed {report['successful']} files")
        
        # Verify files exist
        reconstructed_files = []
        for root, dirs, files in os.walk(test_output_dir):
            for file in files:
                if not file.endswith('.json'):  # Skip report files
                    reconstructed_files.append(os.path.join(root, file))
        
        print(f"✓ Found {len(reconstructed_files)} reconstructed files")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            os.unlink(test_zip)
            import shutil
            shutil.rmtree(test_qr_dir, ignore_errors=True)
            shutil.rmtree(test_output_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    success = test_encode_decode_cycle()
    if success:
        print("\n✓ Quick test PASSED - Basic functionality works!")
    else:
        print("\n✗ Quick test FAILED - Check errors above")
    sys.exit(0 if success else 1)
