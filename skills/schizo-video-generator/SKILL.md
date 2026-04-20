---
name: schizo-video-generator
description: Generate a complete 30-second music video from a text prompt — AI images, animated clips, soundtrack, and glitch effects (pixel sort, RGB split, color shifts, negative flashes). Use when user asks to "generate a music video", "create a psychedelic video", "make a 30s video with effects", "glitch music video", or provides a vibe prompt for video content. Bundled with scripts/ for full pipeline automation.
version: 1.0.0
category: creative
compatibility: Requires FAL_KEY env var, Python 3.10+, ffmpeg 7.1+, fal-client, requests, pillow, numpy. Takes 15-20 min to run. ~$5.17 API cost per video at 720p (~$2.67 at 480p).
metadata:
  author: Nate
  hermes:
    tags: [music-video, glitch, pixel-sort, psychedelic, ai-video, fal-ai]
---

# Schizo Video Generator

Generate a complete 30-second music video from a single text prompt. The pipeline creates 10 AI-generated images, animates them into video clips, generates a soundtrack, and applies 8 layers of glitch effects as random flashes across the full timeline.

## Instructions

### Step 1: Verify Prerequisites

Before running, confirm the following are available:

1. **FAL_KEY** environment variable is set (API key from [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys))
2. **Python 3.10+** with packages: `pip3 install fal-client requests pillow numpy`
3. **FFmpeg 7.1+** with libx264 and libmp3lame codecs

**Quick check:**
```bash
echo $FAL_KEY  # Should output your API key
python3 -c "import fal_client; print('OK')"
ffmpeg -version | head -1
```

### Step 2: Generate the Video

```bash
python3 scripts/schizo_video.py "your vibe prompt here" --output-dir ./output
```

**Example prompts:**
- `"psytrance dmt trip cosmic entities"`
- `"dark industrial heavy metal chaos"`
- `"ambient electronic meditation space"`
- `"vaporwave retro neon nostalgia"`

### Step 3: Review Output

The video is saved to `./output/final.mp4`. The pipeline also generates:

```
output/
├── images/           # 10 source images (1920x1080)
├── clips/            # 10 animated clips (5s each, 720p)
├── psytrance.mp3     # 30s generated soundtrack
├── final.mp4         # 30s final video with effects + music
└── tmp_schizo/       # Temp files (auto-cleaned)
```

## The Pipeline

### Phase 1: Media Generation (~5-10 min)

1. **Images** — 10 unique images via `fal-ai/flux/schnell` (landscape_16_9, 8 steps)
2. **Video clips** — Each image animated via `fal-ai/wan-25-preview/image-to-video` (720p, 5s)
3. **Soundtrack** — 30s instrumental via `fal-ai/minimax-music/v2.6` (uses the prompt as vibe)

### Phase 2: Base Video (~1 min)

Clips are trimmed to 2.5-3.5s each (random trims), concatenated to exactly 30s at 30fps.

### Phase 3: Glitch Effects (~10-15 min)

8 effect passes are applied sequentially. Effects flash on/off at random time windows across the 30s timeline — not per-clip, but throughout the entire video.

| Pass | Effect | Windows | Description |
|------|--------|---------|-------------|
| 1 | Pixel Sort #1 | 35 | Brightness-based interval sorting, grows 30%→85% intensity over time |
| 2 | RGB Split | 15 | 18px R/B channel separation + VHS tear displacement |
| 3 | Pixel Sort #2 | 35 | Second sequence, different random timing, same growth curve |
| 4 | Color Pump | 8 | Red boost (+32), blue reduce (−16), green noise (±15) |
| 5 | Grain Growth | 25 | Film noise grows from σ=15 → σ=45 |
| 6 | Color Shift | 20 | Psychedelic hue rotation (channel cycling) + saturation boost |
| 7 | Negative Flash | 12 | Partial invert (50-85%) with color tints |
| 8 | Color Shift #2 | 15 | Different timing, second pass |

Each effect pass extracts all 905 frames (30fps × 30s), applies the effect only to affected frames, and re-encodes.

### Phase 4: Audio Mix (~30s)

The final video is composited with the generated soundtrack.

## Customization

### Change image/video prompts

Edit `DEFAULT_IMAGE_PROMPTS` and `DEFAULT_VIDEO_PROMPTS` arrays in `scripts/schizo_video.py` to match your desired aesthetic.

For reference aesthetics, see `media/moodboard/` at the repo root — it contains the canonical AWO visual vocabulary (occult geometry, dark gothic cathedrals, ceremonial magic circles, post-internet glitch, terminal/hacker occultism, chibi conspiracy mascots, daemon sigils, gold-on-black color palette, etc.). Describe those images in prose and feed the descriptions into `DEFAULT_IMAGE_PROMPTS` to keep generations on-brand.

### Adjust effect intensity

In the `generate()` method, modify effect pass parameters:

```python
self._rand_win(count=35, min_d=0.15, max_d=0.6, seed=42)
# count: more windows = heavier effect
# min_d/max_d: duration range per effect window (seconds)
# Increase both for heavier effect, decrease for lighter
```

