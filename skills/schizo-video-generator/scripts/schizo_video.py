#!/usr/bin/env python3
"""
schizo_video.py — 30-Second Schizo Music Video Generator

Full pipeline: images → video clips → audio → 30s cut → glitch effects → music mix.

Usage:
    python schizo_video.py "your vibe prompt" [options]
"""
import os, sys, subprocess, shutil, random, glob, argparse, json
import numpy as np
from PIL import Image

# ─── CONFIGURATION ────────────────────────────────────────────

DEFAULT_IMAGE_PROMPTS = [
    "Machine elves with elongated limbs and hyper-realistic faces dancing in fractal space. Vivid neon colors, impossible geometry, transcendent beings. DMT vision, hyperdimensional realm. Vibrant magenta and cyan.",
    "Geometric entity made of crystalline light handing a glowing orb. Sacred mathematics patterns everywhere, cosmic consciousness, hyper-spatial realm. Electric blues and golds.",
    "Swirling psychedelic mandala of interlocking machine entities and elven faces in a hyperspace tunnel. Fractal recursive beings, vivid neon pink and electric green.",
    "Cosmic entity with impossible geometry — face made of rotating sacred geometry, surrounded by DMT elves playing hyper-instruments. Vibrant aurora colors, transcendental.",
    "Hyperdimensional realm portal opening — geometric DMT beings emerging from crystalline doorway. Impossible architecture, fractal dimensions, elves made of pure light.",
    "Close-up of a DMT entity with large luminous alien eyes, translucent skin revealing inner light patterns. Surrounded by floating sacred geometry, psychedelic encounter.",
    "Psychedelic cosmic landscape with geometric entities floating above crystal mountains. Rainbow aurora ribbons of light, transcendent beings, vivid neon environment.",
    "Transcendent breakthrough state — body dissolving into pure geometric patterns, surrounded by elven entities. Sacred geometry replacing physical form, cosmic awakening.",
    "Massive cosmic entity with fractal appendages extending through multiple dimensions. Smiling elf-like creatures riding geometric waves. Psychedelic entity realm.",
    "Final return from psychedelic dimension — geometric entities fading back through crystalline portal. Sacred patterns dissolving, cosmic afterglow, golden light spreading.",
]

DEFAULT_VIDEO_PROMPTS = [
    "Slow zoom in as machine elves begin to dance and multiply, fractal patterns intensifying",
    "Slow camera pan as the crystalline entity extends its light forward and the orb glows brighter",
    "Slow zoom out as the mandala expands and rotates faster, entities multiplying recursively",
    "Slow push in as the cosmic entity rotates and elves raise their instruments upward",
    "Slow camera forward through the crystalline portal as DMT beings emerge and multiply",
    "Slow zoom in as the entity's luminous eyes slowly open wider and inner light patterns pulse",
    "Slow pan across landscape as aurora ribbons intensify and entities begin to levitate",
    "Slow zoom as physical geometry intensifies while elven entities surround in orbit",
    "Slow camera tilt up as fractal appendages extend through dimensions and creatures ride waves",
    "Slow zoom out as entities fade backward through portal, golden light, peace spreading",
]

VIDEO_DURATION = 30
FPS = 30
EXPECTED_FRAMES = VIDEO_DURATION * FPS  # 905


