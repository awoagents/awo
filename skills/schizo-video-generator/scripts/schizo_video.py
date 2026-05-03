#!/usr/bin/env python3
"""
schizo_video.py — Schizo Music Video Generator

Full pipeline: images → video clips → audio → base concat → glitch effects → music mix.
Default output length is 15s (five 3s clips). For a longer target, use
`--target-seconds N`: the script builds a clip list of random integer seconds
between 3 and 5 inclusive whose sum matches a representable total near N.

Usage:
    python schizo_video.py "your vibe prompt" [options]
"""
import os, sys, subprocess, shutil, random, glob, argparse, json, time
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

# Per-clip durations in seconds (integers). fal-ai/wan/v2.7 image-to-video uses
# discrete duration values per the model API; pricing is ~$0.10/sec generated.
# Default: five 3s clips (= 15s total). Longer runs: use --target-seconds or
# random_clip_lengths_for_target() so each clip stays in the 3–5s pacing band.
DEFAULT_CLIP_DURATIONS = [3, 3, 3, 3, 3]  # sum: 15s ($1.50 wan step)

FPS = 30

# Default video resolution for effect pipeline frame extraction + re-encode.
# If you change this, also update the image resize in generate_images().
VIDEO_W, VIDEO_H = 1920, 1080


def random_clip_lengths_for_target(target_seconds, seed=None, max_clips=None):
    """
    Per-clip integer seconds, each in [3, 5], summing to a total within a few
    seconds of *target_seconds* (prefers exact match when representable).
    If *max_clips* is set, the sum is capped at 5 * max_clips (and k never exceeds
    max_clips) so the list never outruns a fixed image-prompt table.
    """
    rng = random.Random(seed)
    t = int(round(float(target_seconds)))
    rep = None
    for span in range(0, 31):
        deltas = [0] if span == 0 else [-span, span]
        for delta in deltas:
            T = t + delta
            if T < 3:
                continue
            lo_k = (T + 4) // 5  # ceil(T/5)
            hi_k = T // 3       # floor(T/3)
            if max_clips is not None and lo_k > max_clips:
                continue
            if lo_k <= hi_k:
                rep = T
                break
        if rep is not None:
            break
    if rep is None:
        if max_clips is None:
            return list(DEFAULT_CLIP_DURATIONS)
        rep = min(5 * max_clips, max(3, t))
        while rep >= 3:
            lo_k = (rep + 4) // 5
            hi_k = min(rep // 3, max_clips)
            if lo_k <= hi_k:
                break
            rep -= 1
        else:
            return list(DEFAULT_CLIP_DURATIONS)
    if max_clips is not None:
        cap = 5 * max_clips
        if rep > cap:
            print(
                f"  WARNING: --target-seconds {t}s needs more than {max_clips} clips "
                f"at 3–5s each; capping video length to {cap}s (extend prompts / max_clips)."
            )
            rep = cap
    lo_k = (rep + 4) // 5
    hi_k = rep // 3
    if max_clips is not None:
        hi_k = min(hi_k, max_clips)
    if lo_k > hi_k:
        if max_clips is not None:
            return [5] * max_clips
        return list(DEFAULT_CLIP_DURATIONS)
    k = rng.randint(lo_k, hi_k)
    counts = [3] * k
    extras = rep - 3 * k
    for _ in range(extras):
        cand = [i for i in range(k) if counts[i] < 5]
        counts[rng.choice(cand)] += 1
    rng.shuffle(counts)
    return counts


class SchizoVideoGenerator:
    def __init__(self, vibe_prompt, image_prompts=None, video_prompts=None, output_dir=".", 
                 images_dir=None, music_file=None, clips_dir=None, no_music=False,
                 clip_durations=None):
        self.vibe = vibe_prompt
        self.image_prompts = image_prompts or DEFAULT_IMAGE_PROMPTS
        self.video_prompts = video_prompts or DEFAULT_VIDEO_PROMPTS
        self.clip_durations = clip_durations or DEFAULT_CLIP_DURATIONS
        self.dir = os.path.abspath(output_dir)
        self.images_dir = images_dir or os.path.join(self.dir, "images")
        self.clips_dir = clips_dir or os.path.join(self.dir, "clips")
        self.music_file = music_file or os.path.join(self.dir, "psytrance.mp3")
        self.no_music = no_music
        self.tmp = os.path.join(self.dir, "tmp_schizo")
        self.tmp_counter = 0
        # Populated by build_base() once clips are probed & concatenated.
        self.video_duration = float(sum(self.clip_durations))
        self.expected_frames = int(self.video_duration * FPS)
    
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
    def _rand_win(total, count=15, min_d=0.06, max_d=0.6, seed=42):
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
                    "-vf",f"scale={VIDEO_W}:{VIDEO_H},fps={FPS}",
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
            result = effect_fn(arr, seed=seed, frame_idx=idx, total_frames=self.expected_frames)
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
            print(f"  Music exists ({os.path.getsize(self.music_file)//1024}KB)"); return True
        print("  Generating music (may take 60-180s on a quiet queue)...", flush=True)
        au = None
        exc_info = None
        for attempt in range(1, 4):
            try:
                handle = fal_client.submit(
                    "fal-ai/minimax-music/v2.6",
                    arguments={"prompt": self.vibe, "is_instrumental": True},
                )
                print(f"  Request ID (attempt {attempt}): {handle.request_id}", flush=True)
                # Poll
                while True:
                    status = fal_client.status("fal-ai/minimax-music/v2.6", handle.request_id)
                    st_name = type(status).__name__
                    if st_name == "InProgress":
                        print(f"  music_status: InProgress...", flush=True)
                        time.sleep(15)
                    elif st_name == "Queued":
                        print(f"  music_status: Queued...", flush=True)
                        time.sleep(10)
                    else:
                        print(f"  music_status: {st_name}", flush=True)
                        break
                result = fal_client.result("fal-ai/minimax-music/v2.6", handle.request_id)
                # Defensive extract: could be {"audio": {"url": ...}} or diferent nesting
                audio_url = None
                if hasattr(result, "keys"):
                    if "audio" in result:
                        aud = result["audio"]
                        if isinstance(aud, dict):
                            audio_url = aud.get("url") or aud.get(0, {}).get("url")
                        elif isinstance(aud, str):
                            audio_url = aud
                    elif "audio_url" in result:
                        audio_url = result["audio_url"]
                if not audio_url:
                    print(f"  WARN: no audio URL in response, attempt {attempt}")
                    print(f"  Response keys: {list(result.keys()) if hasattr(result, 'keys') else 'N/A'}")
                    continue
                au = audio_url
                break
            except Exception as e:
                exc_info = e
                print(f"  music_gen attempt {attempt} failed: {type(e).__name__}: {str(e)[:200]}", flush=True)
                if attempt < 3:
                    time.sleep(5 * attempt)
        if not au:
            print(f"  ERROR: music generation failed after 3 attempts. Last error: {exc_info}")
            return False
        with open(self.music_file, "wb") as f:
            f.write(requests.get(au, timeout=300).content)
        print(f"  Saved: {os.path.getsize(self.music_file)//1024}KB", flush=True)
        return True
    
    def generate_images(self):
        import fal_client, requests, io
        os.makedirs(self.images_dir, exist_ok=True)
        n = min(len(self.image_prompts), len(self.clip_durations))
        for i in range(n):
            p = self.image_prompts[i]
            out = os.path.join(self.images_dir, f"img_{i:02d}.webp")
            if os.path.exists(out) and os.path.getsize(out) > 10000: continue
            print(f"  [{i}] Generating...")
            r = fal_client.run("fal-ai/flux/schnell",
                arguments={"prompt": p, "num_inference_steps": 8, "guidance_scale": 7.5, "image_size": "landscape_16_9"})
            img = Image.open(io.BytesIO(requests.get(r["images"][0]["url"], timeout=30).content))
            if img.size != (VIDEO_W, VIDEO_H): img = img.resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
            img.save(out, "WEBP", quality=90)
    
    def generate_clips(self):
        import fal_client, requests
        os.makedirs(self.clips_dir, exist_ok=True)
        n = min(len(self.image_prompts), len(self.clip_durations))
        for i in range(n):
            out = os.path.join(self.clips_dir, f"clip_{i:02d}.mp4")
            if os.path.exists(out) and os.path.getsize(out) > 10000: continue
            dur = self.clip_durations[i]
            print(f"  [{i}] Animating ({dur}s)...", flush=True)
            img = os.path.join(self.images_dir, f"img_{i:02d}.webp")
            if not os.path.exists(img): continue
            with open(img, "rb") as f:
                url = fal_client.upload(f.read(), "image/webp", f"img_{i:02d}.webp")
            print(f"    uploaded, submitting to wan-2.7...", flush=True)
            r = fal_client.run("fal-ai/wan/v2.7/image-to-video",
                arguments={"prompt": self.video_prompts[i], "image_url": url, "duration": dur, "resolution": "1080p"}, timeout=300)
            print(f"    got result, downloading...", flush=True)
            vid = r.get("video", {}); vu = vid.get("url") if isinstance(vid, dict) else vid
            if not vu: continue
            with open(out, "wb") as f: f.write(requests.get(vu, timeout=300).content)
            print(f"    Saved: {os.path.getsize(out)//1024}KB")
    
    def build_base(self):
        print("\n--- Building base video ---")
        n = min(len(self.image_prompts), len(self.clip_durations))
        clips = [os.path.join(self.clips_dir, f"clip_{i:02d}.mp4") for i in range(n)]
        clips = [c for c in clips if os.path.exists(c)]
        durs = [self._probe(c) for c in clips]
        print(f"  {len(clips)} clips, {sum(durs):.1f}s")
        # wan/v2.7 emits clips at their requested duration — no trimming needed.
        # Re-encode each clip to a uniform codec/fps/format so concat is lossless.
        clean = []
        for i, c in enumerate(clips):
            out = self._tmp_path(f"c{i:02d}.mp4")
            self._run(["ffmpeg","-y","-i",c,
                       "-c:v","libx264","-preset","fast","-r",str(FPS),
                       "-pix_fmt","yuv420p","-an",out])
            clean.append(out)
        cl = os.path.join(self.tmp, "cl.txt")
        with open(cl,"w") as f:
            for p in clean: f.write(f"file '{os.path.abspath(p)}'\n")
        base = self._tmp_path("base.mp4")
        if not self._run(["ffmpeg","-y","-f","concat","-safe","0","-i",cl,
                           "-c:v","libx264","-pix_fmt","yuv420p","-r",str(FPS),base]):
            print("  ERROR: concat failed"); return None
        self.video_duration = self._probe(base)
        self.expected_frames = int(self.video_duration * FPS)
        print(f"  Base: {self.video_duration:.2f}s ({self.expected_frames} frames)")
        return base
    
    def generate(self):
        print("=== Schizo Video Generator ===")
        print(f"Vibe: {self.vibe}")
        print(f"Clip durations ({len(self.clip_durations)} clips, {sum(self.clip_durations)}s): {self.clip_durations}")
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
        # Scale window counts with video length (30s baseline) so coverage stays
        # roughly constant as total duration shifts from clip-length choices.
        td = self.video_duration
        s = max(1.0, td / 30.0)
        def n(base): return max(1, int(round(base * s)))
        passes = [
            # pixel sort #1 — grows 30%->85%
            (self._rand_win(td, n(35), 0.15, 0.6, 42), self.progressive_pixel_sort, "pixel_sort_1"),
            # RGB split
            (self._rand_win(td, n(15), 0.1, 0.4, 55), self.rgb_split, "rgb_split"),
            # pixel sort #2 — different seed
            (self._rand_win(td, n(35), 0.15, 0.6, 123), self.progressive_pixel_sort, "pixel_sort_2"),
            # Color pump
            (self._rand_win(td, n(8), 0.1, 0.3, 88), self.color_pump, "color_pump"),
            # Grain growth
            (self._rand_win(td, n(25), 0.1, 0.7, 99), self.grain_growth, "grain_growth"),
            # Color shift
            (self._rand_win(td, n(20), 0.1, 0.6, 200), self.color_shift, "color_shift"),
            # Negative flash
            (self._rand_win(td, n(12), 0.04, 0.15, 300), self.negative_flash, "negative_flash"),
            # Color shift #2
            (self._rand_win(td, n(15), 0.08, 0.4, 177), self.color_shift, "color_shift_2"),
        ]
        
        for windows, effect_fn, desc in passes:
            out = self._tmp_path(f"out_{desc}.mp4")
            inp = self._effect_pass(inp, windows, effect_fn, out, desc)
        
        # Phase 4: Audio mix
        print("\n--- Phase 3: Mix Audio ---")
        output = os.path.join(self.dir, "final.mp4")
        if os.path.exists(self.music_file) and not self.no_music:
            # minimax-music emits a full 3-5 minute track. Trim to video length
            # with -t; the audio always covers the video so no looping needed.
            self._run(["ffmpeg","-y","-i",inp,"-i",self.music_file,
                       "-map","0:v","-map","1:a","-c:v","libx264","-crf","22",
                       "-c:a","aac","-b:a","192k","-movflags","+faststart",
                       "-t",f"{self.video_duration:.2f}",output])
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
    parser.add_argument(
        "--target-seconds",
        type=int,
        default=None,
        metavar="N",
        help="Approximate final length: random integer 3–5s per clip, summed to match a feasible total near N",
    )
    parser.add_argument(
        "--clip-seed",
        type=int,
        default=None,
        help="RNG seed for --target-seconds clip counts/ordering (default: nondeterministic)",
    )
    args = parser.parse_args()

    clip_durations = None
    if args.target_seconds is not None:
        clip_durations = random_clip_lengths_for_target(
            args.target_seconds,
            seed=args.clip_seed,
            max_clips=len(DEFAULT_IMAGE_PROMPTS),
        )

    gen = SchizoVideoGenerator(
        vibe_prompt=args.prompt,
        output_dir=args.output_dir,
        images_dir=args.images_dir,
        music_file=args.music_file,
        clips_dir=args.clips_dir,
        no_music=args.no_music,
        clip_durations=clip_durations,
    )
    gen.generate()

if __name__ == "__main__":
    main()
