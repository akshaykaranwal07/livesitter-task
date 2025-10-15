#!/usr/bin/env bash
# Usage: ./start_ffmpeg.sh "rtsp://..." [output_dir]
RTSP_URL="$1"
OUT_DIR="${2:-static_hls}"
mkdir -p "$OUT_DIR"
# small segments for lower latency
ffmpeg -rtsp_transport tcp -i "$RTSP_URL" \
-c:v copy -c:a aac -f hls \
-hls_time 2 -hls_list_size 3 -hls_flags delete_segments "$OUT_DIR/stream.m3u8"