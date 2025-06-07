# Zip-to-QR Code Converter & Reassembler

A high-performance Python project that extracts all files from a zip archive, converts them into sequential QR codes with XML payload wrapping, and provides reassembly capabilities to reconstruct the original files from QR codes.

## Overview

This project processes zip archives (specifically targeting `gpt-2-master.zip`) and converts all contained files into QR codes. Each QR code contains XML-wrapped content with a maximum payload of 2048 characters. The project includes both encoding (zip → QR codes) and decoding (QR codes → reconstructed files) capabilities.

## Features

- **Complete Zip Processing**: Extracts and processes ALL files from zip archives
- **Dual-Mode Operation**: Both encoding and decoding scripts
- **High-Performance Parsing**: Efficient file processing with memory optimization
- **Chunked Conversion**: Automatically splits large files into 2048-character chunks
- **XML Payload Wrapping**: Formats content with custom XML structure
- **Sequential QR Generation**: Creates numbered QR code images (1.png, 2.png, etc.)
- **File Reconstruction**: Reassembles original files from QR code scans
- **Metadata Preservation**: Maintains file structure and properties
- **Integrity Verification**: SHA-256 checksums for file validation
- **Agent Mode Compatible**: Designed for automated processing workflows

## Installation

### 1. Clone or Download
Place the project files in your desired directory (e.g., `c:\qrvid`)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Source File
Ensure your zip file exists at the configured location (default: `C:\huggingface\gpt-2-master.zip`)

## Project Structure

```
qrvid/
├── src/
│   ├── __init__.py
│   ├── zip_processor.py    # Zip extraction and file processing
│   ├── qr_encoder.py       # QR code generation from files
│   ├── qr_decoder.py       # QR code reading and parsing
│   ├── file_assembler.py   # File reconstruction logic
│   ├── xml_wrapper.py      # XML payload formatting
│   └── utils.py            # Helper functions
├── images/                 # Output directory for QR codes (created)
├── output/                 # Reconstructed files directory (created)
├── temp/                   # Temporary extraction directory (created)
├── encode.py              # Main encoding script (zip → QR)
├── decode.py              # Main decoding script (QR → files)
├── requirements.txt       # Python dependencies
├── config.yaml           # Configuration settings
└── README.md             # This file
```

## Usage

### Basic Encoding (Zip → QR Codes)
```bash
# Use default configuration
python encode.py

# Specify custom ZIP file and output directory
python encode.py --input-zip "C:\path\to\your\file.zip" --output-dir "qr_codes"

# Adjust chunk size for smaller QR codes
python encode.py --chunk-size 1800
```

### Basic Decoding (QR Codes → Files)
```bash
# Use default configuration
python decode.py

# Specify custom directories
python decode.py --qr-dir "qr_codes" --output-dir "reconstructed_files"

# Enable integrity verification
python decode.py --verify-integrity

# Allow partial reconstruction of incomplete files
python decode.py --allow-partial --force-reconstruct
```

### Diagnostic Mode
```bash
# Check QR code integrity and missing chunks
python decode.py --diagnose --qr-dir "images"
```

## Configuration

Edit `config.yaml` to customize processing:

```yaml
# Source Configuration
zip_path: "C:\\huggingface\\gpt-2-master.zip"
qr_output_directory: "images"
file_output_directory: "output"

# QR Code Settings
max_chunk_size: 2048
qr_error_correction: "M"  # L, M, Q, H
qr_box_size: 10
qr_border: 4

# Processing Options
preserve_structure: true
calculate_checksums: true
verify_integrity: true
```

## XML Payload Format

Each QR code contains XML-wrapped content:

```xml
<doc page="1" x="@tariusdamon" file="model.py" chunk="1" total="5">base64_encoded_content</doc>
```

**Attributes:**
- `page`: Sequential QR code number
- `x`: Static identifier "@tariusdamon"
- `file`: Original filename with path
- `chunk`: Chunk number within this file
- `total`: Total chunks for this file

## Example Workflow

### Complete Process Example
```bash
# 1. Encode ZIP file to QR codes
python encode.py --input-zip "C:\huggingface\gpt-2-master.zip" --output-dir "qr_output"

# Output will include:
# qr_output/1.png, 2.png, 3.png, ... (QR code images)
# qr_output/manifest.json (metadata)

# 2. Decode QR codes back to files
python decode.py --qr-dir "qr_output" --output-dir "reconstructed"

# Output will include:
# reconstructed/ (directory with all original files)
# reconstructed/reconstruction_report.json (status report)
```

