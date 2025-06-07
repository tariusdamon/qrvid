#!/usr/bin/env python3
"""
complete_workflow.py - Demonstrate complete ZIP → QR → Video → QR → ZIP workflow

This script demonstrates the complete round-trip process:
1. ZIP file → QR code images
2. QR code images → MP4 video  
3. MP4 video → QR code images
4. QR code images → ZIP file
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def check_file_exists(filepath, description):
    """Check if file exists and print status."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✓ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"✗ {description}: {filepath} - NOT FOUND")
        return False


def main():
    parser = argparse.ArgumentParser(description="Complete workflow demonstration")
    parser.add_argument("input_zip", help="Input ZIP file")
    parser.add_argument("--work-dir", default="workflow_test", 
                       help="Working directory for intermediate files")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up intermediate files after completion")
    parser.add_argument("--skip-video", action="store_true",
                       help="Skip video creation/extraction steps")
    
    args = parser.parse_args()
    
    # Setup paths
    work_dir = Path(args.work_dir)
    qr_dir1 = work_dir / "qr_images_1"
    video_file = work_dir / "qr_codes.mp4"
    qr_dir2 = work_dir / "qr_images_2"
    output_zip = work_dir / "reconstructed.zip"
    
    # Create working directory
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("QR Video Complete Workflow Test")
    print("=" * 60)
    print(f"Input ZIP: {args.input_zip}")
    print(f"Working directory: {work_dir}")
    
    # Step 1: Check input file
    if not check_file_exists(args.input_zip, "Input ZIP file"):
        return 1
    
    # Step 2: ZIP → QR codes
    if not run_command([
        sys.executable, "encode_direct.py",
        "--input-zip", args.input_zip,
        "--output-dir", str(qr_dir1)
    ], "Convert ZIP to QR codes"):
        return 1
    
    # Check QR codes were created
    qr_files = list(qr_dir1.glob("*.png"))
    if not qr_files:
        print("✗ No QR code images found")
        return 1
    print(f"✓ Created {len(qr_files)} QR code images")
    
    if not args.skip_video:
        # Step 3: QR codes → Video
        if not run_command([
            sys.executable, "quick_video.py",
            str(qr_dir1), str(video_file)
        ], "Convert QR codes to video"):
            return 1
        
        if not check_file_exists(video_file, "Video file"):
            return 1
        
        # Step 4: Video → QR codes
        if not run_command([
            sys.executable, "video_to_qr.py",
            str(video_file), str(qr_dir2)
        ], "Extract QR codes from video"):
            return 1
        
        # Check extracted QR codes
        extracted_qr_files = list(qr_dir2.glob("*.png"))
        if not extracted_qr_files:
            print("✗ No QR codes extracted from video")
            return 1
        print(f"✓ Extracted {len(extracted_qr_files)} QR codes from video")
        
        # Use extracted QR codes for final step
        final_qr_dir = qr_dir2
    else:
        # Skip video steps, use original QR codes
        final_qr_dir = qr_dir1
    
    # Step 5: QR codes → ZIP
    if not run_command([
        sys.executable, "decode_direct.py",
        "--qr-dir", str(final_qr_dir),
        "--output-dir", str(work_dir)
    ], "Convert QR codes back to ZIP"):
        return 1
    
    # Find the reconstructed file
    reconstructed_files = list(work_dir.glob("*.zip"))
    if not reconstructed_files:
        print("✗ No reconstructed ZIP file found")
        return 1
    
    reconstructed_zip = reconstructed_files[0]
    if not check_file_exists(reconstructed_zip, "Reconstructed ZIP"):
        return 1
    
    # Step 6: Verify integrity
    print(f"\n{'='*60}")
    print("Verification")
    print(f"{'='*60}")
    
    original_size = os.path.getsize(args.input_zip)
    reconstructed_size = os.path.getsize(reconstructed_zip)
    
    print(f"Original file: {args.input_zip} ({original_size:,} bytes)")
    print(f"Reconstructed: {reconstructed_zip} ({reconstructed_size:,} bytes)")
    
    if original_size == reconstructed_size:
        print("✓ File sizes match!")
        
        # Compare checksums
        import hashlib
        
        with open(args.input_zip, 'rb') as f:
            original_hash = hashlib.sha256(f.read()).hexdigest()
        
        with open(reconstructed_zip, 'rb') as f:
            reconstructed_hash = hashlib.sha256(f.read()).hexdigest()
        
        print(f"Original SHA256: {original_hash}")
        print(f"Reconstructed:  {reconstructed_hash}")
        
        if original_hash == reconstructed_hash:
            print("✓ PERFECT MATCH! Workflow completed successfully!")
            success = True
        else:
            print("✗ Checksum mismatch - data corruption detected")
            success = False
    else:
        print("✗ File size mismatch")
        success = False
    
    # Cleanup if requested
    if args.cleanup and success:
        import shutil
        print(f"\nCleaning up working directory: {work_dir}")
        shutil.rmtree(work_dir)
    
    # Summary
    print(f"\n{'='*60}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*60}")
    
    if not args.skip_video:
        print("Complete workflow: ZIP → QR → Video → QR → ZIP")
        steps = 5
    else:
        print("Direct workflow: ZIP → QR → ZIP")
        steps = 3
    
    if success:
        print(f"✓ ALL {steps} STEPS COMPLETED SUCCESSFULLY!")
        print("The QR code workflow is fully functional.")
        return 0
    else:
        print(f"✗ WORKFLOW FAILED")
        print("Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
