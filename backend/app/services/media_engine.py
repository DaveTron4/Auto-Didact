import os
import asyncio
import uuid
from typing import Dict, List, Optional

try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
except ImportError:
    # MoviePy 2.x uses different import structure
    try:
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    except ImportError:
        raise ImportError(
            "moviepy is required but not properly installed. "
            "Try: pip uninstall moviepy && pip install moviepy==1.0.3"
        )

# Lazy-load diffusers pipeline (initialized once on first use)
_sd_pipeline = None


def _get_sd_pipeline():
    """Lazy-load Stable Diffusion pipeline (singleton)."""
    global _sd_pipeline
    if _sd_pipeline is None:
        try:
            from diffusers import StableDiffusionPipeline
            import torch
        except ImportError as e:
            raise RuntimeError(
                "diffusers and torch are required. Install with: "
                "pip install diffusers transformers accelerate torch"
            ) from e

        model_id = os.getenv("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        _sd_pipeline = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            safety_checker=None,  # Disable NSFW filter for educational content
        )
        _sd_pipeline = _sd_pipeline.to(device)
        
        # Enable memory optimizations for lower VRAM usage
        if device == "cuda":
            _sd_pipeline.enable_attention_slicing()
    
    return _sd_pipeline


async def _synthesize_edge_tts(text: str, outfile: str, voice: str = "en-US-GuyNeural"):
    """Use edge-tts to synthesize text to an audio file (async)."""
    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError("edge-tts is required. Install with `pip install edge-tts`") from e

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(outfile)


async def _generate_image_diffusers(prompt: str, outfile: str, seed: Optional[int] = None):
    """Generate an image using Stable Diffusion (diffusers) and save to outfile."""
    import torch
    
    # Get the pipeline (lazy-loaded singleton)
    pipe = _get_sd_pipeline()
    
    # Get style prefix from env for consistency
    style_prefix = os.getenv("IMAGE_STYLE_PREFIX", "educational illustration, clean, simple")
    full_prompt = f"{style_prefix}, {prompt}"
    
    # Use deterministic seed if provided (for consistency)
    generator = None
    if seed is not None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)
    
    # Run in executor to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    image = await loop.run_in_executor(
        None,
        lambda: pipe(
            full_prompt,
            num_inference_steps=int(os.getenv("SD_INFERENCE_STEPS", "30")),
            guidance_scale=float(os.getenv("SD_GUIDANCE_SCALE", "7.5")),
            generator=generator,
        ).images[0]
    )
    
    # Save image
    image.save(outfile)


async def create_video_from_script(script: Dict, output_path: str = None) -> str:
    """
    Given a script dict (with 'title' and 'scenes'), generate audio+images and stitch into an MP4.

    script: {
      "title": "...",
      "scenes": [ {"id":1, "narrator_text":"...","image_prompt":"..."}, ... ]
    }

    Returns the path to the generated video file.
    """
    if output_path is None:
        uid = uuid.uuid4().hex[:8]
        os.makedirs("backend/output", exist_ok=True)
        output_path = os.path.join("backend", "output", f"video_{uid}.mp4")

    scenes = script.get("scenes", [])
    if not scenes:
        raise ValueError("Script contains no scenes")

    os.makedirs("backend/tmp/media", exist_ok=True)

    audio_tasks = []
    image_tasks = []
    audio_files: List[str] = []
    image_files: List[str] = []

    # Launch generation tasks
    base_seed = int(os.getenv("IMAGE_BASE_SEED", "42"))
    for idx, scene in enumerate(scenes):
        sid = scene.get("id") or uuid.uuid4().hex[:6]
        narrator = scene.get("narrator_text", "")
        prompt = scene.get("image_prompt", "")

        audio_path = os.path.join("backend", "tmp", "media", f"audio_{sid}.mp3")
        image_path = os.path.join("backend", "tmp", "media", f"image_{sid}.png")

        audio_files.append(audio_path)
        image_files.append(image_path)

        audio_tasks.append(_synthesize_edge_tts(narrator, audio_path))
        # Use deterministic seed (base + scene index) for consistent style
        image_tasks.append(_generate_image_diffusers(prompt, image_path, seed=base_seed + idx))

    # run audio and image generation concurrently
    await asyncio.gather(*(audio_tasks + image_tasks))

    # Build video clips
    clips = []
    for a_path, i_path in zip(audio_files, image_files):
        if not os.path.exists(a_path):
            raise RuntimeError(f"Missing audio file: {a_path}")
        if not os.path.exists(i_path):
            raise RuntimeError(f"Missing image file: {i_path}")

        audio_clip = AudioFileClip(a_path)
        duration = audio_clip.duration

        image_clip = ImageClip(i_path).set_duration(duration)
        image_clip = image_clip.set_audio(audio_clip)
        clips.append(image_clip)

    final = concatenate_videoclips(clips, method="compose")

    # Write the video file (blocking call)
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    # Cleanup clips to free resources
    final.close()
    for c in clips:
        try:
            c.close()
        except Exception:
            pass

    return output_path
