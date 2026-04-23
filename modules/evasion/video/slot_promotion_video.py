from base_module import BaseModule
import os
import sys
import subprocess
import math
import glob
import time

class SlotPromotionVideo(BaseModule):
    def __init__(self):
        super().__init__()
        self.description = "Video injector for slot/promotion overlays using FFmpeg"

        # Register options sesuai kebutuhan script original
        self.register_option("PATH", "", True, "Target video source path")
        self.register_option("GIF", "", True, "Overlay GIF path (frame)")
        self.register_option("ICON", "", True, "PNG Icon/Logo path")
        self.register_option("DURATION", "10", True, "Split duration per segment (seconds)")
        self.register_option("MIN_SIZE", "0", False, "Auto-delete if output size < X MB")
        self.register_option("WIPE", "false", False, "Delete source after process (true/false)")
        self.register_option("OUTPUT_DIR", "injected_outputs", False, "Output directory name")

    def get_video_duration(self, path):
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return float(result.stdout.strip())
        except:
            return 0.0

    def run(self):
        # Ambil nilai dari options
        video_path = self.options["PATH"]["value"]
        gif_path = self.options["GIF"]["value"]
        icon_path = self.options["ICON"]["value"]
        duration = int(self.options["DURATION"]["value"])
        min_size = float(self.options["MIN_SIZE"]["value"])
        wipe_source = str(self.options["WIPE"]["value"]).lower() == "true"
        output_dir = self.options["OUTPUT_DIR"]["value"]

        # ANSI Colors for internal log
        R, B, W, RESET = "\033[31m", "\033[34m", "\033[37m", "\033[0m"

        if not os.path.exists(video_path):
            print(f"{R}[!] Error: Target video not found!{RESET}")
            return

        total_dur = self.get_video_duration(video_path)
        if total_dur == 0:
            print(f"{R}[!] Error: FFmpeg failed to read metadata!{RESET}")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        est_frags = math.ceil(total_dur / duration)
        print(f"{W}[{B}* {W}] Source: {os.path.basename(video_path)}")
        print(f"{W}[{B}* {W}] Duration: {int(total_dur)}s | Expected Sectors: {est_frags}")
        print(f"{R}" + "—" * 50 + f"{RESET}")

        # Segmenting Binary Stream
        print(f"{W}[{B}EXEC{W}] Fragmenting video segments...")
        split_cmd = [
            "ffmpeg", "-v", "error", "-i", video_path,
            "-f", "segment", "-segment_time", str(duration),
            "-c", "copy", "-reset_timestamps", "1", "chunk_%03d.mp4", "-y"
        ]
        subprocess.run(split_cmd)

        matches = sorted(glob.glob("chunk_*.mp4"))
        total_start = time.time()

        for i, frag in enumerate(matches):
            output_file = os.path.join(output_dir, f"payload_{i+1}.mp4")

            # Progress bar logic
            elapsed = time.time() - total_start
            eta = f" | ETA: {int((elapsed / (i+1)) * (len(matches) - (i+1)))}s" if i > 0 else ""
            sys.stdout.write(f"\r{W}[{R}INJECTING {i+1}/{len(matches)}{W}]{B}{eta}{RESET}")
            sys.stdout.flush()

            # Complex Filter for Overlay
            v_filter = (
                "[0:v]scale=-2:400,pad=720:480:(720-iw)/2:40,setsar=1[m];"
                "[1:v]scale=720:40[t];[2:v]scale=720:40[b];"
                "[3:v]scale=100:-1,format=rgba,colorchannelmixer=aa=0.8[l];"
                "[m][t]overlay=0:0:shortest=1[v1];[v1][b]overlay=0:H-h:shortest=1[v2];[v2][l]overlay=20:50"
            )

            render_cmd = [
                "ffmpeg", "-v", "error", "-i", frag,
                "-ignore_loop", "0", "-i", gif_path,
                "-ignore_loop", "0", "-i", gif_path,
                "-i", icon_path, "-filter_complex", v_filter,
                "-map", "0:a?", "-c:v", "libx264",
                "-b:v", "600k", "-preset", "superfast", "-shortest", output_file, "-y"
            ]

            subprocess.run(render_cmd)

            # Clean up chunk
            if os.path.exists(frag):
                os.remove(frag)

            # Min Size Filter
            if min_size > 0 and os.path.exists(output_file):
                if (os.path.getsize(output_file) / (1024 * 1024)) < min_size:
                    os.remove(output_file)

        print(f"\n\n{R}[COMPLETE] {W}Payloads deployed to: {output_dir}{RESET}")

        if wipe_source:
            os.remove(video_path)
            print(f"{R}[WIPE] {W}Source file has been deleted.{RESET}")
