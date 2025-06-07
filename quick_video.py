#!/usr/bin/env python3
"""
quick_video.py - Quick QR codes to video converter (simplified version)
"""

import os
import cv2
import numpy as np
from tqdm import tqdm


def create_qr_video(qr_dir="images_direct", output_file="qr_video.mp4", 
                   duration_per_qr=2.0, fps=30, resolution=(1280, 720)):
    """Create video from QR codes with minimal dependencies."""
    
    # Get QR files
    if not os.path.exists(qr_dir):
        print(f"Error: Directory {qr_dir} not found")
        return False
    
    qr_files = [f for f in os.listdir(qr_dir) if f.endswith('.png')]
    qr_files.sort(key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0)
    
    if not qr_files:
        print("Error: No PNG files found")
        return False
    
    print(f"Found {len(qr_files)} QR code images")
    
    # Calculate frames
    frames_per_qr = int(duration_per_qr * fps)
    total_frames = len(qr_files) * frames_per_qr
    
    print(f"Creating video: {duration_per_qr}s per QR, {fps}fps, {resolution[0]}x{resolution[1]}")
    print(f"Total duration: {len(qr_files) * duration_per_qr:.1f} seconds")
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, resolution)
    
    if not out.isOpened():
        print("Error: Failed to create video writer")
        return False
    
    try:
        with tqdm(total=total_frames, desc="Creating video") as pbar:
            for i, qr_file in enumerate(qr_files):
                # Load image
                img_path = os.path.join(qr_dir, qr_file)
                img = cv2.imread(img_path)
                
                if img is None:
                    print(f"Warning: Could not load {qr_file}")
                    continue
                
                # Resize image to fit resolution while maintaining aspect ratio
                h, w = img.shape[:2]
                target_w, target_h = resolution
                
                # Calculate scale to fit
                scale = min(target_w / w, target_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                # Resize
                resized = cv2.resize(img, (new_w, new_h))
                
                # Create white canvas and center image
                canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
                start_y = (target_h - new_h) // 2
                start_x = (target_w - new_w) // 2
                canvas[start_y:start_y+new_h, start_x:start_x+new_w] = resized
                
                # Add frame counter
                text = f"QR {i+1}/{len(qr_files)}"
                cv2.putText(canvas, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                
                # Write frames
                for _ in range(frames_per_qr):
                    out.write(canvas)
                    pbar.update(1)
        
        out.release()
        
        # Show result
        video_size = os.path.getsize(output_file)
        print(f"\nVideo created successfully!")
        print(f"File: {output_file}")
        print(f"Size: {video_size / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"Error creating video: {e}")
        out.release()
        return False


if __name__ == "__main__":
    import sys
    
    # Parse simple command line args
    qr_dir = sys.argv[1] if len(sys.argv) > 1 else "images_direct"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "qr_video.mp4"
    
    success = create_qr_video(qr_dir, output_file)
    sys.exit(0 if success else 1)
