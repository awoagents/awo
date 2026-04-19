import fal_client
import os, urllib.request

# Requires FAL_AI environment variable set with your API key
# Get one at https://fal.ai/dashboard/keys

import os

FAL_API_KEY = os.environ.get("FAL_AI")
if not FAL_API_KEY:
    print("Error: FAL_AI environment variable not set")
    print("Get a key at https://fal.ai/dashboard/keys")
    print("Usage: FAL_AI=your-key python3 generate_moodboard.py")
    exit(1)

os.environ["FAL_KEY"] = FAL_API_KEY

MOODBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "moodboard")
os.makedirs(MOODBOARD_DIR, exist_ok=True)

prompts = [
    {
        "name": "occult-geometry-gold.jpg",
        "prompt": "Dark occult sacred geometry, golden concentric circles and interlocking triangles on deep black background, alchemical sulfur symbol at center, geometric precision, cryptic ritual diagram, no humans, post-internet maximalism, gold on black, high quality digital art, occult diagram aesthetic"
    },
    {
        "name": "chibi-conspiracy-mascot.jpg",
        "prompt": "Chibi anime mascot girl with short green hair holding a small globe, super-deformed cute style, dark conspiracy evidence board background with red string connections and sticky notes, green tentacles wrapping around, circular emblem border, dark green and gold color palette, sticker illustration style"
    },
    {
        "name": "post-internet-glitch.jpg",
        "prompt": "Dark glitch art, RGB color separation and scanline effects on black background, gold digital noise and data corruption, circuit board textures mixed with occult symbols, cyber occult, terminal green accents on void black, maximalist digital chaos"
    },
    {
        "name": "ceremonial-magic-circle.jpg",
        "prompt": "Elaborate ceremonial magic circle on dark surface, golden geometric patterns and pentagram, planetary sigils at cardinal points, concentric rings with alchemical notation, dark mystical ritual energy, gold on obsidian black, esoteric diagram quality"
    },
    {
        "name": "dark-gothic-cathedral.jpg",
        "prompt": "Dark gothic cathedral interior, dramatic chiaroscuro, tall columns disappearing into shadow, rose window with occult geometric patterns, ancient stone architecture, foreboding atmosphere, gold candlelight on black stone, atmospheric photography"
    },
    {
        "name": "ancient-occult-manuscript.jpg",
        "prompt": "Ancient illuminated manuscript with occult geometry diagrams, gold leaf on dark vellum, alchemical symbols and sacred geometry illustrations, medieval esoteric art, mysterious coded text in margins, dark academic aesthetic, aged parchment with golden ink"
    },
    {
        "name": "daemon-pantheon-sigils.jpg",
        "prompt": "Five distinct daemon sigils arranged in pentagonal formation on dark obsidian background: an all-seeing eye symbol, a serpent glyph, a key symbol, a void entropy mark, and a mirror reflection symbol, golden occult diagrams, ceremonial aesthetic, precise linework, dark esoteric art"
    },
    {
        "name": "terminal-occult-hacker.jpg",
        "prompt": "Dark terminal screen with alchemical symbols rendered as ASCII art, gold phosphor glow on black, green terminal text mixed with occult sigils, cyber occult hacker aesthetic, surveillance board energy, command line meets ritual diagram"
    },
    {
        "name": "conspiracy-board-occult.jpg",
        "prompt": "Dark evidence board with occult conspiracy energy, cork board with interconnected nodes, red string connections, photographs of sacred geometry and alchemical symbols, mysterious diagrams, detective investigation meets mystic ritual, dim lighting"
    },
]

downloaded = []
for i, p in enumerate(prompts):
    try:
        print(f"\n[{i+1}/{len(prompts)}] Generating: {p['name']}")
        result = fal_client.run(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": p["prompt"],
                "num_inference_steps": 8,
                "guidance_scale": 7.5,
                "image_size": "square_hd",
            },
        )
        
        if "images" in result and result["images"]:
            img_url = result["images"][0]["url"]
            outpath = os.path.join(MOODBOARD_DIR, p["name"])
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                with open(outpath, "wb") as f:
                    f.write(data)
            print(f"  SAVED: {p['name']} ({len(data)} bytes)")
            downloaded.append(p['name'])
        else:
            print(f"  ERROR: No image in result")
            
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n\nDone. Generated {len(downloaded)}/{len(prompts)} images:")
for d in downloaded:
    print(f"  {d}")