### Skip certain phases

```bash
python3 scripts/schizo_video.py "vibe" --images-dir ./my-images  # Use existing images
python3 scripts/schizo_video.py "vibe" --music-file ./my-track.mp3  # Use existing music
python3 scripts/schizo_video.py "vibe" --clips-dir ./my-clips  # Use existing clips
```

## Examples

**Example 1: Psychedelic DMT video**
```bash
python3 scripts/schizo_video.py "psytrance dmt trip cosmic entities" --output-dir ./dmt-video
```
Result: `./dmt-video/final.mp4` — 30s, 720p, 84MB with full effect pipeline + psytrance soundtrack.

**Example 2: Dark industrial**
```bash
python3 scripts/schizo_video.py "dark industrial techno chaos 140bpm" --output-dir ./industrial-video
```
Edit `DEFAULT_IMAGE_PROMPTS` first with darker/industrial themes, then run.

**Example 3: Vaporwave aesthetic**
```bash
python3 scripts/schizo_video.py "vaporwave synthwave neon retro 80s" --output-dir ./vaporwave-video
```
Edit prompts for pink/purple/cyan color schemes and retro imagery.

## Troubleshooting

### FAL_KEY not set
**Error:** `401 Unauthorized` or `FAL_KEY not set`
**Solution:** `export FAL_KEY="your-api-key"` before running.

### Music generation times out
**Cause:** minimax-music/v2.6 can take 3+ minutes and may hit timeout.
**Solution:** 
- Generate music separately: `python3 -c "import fal_client; ..."`
- Or use `--music-file ./existing-track.mp3` to skip generation.

### Video clip generation fails (clips 5-9)
**Cause:** wan-2.5 API can timeout on high load.
**Solution:** Re-run the command. Existing clips are cached, only missing ones regenerate.

### "No frames extracted" during effects
**Cause:** ffmpeg frame extraction failed.
**Solution:** Check that video plays and is valid H.264. Try:
```bash
ffmpeg -i ./clips/clip_00.mp4 -t 10 -f null -  # Test playback
```

### Permission denied on scripts
**Solution:** Make executable:
```bash
chmod +x scripts/schizo_video.py
```

### Out of disk space during processing
**Cause:** Temp files can reach 5-10GB during frame-level processing.
**Solution:** Ensure 15-20GB free space. Temp directory is auto-cleaned on completion.

## Performance & Cost

| Resource | Cost | Time |
|----------|------|------|
| 10 images (flux/schnell) | ~$0.02 | 1-2 min |
| 10 video clips (wan-2.5, 720p) | ~$5.00 | 5-10 min |
| Music (minimax-music) | ~$0.15 | 1-3 min |
| Frame processing (CPU) | $0 | 10-15 min |

**Total: ~$5.17 per video at 720p, 15-20 min runtime**

### Cut cost ~50% by rendering at 480p

The dominant cost is the wan-2.5 image-to-video step (~$0.50/clip at 720p, ~$0.25/clip at 480p). Dropping to 480p brings the total to **~$2.67 per video** with only minor fidelity loss — the glitch/pixel-sort pipeline masks most of the resolution delta anyway.

To switch, edit `scripts/schizo_video.py` and change the `resolution` argument in the wan-2.5 call:

```python
r = fal_client.run("fal-ai/wan-25-preview/image-to-video",
    arguments={"prompt": self.video_prompts[i], "image_url": url, "duration": 5, "resolution": "480p"})
```

### Customizing the vibe

The script uses the prompt for:
1. **Music generation** — directly passed to minimax-music/v2.6 as style descriptor
2. **Images** — uses `DEFAULT_IMAGE_PROMPTS` array (edit manually for specific aesthetics)

For best results, include **genre, mood, BPM, and atmosphere** in your prompt:
- ✅ `"psytrance 145bpm cosmic transcendence ethereal"`
- ✅ `"dark ambient tribal ritual percussion"`
- ❌ `"make a cool video"`

## Best Practices

- **Let it run uninterrupted** — the full pipeline takes 15-20 min without user interaction
- **Run on macOS/Linux** — tested on macOS, requires Unix tools
- **Monitor disk space** — temporary files are large but auto-cleaned
- **Use descriptive prompts** — the more specific the vibe, the better the music and imagery
- **Iterate on prompts** — regenerate music/clips with refined vibes if the first result isn't right

## Credits

- Images: [fal-ai/flux/schnell](https://fal.ai/models/fal-ai/flux/schnell)
- Video: [fal-ai/wan-25-preview/image-to-video](https://fal.ai/models/fal-ai/wan-25-preview/image-to-video)
- Music: [fal-ai/minimax-music/v2.6](https://fal.ai/models/fal-ai/minimax-music/v2.6)
- Pixel sorting algorithm based on [DavidMcLaughlin208/PixelSorting](https://github.com/DavidMcLaughlin208/PixelSorting)
