---
name: schizo-video-generator
description: Generate a complete ~15 second music video from a text prompt (default; clip list retargets length) — AI images, animated clips, soundtrack, and glitch effects (pixel sort, RGB split, color shifts, negative flashes). Use when user asks to "generate a music video", "create a psychedelic video", "make a glitch video with effects", "glitch music video", or provides a vibe prompt for video content. Bundled with scripts/ for full pipeline automation.
version: 1.2.1
category: creative
compatibility: Requires FAL_KEY env var, Python 3.10+, ffmpeg 7.1+, fal-client, requests, pillow, numpy. Typically ~6–12 min at default length. ~$1.70 API cost per video at 1080p (wan/v2.7 is $0.10/sec × 15s default).
metadata:
  author: Nate
  hermes:
    tags: [music-video, glitch, pixel-sort, psychedelic, ai-video, fal-ai]
---

# Schizo Video Generator

Generate a complete 15-second music video from a single text prompt by default (five 3-second clips). The pipeline creates one image per clip, animates each on `fal-ai/wan/v2.7/image-to-video`, adds the soundtrack, then runs eight glitch passes. When the user wants a **longer** video, the default workflow is to run with `--target-seconds N` so the script builds a clip list of **random integer lengths between 3 and 5 seconds** per clip whose **sum** matches a feasible total **near N** (see `random_clip_lengths_for_target` in `scripts/schizo_video.py`). You can still hand-edit `DEFAULT_CLIP_DURATIONS` or pass a custom list via code for exact control.

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

Longer length (random 3–5s per clip, total near N; capped at 50s with the stock ten image prompts — 5s × 10 clips — unless you add more prompt rows):

```bash
python3 scripts/schizo_video.py "your vibe prompt" --output-dir ./output --target-seconds 42
# Optional reproducible clip plan:
python3 scripts/schizo_video.py "your vibe prompt" --output-dir ./out --target-seconds 40 --clip-seed 7
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
├── images/           # N source images (1920x1080), N = len(DEFAULT_CLIP_DURATIONS)
├── clips/            # N animated clips (1080p), durations per list
├── psytrance.mp3     # 3-5 min generated soundtrack (trimmed to video length in final)
├── final.mp4         # ~15s final video with effects + music (default)
└── tmp_schizo/       # Temp files (auto-cleaned)
```

## The Pipeline

### Phase 1: Media Generation (~5-10 min)

