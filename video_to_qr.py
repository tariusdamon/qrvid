#!/usr/bin/env python3
"""
video_to_qr.py - Extract QR codes from video back to images

This script takes a video file containing QR codes and extracts them back
to individual PNG images for decoding.
"""

import cv2
import os
import argparse
import logging
from pathlib import Path
from tqdm import tqdm


def extract_qr_from_video(video_path, output_dir, frame_interval=None, quality_threshold=0.8):
    """Extract QR codes from video to individual images."""
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Could not open video: {video_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    logging.info(f"Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s")
    
    # Calculate frame interval if not provided
    if frame_interval is None:
        # Assume each QR is shown for 2 seconds, extract from middle of each segment
        frame_interval = int(fps * 2)  # Every 2 seconds
    
    extracted_images = []
    qr_counter = 1
    
    with tqdm(total=total_frames // frame_interval, desc="Extracting QR codes") as pbar:
        frame_num = frame_interval // 2  # Start from middle of first segment
        
        while frame_num < total_frames:
            # Seek to specific frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Check if frame contains QR code (basic quality check)
            if is_good_qr_frame(frame, quality_threshold):
                # Save frame as QR image
                output_filename = os.path.join(output_dir, f"{qr_counter}.png")
                cv2.imwrite(output_filename, frame)
                extracted_images.append(output_filename)
                
                logging.debug(f"Extracted QR {qr_counter} from frame {frame_num}")
                qr_counter += 1
            
            frame_num += frame_interval
            pbar.update(1)
    
    cap.release()
    
    logging.info(f"Extracted {len(extracted_images)} QR code images")
    return extracted_images


def is_good_qr_frame(frame, threshold=0.8):
    """Basic quality check for QR code frames."""
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Check for high contrast (QR codes have strong black/white patterns)
    mean_val = cv2.mean(gray)[0]
    
    # Calculate standard deviation as measure of contrast
    _, thresh = cv2.threshold(gray, mean_val, 255, cv2.THRESH_BINARY)
    white_pixels = cv2.countNonZero(thresh)
    total_pixels = gray.shape[0] * gray.shape[1]
    contrast_ratio = min(white_pixels, total_pixels - white_pixels) / total_pixels
    
    # Good QR frames should have reasonable contrast
    return contrast_ratio > (1 - threshold) / 2


def extract_with_scene_detection(video_path, output_dir):
    """Extract QR codes using scene change detection."""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    prev_frame = None
    qr_counter = 1
    extracted_images = []
    scene_threshold = 10000  # Adjust based on video
    
    with tqdm(total=total_frames, desc="Scene detection") as pbar:
        for frame_num in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, frame)
                diff_score = cv2.sumElems(diff)[0]
                
                # If significant change detected, save previous frame
                if diff_score > scene_threshold:
                    output_filename = os.path.join(output_dir, f"{qr_counter}.png")
                    cv2.imwrite(output_filename, prev_frame)
                    extracted_images.append(output_filename)
                    qr_counter += 1
            
            prev_frame = frame.copy()
            pbar.update(1)
    
    # Save last frame
    if prev_frame is not None:
        output_filename = os.path.join(output_dir, f"{qr_counter}.png")
        cv2.imwrite(output_filename, prev_frame)
        extracted_images.append(output_filename)
    
    cap.release()
    logging.info(f"Extracted {len(extracted_images)} QR codes using scene detection")
    return extracted_images


def main():
    parser = argparse.ArgumentParser(description="Extract QR codes from video")
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument("output_dir", help="Output directory for QR images")
    parser.add_argument("--fps", type=float, help="Original video FPS for timing")
    parser.add_argument("--qr-duration", type=float, default=2.0, 
                       help="Duration each QR is shown (seconds)")
    parser.add_argument("--scene-detection", action="store_true",
                       help="Use scene change detection instead of timing")
    parser.add_argument("--quality-threshold", type=float, default=0.8,
                       help="Quality threshold for QR detection (0-1)")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        return 1
    
    print(f"Extracting QR codes from: {args.video_path}")
    print(f"Output directory: {args.output_dir}")
    
    try:
        if args.scene_detection:
            extracted = extract_with_scene_detection(args.video_path, args.output_dir)
        else:
            # Calculate frame interval
            cap = cv2.VideoCapture(args.video_path)
            fps = args.fps or cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
            frame_interval = int(fps * args.qr_duration)
            extracted = extract_qr_from_video(
                args.video_path, 
                args.output_dir, 
                frame_interval,
                args.quality_threshold
            )
        
        if extracted:
            print(f"\nExtraction complete!")
            print(f"Extracted {len(extracted)} QR code images")
            print(f"Images saved in: {args.output_dir}")
            return 0
        else:
            print("Extraction failed")
            return 1
            
    except Exception as e:
        print(f"Error during extraction: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
