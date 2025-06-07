#!/usr/bin/env python3
"""
qr_to_video.py - Convert QR code images to MP4 video

This script takes a directory of QR code images (1.png, 2.png, etc.) 
and creates an MP4 video where each frame shows a QR code for a specified duration.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import setup_logging, load_json


class QRToVideoConverter:
    def __init__(self, config=None):
        self.config = config or {}
        
    def get_qr_files(self, qr_dir):
        """Get sorted list of QR code files."""
        if not os.path.exists(qr_dir):
            logging.error(f"QR directory not found: {qr_dir}")
            return []
        
        # Get all PNG files and sort numerically
        qr_files = [f for f in os.listdir(qr_dir) if f.endswith('.png')]
        
        # Try to sort numerically by extracting number from filename
        try:
            qr_files.sort(key=lambda x: int(x.split('.')[0]))
        except ValueError:
            # Fallback to alphabetical sort
            qr_files.sort()
            logging.warning("Could not sort files numerically, using alphabetical order")
        
        full_paths = [os.path.join(qr_dir, f) for f in qr_files]
        logging.info(f"Found {len(full_paths)} QR code images")
        return full_paths
    
    def load_and_resize_image(self, image_path, target_size):
        """Load image and resize to target size."""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                logging.error(f"Could not load image: {image_path}")
                return None
            
            # Resize image while maintaining aspect ratio
            h, w = img.shape[:2]
            target_w, target_h = target_size
            
            # Calculate scaling factor to fit within target size
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Resize image
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Create canvas with target size and center the image
            canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255  # White background
            
            # Calculate position to center the image
            start_y = (target_h - new_h) // 2
            start_x = (target_w - new_w) // 2
            
            # Place resized image on canvas
            canvas[start_y:start_y+new_h, start_x:start_x+new_w] = resized
            
            return canvas
            
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}")
            return None
    
    def add_text_overlay(self, img, text, position='top'):
        """Add text overlay to image."""
        try:
            h, w = img.shape[:2]
            
            # Text properties
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            color = (0, 0, 0)  # Black text
            thickness = 2
            
            # Get text size
            (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Calculate position
            if position == 'top':
                x = (w - text_w) // 2
                y = text_h + 20
            elif position == 'bottom':
                x = (w - text_w) // 2
                y = h - 20
            else:
                x, y = position
            
            # Add white background for text
            cv2.rectangle(img, (x-5, y-text_h-5), (x+text_w+5, y+baseline+5), (255, 255, 255), -1)
            
            # Add text
            cv2.putText(img, text, (x, y), font, font_scale, color, thickness)
            
            return img
            
        except Exception as e:
            logging.error(f"Error adding text overlay: {e}")
            return img
    
    def create_video(self, qr_dir, output_video, frame_duration=2.0, resolution=(1920, 1080), 
                    fps=30, add_frame_numbers=True, add_metadata=True):
        """Create MP4 video from QR codes."""
        
        # Get QR code files
        qr_files = self.get_qr_files(qr_dir)
        if not qr_files:
            logging.error("No QR code files found")
            return False
        
        # Load manifest if available for metadata
        manifest_path = os.path.join(qr_dir, "manifest.json")
        manifest = load_json(manifest_path) if os.path.exists(manifest_path) else None
        
        # Calculate frames per QR code
        frames_per_qr = int(frame_duration * fps)
        total_frames = len(qr_files) * frames_per_qr
        
        logging.info(f"Creating video with {len(qr_files)} QR codes")
        logging.info(f"Frame duration: {frame_duration}s ({frames_per_qr} frames per QR)")
        logging.info(f"Total video length: {len(qr_files) * frame_duration:.1f}s ({total_frames} frames)")
        logging.info(f"Resolution: {resolution[0]}x{resolution[1]} @ {fps}fps")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, resolution)
        
        if not out.isOpened():
            logging.error("Failed to initialize video writer")
            return False
        
        try:
            with tqdm(total=total_frames, desc="Creating video") as pbar:
                for qr_idx, qr_file in enumerate(qr_files, 1):
                    # Load and resize QR code image
                    img = self.load_and_resize_image(qr_file, resolution)
                    if img is None:
                        logging.warning(f"Skipping {qr_file} - could not load")
                        continue
                    
                    # Add overlays if requested
                    if add_frame_numbers:
                        frame_text = f"QR Code {qr_idx}/{len(qr_files)}"
                        img = self.add_text_overlay(img, frame_text, 'top')
                    
                    if add_metadata and manifest:
                        # Add metadata from manifest
                        metadata_text = f"Files: {len(manifest.get('files', {}))}"
                        if 'source_zip' in manifest:
                            zip_name = os.path.basename(manifest['source_zip'])
                            metadata_text += f" | Source: {zip_name}"
                        img = self.add_text_overlay(img, metadata_text, 'bottom')
                    
                    # Write frames (repeat the same image for frame duration)
                    for frame_num in range(frames_per_qr):
                        out.write(img)
                        pbar.update(1)
            
            # Release video writer
            out.release()
            
            # Get video file size
            video_size = os.path.getsize(output_video)
            logging.info(f"Video created successfully: {output_video}")
            logging.info(f"Video size: {video_size / (1024*1024):.2f} MB")
            
            return True
            
        except Exception as e:
            logging.error(f"Error creating video: {e}")
            out.release()
            return False
    
    def create_slideshow_video(self, qr_dir, output_video, transition_duration=0.5, 
                              static_duration=1.5, resolution=(1920, 1080), fps=30):
        """Create video with smooth transitions between QR codes."""
        
        qr_files = self.get_qr_files(qr_dir)
        if len(qr_files) < 2:
            logging.error("Need at least 2 QR codes for slideshow")
            return False
        
        # Calculate frame counts
        transition_frames = int(transition_duration * fps)
        static_frames = int(static_duration * fps)
        frames_per_qr = static_frames + transition_frames
        total_frames = len(qr_files) * frames_per_qr
        
        logging.info(f"Creating slideshow video with {len(qr_files)} QR codes")
        logging.info(f"Static duration: {static_duration}s, Transition: {transition_duration}s")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, resolution)
        
        if not out.isOpened():
            logging.error("Failed to initialize video writer")
            return False
        
        try:
            with tqdm(total=total_frames, desc="Creating slideshow") as pbar:
                for i, qr_file in enumerate(qr_files):
                    current_img = self.load_and_resize_image(qr_file, resolution)
                    if current_img is None:
                        continue
                    
                    # Add frame number
                    current_img = self.add_text_overlay(current_img, f"QR {i+1}/{len(qr_files)}", 'top')
                    
                    # Static frames
                    for _ in range(static_frames):
                        out.write(current_img)
                        pbar.update(1)
                    
                    # Transition frames (if not last image)
                    if i < len(qr_files) - 1:
                        next_img = self.load_and_resize_image(qr_files[i + 1], resolution)
                        if next_img is not None:
                            next_img = self.add_text_overlay(next_img, f"QR {i+2}/{len(qr_files)}", 'top')
                            
                            # Create transition
                            for t in range(transition_frames):
                                alpha = t / transition_frames
                                blended = cv2.addWeighted(current_img, 1-alpha, next_img, alpha, 0)
                                out.write(blended)
                                pbar.update(1)
                    else:
                        # Last image - just add static frames
                        for _ in range(transition_frames):
                            out.write(current_img)
                            pbar.update(1)
            
            out.release()
            
            video_size = os.path.getsize(output_video)
            logging.info(f"Slideshow video created: {output_video}")
            logging.info(f"Video size: {video_size / (1024*1024):.2f} MB")
            
            return True
            
        except Exception as e:
            logging.error(f"Error creating slideshow: {e}")
            out.release()
            return False


def main():
    parser = argparse.ArgumentParser(description="Convert QR code images to MP4 video")
    parser.add_argument("--qr-dir", 
                       default="images_direct",
                       help="Directory containing QR code images")
    parser.add_argument("--output", 
                       default="qr_codes.mp4",
                       help="Output video file path")
    parser.add_argument("--duration", 
                       type=float, 
                       default=2.0,
                       help="Duration per QR code in seconds")
    parser.add_argument("--fps", 
                       type=int, 
                       default=30,
                       help="Video frame rate")
    parser.add_argument("--resolution", 
                       default="1920x1080",
                       help="Video resolution (WIDTHxHEIGHT)")
    parser.add_argument("--slideshow", 
                       action="store_true",
                       help="Create slideshow with transitions")
    parser.add_argument("--no-frame-numbers", 
                       action="store_true",
                       help="Don't add frame numbers")
    parser.add_argument("--no-metadata", 
                       action="store_true",
                       help="Don't add metadata overlay")
    parser.add_argument("--log-level", 
                       default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)
    
    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
    except:
        logging.error(f"Invalid resolution format: {args.resolution}")
        sys.exit(1)
    
    # Validate input directory
    if not os.path.exists(args.qr_dir):
        logging.error(f"QR directory not found: {args.qr_dir}")
        sys.exit(1)
    
    # Create converter and process
    converter = QRToVideoConverter()
    
    try:
        if args.slideshow:
            success = converter.create_slideshow_video(
                qr_dir=args.qr_dir,
                output_video=args.output,
                resolution=resolution,
                fps=args.fps
            )
        else:
            success = converter.create_video(
                qr_dir=args.qr_dir,
                output_video=args.output,
                frame_duration=args.duration,
                resolution=resolution,
                fps=args.fps,
                add_frame_numbers=not args.no_frame_numbers,
                add_metadata=not args.no_metadata
            )
        
        if success:
            print(f"Video created successfully: {args.output}")
            
            # Show video info
            video_size = os.path.getsize(args.output)
            print(f"Video size: {video_size / (1024*1024):.2f} MB")
            
            # Try to get video duration
            try:
                cap = cv2.VideoCapture(args.output)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = frame_count / fps
                cap.release()
                print(f"Duration: {duration:.1f} seconds")
                print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            except:
                pass
            
            sys.exit(0)
        else:
            print("Video creation failed - check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Video creation interrupted by user")
        print("Video creation interrupted")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"Video creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