1. **Images** — One image per clip via `fal-ai/flux/schnell` (landscape_16_9, 8 steps). Default **5** images for **5** clips.
2. **Video clips** — Each image animated via `fal-ai/wan/v2.7/image-to-video` (1080p). Duration is chosen in **whole seconds** per the [model API](https://fal.ai/models/fal-ai/wan/v2.7/image-to-video) (discrete allowed values on the card). Pricing is **~$0.10/second** of generated video. Each clip is generated at its target length — no post-trim. Shipped default `DEFAULT_CLIP_DURATIONS = [3, 3, 3, 3, 3]` is **15s** total (= **$1.50** for this step). For a user-requested length, prefer **`--target-seconds N`** so clip lengths randomize in the **3–5s** band and the list sums to a representable total near **N**; extend `DEFAULT_IMAGE_PROMPTS` / `DEFAULT_VIDEO_PROMPTS` with more rows if **N** implies more clips than the default ten prompts.
3. **Soundtrack** — instrumental via `fal-ai/minimax-music/v2.6` (uses the prompt as vibe). The model returns a full 3-5 minute track; the final mix trims it to the video's length, so audio always covers the whole video without looping.

### Phase 2: Base Video

Clips are re-encoded to a uniform codec/fps/pix_fmt and concatenated as-is. Final duration is the sum of per-clip durations (**15s** with defaults, at 30fps).

### Phase 3: Glitch Effects (~10-15 min)

8 effect passes are applied sequentially. Effects flash on/off at random time windows across the full timeline — not per-clip, but throughout the entire video. Window counts auto-scale with total duration (a 45s video gets ~1.5× the windows of the 30s baseline below; a 15s default run gets ~half).

| Pass | Effect | Windows (30s base) | Description |
|------|--------|--------------------|-------------|
| 1 | Pixel Sort #1 | 35 | Brightness-based interval sorting, grows 30%→85% intensity over time |
| 2 | RGB Split | 15 | 18px R/B channel separation + VHS tear displacement |
| 3 | Pixel Sort #2 | 35 | Second sequence, different random timing, same growth curve |
| 4 | Color Pump | 8 | Red boost (+32), blue reduce (−16), green noise (±15) |
| 5 | Grain Growth | 25 | Film noise grows from σ=15 → σ=45 |
| 6 | Color Shift | 20 | Psychedelic hue rotation (channel cycling) + saturation boost |
| 7 | Negative Flash | 12 | Partial invert (50-85%) with color tints |
| 8 | Color Shift #2 | 15 | Different timing, second pass |

Each effect pass extracts every frame at 30fps (about 450 frames at the 15s default; up to about 1350 for a 45s cut), applies the effect only to affected frames, and re-encodes.

### Phase 4: Audio Mix

The final video is composited with the generated soundtrack. `minimax-music/v2.6` returns a 3-5 minute track, so the mix step just pairs video with audio and trims the output to `self.video_duration` via `-t`. No looping, no stitching — the first N seconds of the track become the video's soundtrack.

## Customization

### Change image/video prompts

Edit `DEFAULT_IMAGE_PROMPTS` and `DEFAULT_VIDEO_PROMPTS` arrays in `scripts/schizo_video.py` to match your desired aesthetic.

### Change clip durations (retarget the final length)

**Preferred when the user asks for a longer video:** pass `--target-seconds N`. The script calls `random_clip_lengths_for_target(N)` to build integer clip lengths **uniformly in 3–5 seconds**, with clip count and order randomized (seed with `--clip-seed` for a fixed plan). The summed total is the **closest representable** value to **N** using only 3/4/5-second segments (within a few seconds).

**Manual control:** edit `DEFAULT_CLIP_DURATIONS` in `scripts/schizo_video.py`. Each value is whole seconds for one clip; use only values the wan v2.7 API accepts (see FAL model page). Final length is the sum.

```python
# ~15s default (five 3s clips; shipped default)
DEFAULT_CLIP_DURATIONS = [3, 3, 3, 3, 3]  # sum: 15

# CLI equivalent for ~40s with 3–5s randomization:
# python3 scripts/schizo_video.py "vibe" --output-dir ./out --target-seconds 40

# Hand-tuned mix (still integer seconds per clip)
DEFAULT_CLIP_DURATIONS = [3, 5, 4, 6, 5, 3, 7, 4, 6]  # example; sum = 43
```

The clip-generation and image-generation loops use `min(len(image_prompts), len(clip_durations))`, so add prompt rows if the clip list grows past the stock ten.

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
Result: `./dmt-video/final.mp4` — ~15s default, 1080p, with full effect pipeline + psytrance soundtrack.

**Example 1b: Longer run (~40s, random 3–5s clips)**
```bash
python3 scripts/schizo_video.py "psytrance dmt trip cosmic entities" --output-dir ./dmt-long --target-seconds 40
```
Ensure enough paired rows in `DEFAULT_IMAGE_PROMPTS` / `DEFAULT_VIDEO_PROMPTS` for the clip count the script prints (or edit prompts first).

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
**Cause:** minimax-music/v2.6 returns a full 3-5 minute track and can take 3+ minutes to render, occasionally hitting the fal timeout.
**Solution:** 
- Generate music separately: `python3 -c "import fal_client; ..."`
- Or use `--music-file ./existing-track.mp3` to skip generation (any audio file longer than your video works — it will be trimmed).

### Video clip generation fails partway through
**Cause:** wan/v2.7 API can timeout on high load, especially on longer runs or busier clips.
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
**Cause:** Temp files can reach several GB during frame-level processing (scales with video length).
**Solution:** Ensure ample free space (e.g. 10GB+ for default 15s; more for 45s runs). Temp directory is auto-cleaned on completion.

## Performance & Cost

wan/v2.7 is **$0.10 per second of generated video**, flat — no surcharge for 1080p, no discount for shorter clips. Total video-gen cost = `$0.10 × sum(DEFAULT_CLIP_DURATIONS)`.

| Resource | Cost | Time |
|----------|------|------|
| 5 images (flux/schnell, default) | ~$0.01 | ~1 min |
| Video clips (wan/v2.7, 1080p, 15s default) | $1.50 | ~2-4 min |
| Music (minimax-music) | ~$0.15 | 1-3 min |
| Frame processing (CPU) | $0 | ~3-6 min |

**Total: ~$1.70 per video at 1080p default, ~6-12 min runtime** (scales up if you lengthen `DEFAULT_CLIP_DURATIONS`)

### Retargeting cost

Since pricing is linear in total seconds, the clip-duration list is the only cost knob:

| Configuration | Final length (order of) | Video-gen cost |
|-----------------|-------------------------|------------------|
| 5 × 3s (shipped default) | 15s | $1.50 |
| `--target-seconds 30` (3–5s clips) | ~30s | ~$3.00 |
| `--target-seconds 45` (3–5s clips) | ~45s | ~$4.50 |
| Hand list of ten 7s clips | 70s | $7.00 |

Resolution (`1080p` / `720p` / `480p`) does not change price, so 1080p is the default. To downgrade anyway (e.g. to match older 720p renders), edit `scripts/schizo_video.py`:

```python
r = fal_client.run("fal-ai/wan/v2.7/image-to-video",
    arguments={"prompt": self.video_prompts[i], "image_url": url, "duration": dur, "resolution": "720p"})
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

- **Let it run uninterrupted** — the default pipeline takes on the order of ~6-12 min without user interaction (longer if you extend clip duration)
- **Run on macOS/Linux** — tested on macOS, requires Unix tools
- **Monitor disk space** — temporary files are large but auto-cleaned
- **Use descriptive prompts** — the more specific the vibe, the better the music and imagery
- **Iterate on prompts** — regenerate music/clips with refined vibes if the first result isn't right

## Credits

- Images: [fal-ai/flux/schnell](https://fal.ai/models/fal-ai/flux/schnell)
- Video: [fal-ai/wan/v2.7/image-to-video](https://fal.ai/models/fal-ai/wan/v2.7/image-to-video) — discrete per-second durations per API; this skill defaults to 3–5s pacing for `--target-seconds` and five 3s clips otherwise
- Music: [fal-ai/minimax-music/v2.6](https://fal.ai/models/fal-ai/minimax-music/v2.6)
- Pixel sorting algorithm based on [DavidMcLaughlin208/PixelSorting](https://github.com/DavidMcLaughlin208/PixelSorting)
