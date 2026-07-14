"""Build web-ready images and videos from media-source into public."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "media-source"
PUBLIC = ROOT / "public"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def find_ffmpeg() -> str:
    configured = os.environ.get("FFMPEG")
    if configured and Path(configured).is_file():
        return configured

    executable = shutil.which("ffmpeg")
    if executable:
        return executable

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as error:
        raise SystemExit(
            "FFmpeg was not found. Install it or set the FFMPEG environment variable."
        ) from error


def optimize_image(source: Path) -> None:
    relative = source.relative_to(SOURCE)
    output_stem = (PUBLIC / "media" / relative).with_suffix("")
    output_stem.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")

        for target_width in (640, 1600):
            variant = image.copy()
            if variant.width > target_width:
                target_height = round(variant.height * target_width / variant.width)
                variant = variant.resize((target_width, target_height), Image.Resampling.LANCZOS)

            output = Path(f"{output_stem}-{target_width}.webp")
            quality = 86 if "certificates" in relative.parts else 82
            variant.save(output, "WEBP", quality=quality, method=6)
            print(f"image: {relative} -> {output.relative_to(ROOT)}")


def optimize_video(ffmpeg: str, source: Path) -> None:
    relative = source.relative_to(SOURCE)
    output = (PUBLIC / relative).with_suffix(".mp4")
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "warning",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-vf",
        "scale='min(1280,iw)':-2",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "26",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        "-map_metadata",
        "-1",
        str(output),
    ]
    subprocess.run(command, check=True)
    print(
        f"video: {relative} -> {output.relative_to(ROOT)} "
        f"({source.stat().st_size / 1_000_000:.1f} MB to {output.stat().st_size / 1_000_000:.1f} MB)"
    )


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"Source directory does not exist: {SOURCE}")

    files = [path for path in SOURCE.rglob("*") if path.is_file()]
    image_sources: dict[Path, Path] = {}
    for source in files:
        if source.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        output_key = source.relative_to(SOURCE).with_suffix("")
        existing = image_sources.get(output_key)
        if existing is None or source.suffix.lower() == ".png":
            image_sources[output_key] = source

    for source in image_sources.values():
        optimize_image(source)

    videos = [path for path in files if path.suffix.lower() in VIDEO_EXTENSIONS]
    if videos:
        ffmpeg = find_ffmpeg()
        for source in videos:
            optimize_video(ffmpeg, source)


if __name__ == "__main__":
    main()
