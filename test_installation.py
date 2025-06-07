#!/usr/bin/env python3
"""
test_installation.py - Test script to verify installation and dependencies
"""

import sys
import os

def test_dependencies():
    """Test if all required dependencies are available."""
    print("Testing dependencies...")
    
    dependencies = [
        ('qrcode', 'QR code generation'),
        ('PIL', 'Image processing (Pillow)'),
        ('cv2', 'OpenCV for image processing'),
        ('pyzbar', 'QR code scanning'),
        ('numpy', 'Numerical computing'),
        ('tqdm', 'Progress bars'),
        ('yaml', 'YAML configuration parsing')
    ]
    
    failed = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✓ {module}: {description}")
        except ImportError:
            print(f"✗ {module}: {description} - NOT FOUND")
            failed.append(module)
    
    if failed:
        print(f"\nMissing dependencies: {', '.join(failed)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("\nAll dependencies are available!")
        return True

def test_src_modules():
    """Test if src modules can be imported."""
    print("\nTesting src modules...")
    
    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    modules = [
        ('src.utils', 'Utility functions'),
        ('src.xml_wrapper', 'XML payload wrapper'),
        ('src.zip_processor', 'ZIP file processor'),
        ('src.qr_encoder', 'QR code encoder'),
        ('src.qr_decoder', 'QR code decoder'),
        ('src.file_assembler', 'File assembler')
    ]
    
    failed = []
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"✓ {module}: {description}")
        except ImportError as e:
            print(f"✗ {module}: {description} - FAILED ({e})")
            failed.append(module)
    
    if failed:
        print(f"\nFailed to import: {', '.join(failed)}")
        return False
    else:
        print("\nAll src modules imported successfully!")
        return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from src.utils import load_config
        config = load_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  Chunk size: {config.get('max_chunk_size')}")
        print(f"  QR output dir: {config.get('qr_output_directory')}")
        print(f"  Default ZIP path: {config.get('zip_path')}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without actual files."""
    print("\nTesting basic functionality...")
    
    try:
        from src.xml_wrapper import XMLWrapper
        from src.utils import get_default_config
        
        config = get_default_config()
        xml_wrapper = XMLWrapper(config)
        
        # Test XML creation
        xml_content = xml_wrapper.create_xml_payload(
            content="test_content",
            page_num=1,
            filename="test.txt",
            chunk_id=1,
            total_chunks=1
        )
        
        if xml_content:
            print("✓ XML payload creation works")
            
            # Test XML parsing
            parsed = xml_wrapper.parse_xml_payload(xml_content)
            if parsed and parsed.get('content') == 'test_content':
                print("✓ XML payload parsing works")
                return True
            else:
                print("✗ XML payload parsing failed")
                return False
        else:
            print("✗ XML payload creation failed")
            return False
            
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("QR Video Project Installation Test")
    print("=" * 40)
    
    tests = [
        test_dependencies,
        test_src_modules,
        test_config,
        test_basic_functionality
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✓ Installation test PASSED - Project is ready to use!")
        print("\nNext steps:")
        print("1. Ensure your ZIP file exists at the configured path")
        print("2. Run: python encode.py --help")
        print("3. Run: python decode.py --help")
        return True
    else:
        print("✗ Installation test FAILED - Please fix the issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
