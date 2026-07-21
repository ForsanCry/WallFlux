import subprocess
import json
import re
import shutil
from pathlib import Path


# ─── Duration ────────────────────────────────────────────────────────────────

def get_duration(video_path: Path) -> float:
    """Return video duration in seconds (float)."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(video_path),
        ],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


# ─── Time parsing ─────────────────────────────────────────────────────────────

def parse_timestamp(raw: str) -> float:
    """
    Parse a user-supplied timestamp string into seconds (float).

    Accepted formats:
        32            → 32.0 s
        32.450        → 32.45 s
        1:32          → 92.0 s
        1:32.450      → 92.45 s
        1:04:32       → 3872.0 s
        1:04:32.450   → 3872.45 s
    """
    raw = raw.strip()

    # Three distinct patterns by number of colons:
    #   no colon   → S or S.ms
    #   one colon  → M:S or M:S.ms
    #   two colons → H:M:S or H:M:S.ms
    ms_frag = r'(?:\.(?P<ms>\d+))?$'

    p_s   = re.match(r'^(?P<s>\d+)' + ms_frag, raw)
    p_ms  = re.match(r'^(?P<m>\d+):(?P<s>\d+)' + ms_frag, raw)
    p_hms = re.match(r'^(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)' + ms_frag, raw)

    if p_hms:
        h, m, s = int(p_hms.group("h")), int(p_hms.group("m")), int(p_hms.group("s"))
        ms_str  = p_hms.group("ms") or "0"
    elif p_ms:
        h, m, s = 0, int(p_ms.group("m")), int(p_ms.group("s"))
        ms_str  = p_ms.group("ms") or "0"
    elif p_s:
        h, m, s = 0, 0, int(p_s.group("s"))
        ms_str  = p_s.group("ms") or "0"
    else:
        raise ValueError(
            f"Invalid timestamp: '{raw}'\n"
            "Accepted formats: 32 / 32.450 / 1:32 / 1:32.450 / 1:04:32.450"
        )

    ms = int(ms_str) / (10 ** len(ms_str))   # "450" → 0.450, "45" → 0.45
    return h * 3600 + m * 60 + s + ms


def seconds_to_timestamp(secs: float) -> str:
    """Convert float seconds to human-readable M:SS.mmm string."""
    secs = max(0.0, secs)
    h   = int(secs // 3600)
    rem = secs % 3600
    m   = int(rem // 60)
    s   = rem % 60

    if h > 0:
        return f"{h}:{m:02d}:{s:06.3f}"
    return f"{m}:{s:06.3f}"


# ─── Auto-detect cut point ────────────────────────────────────────────────────

def detect_cut_point(video_path: Path) -> float:
    """
    Automatically detect the best cut point using:
      1. Audio energy peaks  (ffmpeg astats + volumedetect)
      2. Scene change score  (ffmpeg select filter)

    Returns the timestamp in seconds where both signals peak closest together.
    Falls back to audio-only if scene detection finds nothing.
    """
    duration = get_duration(video_path)

    audio_peaks  = _detect_audio_peaks(video_path)
    scene_points = _detect_scene_changes(video_path)

    if not audio_peaks:
        raise RuntimeError("Could not detect audio peaks in the video.")

    if not scene_points:
        # Fallback: strongest audio peak
        return audio_peaks[0]

    # Find the audio peak that is closest to a scene change (within 1.5 s window)
    best = None
    best_dist = float("inf")

    for ap in audio_peaks:
        for sc in scene_points:
            dist = abs(ap - sc)
            if dist < 1.5 and dist < best_dist:
                best_dist = dist
                best = ap

    # If no co-occurring pair found, use strongest audio peak
    return best if best is not None else audio_peaks[0]


def _detect_audio_peaks(video_path: Path) -> list[float]:
    """
    Use ffmpeg silencedetect + astats to find timestamps where
    audio energy is significantly above average.
    Returns list of timestamps (seconds), strongest first.
    """
    result = subprocess.run(
        [
            "ffmpeg", "-i", str(video_path),
            "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )

    output = result.stderr

    # Parse "pts_time:X" lines paired with RMS values
    pts_pattern = re.compile(r'pts_time:([\d.]+)')
    rms_pattern = re.compile(r'lavfi\.astats\.Overall\.RMS_level=([-\d.]+|inf|-inf)')

    timestamps = []
    rms_values = []

    for line in output.splitlines():
        pt = pts_pattern.search(line)
        rm = rms_pattern.search(line)
        if pt:
            timestamps.append(float(pt.group(1)))
        if rm:
            val = rm.group(1)
            try:
                rms_values.append(float(val))
            except ValueError:
                rms_values.append(-100.0)  # -inf etc.

    if not timestamps or not rms_values:
        return []

    # Pair up and sort by RMS descending
    pairs = list(zip(timestamps, rms_values))
    pairs.sort(key=lambda x: x[1], reverse=True)

    # Return top-5 candidate timestamps
    return [p[0] for p in pairs[:5]]


def _detect_scene_changes(video_path: Path) -> list[float]:
    """
    Detect scene changes using ffmpeg scene filter.
    Returns list of timestamps (seconds) where scene score > 0.35.
    """
    result = subprocess.run(
        [
            "ffmpeg", "-i", str(video_path),
            "-vf", "select=gt(scene\\,0.35),metadata=print:key=lavfi.scene_score",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )

    pts_pattern   = re.compile(r'pts_time:([\d.]+)')
    score_pattern = re.compile(r'lavfi\.scene_score=([\d.]+)')

    timestamps = []
    scores     = []

    for line in result.stderr.splitlines():
        pt = pts_pattern.search(line)
        sc = score_pattern.search(line)
        if pt:
            timestamps.append(float(pt.group(1)))
        if sc:
            scores.append(float(sc.group(1)))

    if not timestamps:
        return []

    pairs = list(zip(timestamps, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in pairs[:10]]


# ─── Lossless cutting ─────────────────────────────────────────────────────────

def cut_video(
    source: Path,
    highlight_out: Path,
    wp_out: Path,
    cut_point: float,
):
    """
    Losslessly cut source video at cut_point.
      highlight_out → 0 to cut_point
      wp_out        → cut_point to end
    """
    _lossless_cut(source, highlight_out, start=None,      end=cut_point)
    _lossless_cut(source, wp_out,        start=cut_point, end=None)


def _lossless_cut(
    source: Path,
    output: Path,
    start: float | None,
    end:   float | None,
):
    cmd = ["ffmpeg", "-y"]

    if start is not None:
        cmd += ["-ss", str(start)]

    cmd += ["-i", str(source)]

    if end is not None and start is None:
        cmd += ["-to", str(end)]
    elif end is not None and start is not None:
        # After -ss seek, duration = end - start
        cmd += ["-t", str(end - start)]

    cmd += ["-c", "copy", str(output)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg lossless cut failed:\n{result.stderr[-800:]}"
        )


# ─── Preview ─────────────────────────────────────────────────────────────────

def preview_cut(video_path: Path, cut_point: float):
    """
    Open mpv starting 3 seconds before the cut point so the user
    can confirm the transition feels right.
    """
    start = max(0.0, cut_point - 3.0)
    subprocess.run(
        [
            "mpv",
            f"--start={start}",
            f"--end={cut_point + 2.0}",
            "--fullscreen=no",
            "--title=WallFlux Preview — press Q to close",
            str(video_path),
        ]
    )