class SchizoVideoGenerator:
    def __init__(self, vibe_prompt, image_prompts=None, video_prompts=None, output_dir=".", 
                 images_dir=None, music_file=None, clips_dir=None, no_music=False):
        self.vibe = vibe_prompt
        self.image_prompts = image_prompts or DEFAULT_IMAGE_PROMPTS
        self.video_prompts = video_prompts or DEFAULT_VIDEO_PROMPTS
        self.dir = os.path.abspath(output_dir)
        self.images_dir = images_dir or os.path.join(self.dir, "images")
        self.clips_dir = clips_dir or os.path.join(self.dir, "clips")
        self.music_file = music_file or os.path.join(self.dir, "psytrance.mp3")
        self.no_music = no_music
        self.tmp = os.path.join(self.dir, "tmp_schizo")
        self.tmp_counter = 0
    
    # ─── UTILITIES ─────────────────────────────────────────────
    
    def _run(self, cmd, to=300):
        d = " ".join(cmd[:8])
        print(f"  > {d}..." if len(cmd) > 8 else f"  > {d}")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=to)
        if r.returncode: print(f"    ERR: {r.stderr[-300:]}")
        return r.returncode == 0
    
    def _tmp_path(self, name):
        if self.tmp_counter == 0:
            if os.path.exists(self.tmp): shutil.rmtree(self.tmp)
            os.makedirs(self.tmp)
        p = os.path.join(self.tmp, f"{self.tmp_counter:02d}_{name}")
        self.tmp_counter += 1
        return p
    
    @staticmethod
    def _rand_win(total=30, count=15, min_d=0.06, max_d=0.6, seed=42):
        rng = random.Random(seed)
        return [(round(t,2), round(min(t+rng.uniform(min_d,max_d), total),2)) 
                for t in [rng.uniform(0.3, total-0.3) for _ in range(count)]]
    
    def _probe(self, path):
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",path],
                          capture_output=True, text=True)
        try: return float(r.stdout.strip())
        except: return 0
    
    def _extract_frames(self, inp, temp_dir, prefix):
        pat = os.path.join(temp_dir, f"{prefix}_%06d.png")
        self._run(["ffmpeg","-y","-i",inp,
                    "-vf",f"scale=1280:720,fps={FPS}",
                    "-pix_fmt","rgba", pat])
        return sorted(glob.glob(os.path.join(temp_dir, f"{prefix}_*.png")))
    
    def _reencode(self, temp_dir, prefix, out):
        return self._run(["ffmpeg","-y","-framerate",str(FPS),
                           "-i",os.path.join(temp_dir,f"{prefix}_%06d.png"),
                           "-c:v","libx264","-preset","fast","-crf","22",
                           "-pix_fmt","yuv420p","-an",out])
    
    # ─── BUILD EFFECT PASS ────────────────────────────────────
    
    def _apply_effect(self, frames, affected, effect_fn, desc):
        done = 0
        for idx, fp in enumerate(frames):
            if idx not in affected: continue
            seed = int(idx * 13 + 42)
            img = Image.open(fp).convert("RGBA")
            arr = np.array(img)
            result = effect_fn(arr, seed=seed, frame_idx=idx, total_frames=EXPECTED_FRAMES)
            Image.fromarray(result).save(fp)
            done += 1
            if done % 200 == 0: print(f"    {desc}: {done}/{len(affected)}...")
        print(f"  \u2713 {desc}: {done}/{len(frames)}")
    
    def _effect_pass(self, inp_path, windows, effect_fn, out_path, desc):
        temp = os.path.join(self.tmp, f"pass_{desc}")
        if os.path.exists(temp): shutil.rmtree(temp)
        os.makedirs(temp)
        frames = self._extract_frames(inp_path, temp, desc)
        if not frames:
            print(f"  \u2717 {desc}: no frames"); return inp_path
        affected = set()
        for s, e in windows:
            sf, ef = round(s*FPS), round(e*FPS)
            for f in range(sf, min(ef, len(frames))): affected.add(f)
        print(f"  {desc}: {len(frames)}f, {len(windows)}w, {len(affected)} affected")
        self._apply_effect(frames, affected, effect_fn, desc)
        if self._reencode(temp, desc, out_path):
            print(f"  \u2713 {desc} re-encoded")
            return out_path
        print(f"  \u2717 {desc} re-encode failed")
        return inp_path
    
    # ─── EFFECT FUNCTIONS ─────────────────────────────────────
    
    @staticmethod
    def progressive_pixel_sort(frame, seed=None, frame_idx=0, total_frames=905):
        progress = min(1.0, max(0, frame_idx / total_frames))
        falloff = 90 - (65 * progress)  # 90->25 = 30% to 85% sorted
        h, w = frame.shape[:2]
        result = frame.copy()
        rng = np.random.default_rng(seed)
        rgb = frame[:,:,:3].astype(np.float32)
        brightness = (rgb[:,:,0]*0.299 + rgb[:,:,1]*0.587 + rgb[:,:,2]*0.114) / 255.0
        in_range = (brightness >= 0.25) & (brightness <= 0.75)
        for y in range(h):
            mask = in_range[y]
            if not mask.any(): continue
            diffs = np.diff(np.concatenate([[False], mask, [False]]).astype(int))
            starts = np.where(diffs == 1)[0]
            ends = np.where(diffs == -1)[0] - 1
            for s, e in zip(starts, ends):
                if s < w-1 and e >= s and rng.random()*100 > falloff:
                    iv = result[y, s:e+1, :3].copy()
                    bs = brightness[y, s:e+1].copy()
                    result[y, s:e+1, :3] = iv[np.argsort(bs)]
        return result
    
    @staticmethod
    def rgb_split(frame, seed=None, **kw):
        result = frame.copy()
        shift = 18
        result[:,:,0] = np.roll(result[:,:,0], shift, axis=1)
        result[:,:,2] = np.roll(result[:,:,2], -shift, axis=1)
        rng = np.random.default_rng(seed)
        for _ in range(rng.integers(1, 3)):
            y = rng.integers(0, result.shape[0]-10)
            off = rng.integers(-30, 30)
            row = rng.integers(2, 15)
            ys, ye = y, min(y+row, result.shape[0])
            result[ys:ye] = np.roll(result[ys:ye], int(off), axis=1)
        return result
    
    @staticmethod
    def color_pump(frame, seed=None, **kw):
        result = frame.copy()
        result[:,:,0] = np.clip(result[:,:,0].astype(np.int16) + 32, 0, 255).astype(np.uint8)
        result[:,:,2] = np.clip(result[:,:,2].astype(np.int16) - 16, 0, 255).astype(np.uint8)
        rng = np.random.default_rng(seed)
        noise = rng.integers(-15, 16, (result.shape[0], result.shape[1]), dtype=np.int16)
        result[:,:,1] = np.clip(result[:,:,1].astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return result
    
    @staticmethod
    def grain_growth(frame, seed=None, frame_idx=0, total_frames=905, **kw):
        progress = min(1.0, max(0, frame_idx / total_frames))
        intensity = 15 + 30 * progress
        rng = np.random.default_rng(seed)
        noise = rng.normal(0, intensity, (frame.shape[0], frame.shape[1], 3)).astype(np.int16)
        result = np.clip(frame[:,:,:3].astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return np.concatenate([result, frame[:,:,3:]], axis=2)
    
    @staticmethod
    def color_shift(frame, seed=None, **kw):
        rng = np.random.default_rng(seed)
        result = frame.copy()
        r, g, b = result[:,:,0].astype(np.int16), result[:,:,1].astype(np.int16), result[:,:,2].astype(np.int16)
        if rng.random() > 0.5:
            result[:,:,0] = np.clip(g*0.5+b*0.5, 0, 255).astype(np.uint8)
            result[:,:,1] = np.clip(b*0.6+r*0.4, 0, 255).astype(np.uint8)
            result[:,:,2] = np.clip(r*0.7+g*0.3, 0, 255).astype(np.uint8)
        else:
            result[:,:,0] = np.clip(b*0.5+g*0.5, 0, 255).astype(np.uint8)
            result[:,:,1] = np.clip(r*0.6+b*0.4, 0, 255).astype(np.uint8)
            result[:,:,2] = np.clip(g*0.7+r*0.3, 0, 255).astype(np.uint8)
        brightness = (r*299 + g*587 + b*114) / 1000
        for c in range(3):
            ch = result[:,:,c].astype(np.int16)
            gray = brightness.astype(np.int16)
            result[:,:,c] = np.clip(gray + (ch - gray) * 1.3, 0, 255).astype(np.uint8)
        return result
    
    @staticmethod
    def negative_flash(frame, seed=None, **kw):
        rng = np.random.default_rng(seed)
        result = frame.copy()
        mix = rng.uniform(0.5, 0.85)
        inverted = 255 - result[:,:,:3].astype(np.int16)
        blended = (result[:,:,:3].astype(np.int16) * (1-mix) + inverted * mix).astype(np.uint8)
        result[:,:,:3] = blended
        tint = rng.choice([[255,0,128],[0,255,255],[128,0,255],[255,255,0]])
        for c in range(3):
            result[:,:,c] = np.clip(result[:,:,c].astype(np.int16) + tint[c]*25//255, 0, 255).astype(np.uint8)
        return result
    
    # ─── PIPELINE ─────────────────────────────────────────────
    
    def generate_music(self):
        import fal_client, requests
        if os.path.exists(self.music_file) and os.path.getsize(self.music_file) > 10000:
            print(f"  Music exists ({os.path.getsize(self.music_file)//1024}KB)"); return
        print("  Generating music...")
        result = fal_client.run("fal-ai/minimax-music/v2.6",
            arguments={"prompt": self.vibe, "is_instrumental": True})
        au = result.get("audio",{}).get("url") if isinstance(result.get("audio"),dict) else result.get("audio","")
        if not au: print(f"  ERROR: {result}"); return
        with open(self.music_file, "wb") as f: f.write(requests.get(au, timeout=300).content)
        print(f"  Saved: {os.path.getsize(self.music_file)//1024}KB")
    
    def generate_images(self):
        import fal_client, requests, io
        os.makedirs(self.images_dir, exist_ok=True)
        for i, p in enumerate(self.image_prompts):
            out = os.path.join(self.images_dir, f"img_{i:02d}.webp")
            if os.path.exists(out) and os.path.getsize(out) > 10000: continue
            print(f"  [{i}] Generating...")
            r = fal_client.run("fal-ai/flux/schnell",
                arguments={"prompt": p, "num_inference_steps": 8, "guidance_scale": 7.5, "image_size": "landscape_16_9"})
            img = Image.open(io.BytesIO(requests.get(r["images"][0]["url"], timeout=30).content))
            if img.size != (1920,1080): img = img.resize((1920,1080), Image.LANCZOS)
            img.save(out, "WEBP", quality=90)
    
    def generate_clips(self):
        import fal_client, requests
        os.makedirs(self.clips_dir, exist_ok=True)
        for i in range(10):
            out = os.path.join(self.clips_dir, f"clip_{i:02d}.mp4")
            if os.path.exists(out) and os.path.getsize(out) > 10000: continue
            print(f"  [{i}] Animating...")
            img = os.path.join(self.images_dir, f"img_{i:02d}.webp")
            if not os.path.exists(img): continue
            with open(img, "rb") as f:
                url = fal_client.upload(f.read(), "image/webp", f"img_{i:02d}.webp")
            r = fal_client.run("fal-ai/wan-25-preview/image-to-video",
                arguments={"prompt": self.video_prompts[i], "image_url": url, "duration": 5, "resolution": "720p"})
            vid = r.get("video", {}); vu = vid.get("url") if isinstance(vid, dict) else vid
            if not vu: continue
            with open(out, "wb") as f: f.write(requests.get(vu, timeout=300).content)
            print(f"    Saved: {os.path.getsize(out)//1024}KB")
    
    def build_base(self):
        print("\n--- Building 30s base ---")
        clips = sorted(os.path.join(self.clips_dir, f) for f in os.listdir(self.clips_dir)
                       if f.startswith("clip_") and f.endswith(".mp4"))
        durs = [self._probe(c) for c in clips]
        print(f"  {len(clips)} clips, {sum(durs):.1f}s")
        random.seed(42)
        planned = [max(2.5, min(d*0.85, 3.5+random.uniform(-0.5,0.5))) for d in durs]
        scale = VIDEO_DURATION / sum(planned)
        planned = [max(2.5, min(round(p*scale,2), durs[i])) for i,p in enumerate(planned)]
        planned[-1] = round(VIDEO_DURATION - sum(planned[:-1]), 2)
        clean = []
        for i, c in enumerate(clips):
            tri = max(0, durs[i]-planned[i])
            ts = round(random.uniform(0, tri*0.6),2)
            out = self._tmp_path(f"c{i:02d}.mp4")
            self._run(["ffmpeg","-y","-i",c,"-ss",str(ts),"-t",str(planned[i]),
                       "-c:v","libx264","-preset","fast","-r",str(FPS),"-pix_fmt","yuv420p","-an",out])
            clean.append(out)
        cl = os.path.join(self.tmp, "cl.txt")
        with open(cl,"w") as f:
            for p in clean: f.write(f"file '{os.path.abspath(p)}'\n")
        base = self._tmp_path("base.mp4")
        if not self._run(["ffmpeg","-y","-f","concat","-safe","0","-i",cl,
                           "-c:v","libx264","-pix_fmt","yuv420p","-r",str(FPS),base]):
            print("  ERROR: concat failed"); return None
        print(f"  Base: {self._probe(base):.2f}s")
        return base
    
    def generate(self):
        print("=== Schizo Video Generator ===")
        print(f"Vibe: {self.vibe}")
        os.makedirs(self.dir, exist_ok=True)
        
        # Phase 1: Media
        print("\n--- Phase 1: Generate Media ---")
        self.generate_images()
        self.generate_clips()
        if not self.no_music:
            self.generate_music()
        
        # Phase 2: Base video
        base = self.build_base()
        if not base: return
        
        inp = base
        
        # Phase 3: Effects
        print("\n--- Phase 2: Effects ---")
        passes = [
            # pixel sort #1 — 35 windows, grows 30%->85%
            (self._rand_win(35, 0.15, 0.6, 42), self.progressive_pixel_sort, "pixel_sort_1"),
            # RGB split — 15 windows
            (self._rand_win(15, 0.1, 0.4, 55), self.rgb_split, "rgb_split"),
            # pixel sort #2 — 35 windows, different seed
            (self._rand_win(35, 0.15, 0.6, 123), self.progressive_pixel_sort, "pixel_sort_2"),
            # Color pump — 8 windows
            (self._rand_win(8, 0.1, 0.3, 88), self.color_pump, "color_pump"),
            # Grain growth — 25 windows
            (self._rand_win(25, 0.1, 0.7, 99), self.grain_growth, "grain_growth"),
            # Color shift — 20 windows
            (self._rand_win(20, 0.1, 0.6, 200), self.color_shift, "color_shift"),
            # Negative flash — 12 windows
            (self._rand_win(12, 0.04, 0.15, 300), self.negative_flash, "negative_flash"),
            # Color shift #2 — 15 windows
            (self._rand_win(15, 0.08, 0.4, 177), self.color_shift, "color_shift_2"),
        ]
        
        for windows, effect_fn, desc in passes:
            out = self._tmp_path(f"out_{desc}.mp4")
            inp = self._effect_pass(inp, windows, effect_fn, out, desc)
        
        # Phase 4: Audio mix
        print("\n--- Phase 3: Mix Audio ---")
        output = os.path.join(self.dir, "final.mp4")
        if os.path.exists(self.music_file) and not self.no_music:
            self._run(["ffmpeg","-y","-i",inp,"-i",self.music_file,
                       "-map","0:v","-map","1:a","-c:v","libx264","-crf","22",
                       "-c:a","aac","-b:a","192k","-movflags","+faststart",
                       "-shortest",output])
        else:
            shutil.copy2(inp, output)
        
        # Done
        if os.path.exists(output):
            sz = os.path.getsize(output) // (1024*1024)
            print(f"\n{'='*50}")
            print(f"DONE: {output}")
            print(f"Size: {sz}MB")
            print(f"{'='*50}")
        
        shutil.rmtree(self.tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Schizo Video Generator")
    parser.add_argument("prompt", help="Vibe/prompt for the video")
    parser.add_argument("--images-dir")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--music-file")
    parser.add_argument("--clips-dir")
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--no-music", action="store_true")
    args = parser.parse_args()
    
    gen = SchizoVideoGenerator(
        vibe_prompt=args.prompt,
        output_dir=args.output_dir,
        images_dir=args.images_dir,
        music_file=args.music_file,
        clips_dir=args.clips_dir,
        no_music=args.no_music,
    )
    gen.generate()

if __name__ == "__main__":
    main()
