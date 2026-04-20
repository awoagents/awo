# Schizo Video Generator

A skill for Claude that generates complete 30-second music videos from a single text prompt.

![Example output](screenshot-here.png)

## What it does

1. Generates 10 esoteric AI images from your vibe prompt
2. Animates each into 5s video clips
3. Creates a matching instrumental soundtrack
4. Cuts everything into a 30s base video
5. Applies 8 layers of glitch effects:
   - Progressive pixel sorting (grows 30%→85% intensity)
   - RGB channel splitting + VHS tears
   - Color pumping (red/blue balance shifts)
   - Growing film grain
   - Psychedelic color shifts
   - Negative flashes with color tints

**Cost:** ~$1.17 per video  
**Runtime:** 15-20 minutes  
**Output:** 1280x720 @ 30fps, 84MB MP4

## Quick start

```bash
# Install dependencies
pip3 install fal-client requests pillow numpy

# Set your FAL API key
export FAL_KEY="your-key-here"

# Run the pipeline
python3 scripts/schizo_video.py "psytrance dmt trip cosmic entities" --output-dir ./my-video
```

See `SKILL.md` inside the skill folder for full documentation, customization guide, and troubleshooting.

## Using as a Claude Skill

1. Download this repo or the `.zip` file
2. Upload to Claude: Settings > Capabilities > Skills > Upload skill
3. Ask: "Generate a music video from the prompt 'vaporwave retro neon'"

## Requirements

- **FAL API key** — get at [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)
- **Python 3.10+**
- **FFmpeg 7.1+** with libx264

## Examples

```bash
# Psychedelic
python3 scripts/schizo_video.py "psytrance 145bpm cosmic transcendence"

# Dark
python3 scripts/schizo_video.py "dark industrial tribal ritual 140bpm"

# Relaxing
python3 scripts/schizo_video.py "ambient meditation ethereal space journey"
```

## License

MIT