## Advanced Options

### Command Line Arguments

**Encoding (`encode.py`):**
- `--input-zip`: Path to ZIP file
- `--output-dir`: QR codes output directory
- `--chunk-size`: Maximum chunk size (default: 2048)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--agent-mode`: Minimal output for automation
- `--no-cleanup`: Keep temporary files

**Decoding (`decode.py`):**
- `--qr-dir`: Directory with QR codes
- `--output-dir`: Reconstructed files output directory
- `--verify-integrity`: Enable checksum verification
- `--allow-partial`: Reconstruct incomplete files
- `--force-reconstruct`: Force reconstruction despite missing chunks
- `--diagnose`: Run diagnostic mode only

### Logging
```bash
# Enable debug logging with file output
python encode.py --log-level DEBUG --log-file encoding.log

python decode.py --log-level DEBUG --log-file decoding.log
```

## Error Handling

### Common Issues and Solutions

**Issue: "ZIP file not found"**
```bash
# Check if file exists and update config
python encode.py --input-zip "C:\correct\path\to\file.zip"
```

**Issue: "No QR code found in image"**
```bash
# Try alternative QR library or check image quality
python decode.py --qr-library opencv
```

**Issue: "Missing chunks for file"**
```bash
# Use diagnostic mode to identify issues
python decode.py --diagnose --qr-dir "images"

# Force partial reconstruction
python decode.py --allow-partial --force-reconstruct
```

**Issue: "Checksum mismatch"**
```bash
# Skip verification for recovery
python decode.py --skip-verification --force-reconstruct
```

## Performance Notes

- **Memory Usage**: Large ZIP files are processed in chunks to minimize memory usage
- **QR Code Size**: 2048-character limit ensures QR codes remain scannable
- **Processing Speed**: Progress bars show real-time status for long operations
- **File Integrity**: SHA-256 checksums ensure data integrity throughout the process

## Output Files

### Encoding Output
- `{page_number}.png`: Sequential QR code images
- `manifest.json`: Complete file mapping and metadata
- `encoding.log`: Processing log (if enabled)

### Decoding Output
- Reconstructed files in original directory structure
- `reconstruction_report.json`: Detailed reconstruction status
- `decoding.log`: Processing log (if enabled)

## Dependencies

- `qrcode[pil]`: QR code generation
- `opencv-python`: Image processing for QR reading
- `pyzbar`: QR code scanning and decoding
- `Pillow`: Image manipulation
- `PyYAML`: Configuration file parsing
- `tqdm`: Progress bars
- `click`: Command line interface

## Troubleshooting

1. **Installation Issues**: Ensure all dependencies are installed correctly
2. **QR Reading Problems**: Try different QR libraries (pyzbar vs opencv)
3. **Memory Issues**: Reduce chunk size or process smaller files
4. **File Permissions**: Ensure write access to output directories
5. **Path Issues**: Use absolute paths for better reliability

## License

This project is licensed under a **Non-Commercial Use License**. 

### For Non-Commercial Use (FREE):
- ✅ Personal projects
- ✅ Educational use
- ✅ Research purposes
- ✅ Open source projects
- ✅ Small businesses (<$100k annual revenue)

### For Commercial Use (LICENSE REQUIRED):
- 💰 Commercial products or services
- 💰 Large corporations (>$100k annual revenue)
- 💰 Revenue-generating applications
- 💰 Enterprise deployments

**Commercial licensing available** - Contact for pricing and terms.

See the [LICENSE](LICENSE) file for complete terms and conditions.

## Commercial Licensing

If you're a company or organization that wants to use this project commercially, please reach out for licensing terms. Commercial licenses support continued development and maintenance of this project.

**Benefits of commercial licensing:**
- Commercial use rights
- Priority support
- Custom feature development
- Enterprise deployment assistance
- Legal protection and compliance

## Contributing

Feel free to submit issues and enhancement requests. This project is designed to be modular and extensible.

**Contributing Guidelines:**
- All contributions will be licensed under the same terms
- Commercial contributors may be required to sign a CLA
- Please ensure your contributions don't infringe on third-party rights
