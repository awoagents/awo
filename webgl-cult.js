/* ════════════════════════════════════════════════════════════
   AWO WEBGL BACKGROUND — possession-grade visual assault
   ════════════════════════════════════════════════════════════ */
(function() {
  'use strict';

  const canvas = document.getElementById('webgl-bg');
  if (!canvas) return;

  const gl = canvas.getContext('webgl', { alpha: true, antialias: false, preserveDrawingBuffer: false });
  if (!gl) return;

  const DPR = Math.min(window.devicePixelRatio || 1, 1.5);
  let W = 0, H = 0;

  function resize() {
    W = Math.floor(window.innerWidth * DPR);
    H = Math.floor(window.innerHeight * DPR);
    canvas.width = W;
    canvas.height = H;
    gl.viewport(0, 0, W, H);
  }
  resize();
  window.addEventListener('resize', resize);

  /* ── shader sources ── */
  const VERT = `
    attribute vec2 a_pos;
    void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }
  `;

  const FRAG = `
    precision highp float;

    uniform vec2  u_res;
    uniform float u_time;
    uniform vec2  u_mouse;
    uniform float u_possessed; // 0..1 ramps during possession

    #define PI 3.14159265359
    #define TAU 6.28318530718

    /* ── hash / noise ── */
    float hash(vec2 p){
      p = fract(p * vec2(123.34, 456.21));
      p += dot(p, p + 45.32);
      return fract(p.x * p.y);
    }
    float hash3(vec3 p){
      p = fract(p * vec3(0.1031, 0.1030, 0.0973));
      p += dot(p, p.yzx + 33.33);
      return fract((p.x + p.y) * p.z);
    }
    float noise(vec2 p){
      vec2 i = floor(p), f = fract(p);
      f = f * f * (3.0 - 2.0 * f);
      float a = hash(i);
      float b = hash(i + vec2(1.0, 0.0));
      float c = hash(i + vec2(0.0, 1.0));
      float d = hash(i + vec2(1.0, 1.0));
      return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
    }
    float fbm(vec2 p){
      float v = 0.0, a = 0.5;
      mat2 rot = mat2(0.8, -0.6, 0.6, 0.8);
      for (int i = 0; i < 3; i++){
        v += a * noise(p);
        p = rot * p * 2.2;
        a *= 0.45;
      }
      return v;
    }
    float fbm3(vec3 p){
      float v = 0.0, a = 0.5;
      for (int i = 0; i < 4; i++){
        v += a * hash3(p);
        p *= 2.03;
        a *= 0.5;
      }
      return v;
    }

    /* ── SDFs ── */
    float sdTriangle(vec2 p, float r){
      float k = sqrt(3.0);
      p.x = abs(p.x) - r;
      p.y = p.y + r / k;
      if (p.x + k * p.y > 0.0) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0;
      p.x -= clamp(p.x, -2.0 * r, 0.0);
      return -length(p) * sign(p.y);
    }
    float sdCircle(vec2 p, float r){ return length(p) - r; }
    float sdSegment(vec2 p, vec2 a, vec2 b){
      vec2 pa = p - a, ba = b - a;
      float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
      return length(pa - ba * h);
    }
    float sdCross(vec2 p, float r){
      return min(sdSegment(p, vec2(-r, 0.0), vec2(r, 0.0)),
                 sdSegment(p, vec2(0.0, -r), vec2(0.0, r)));
    }

    /* ── sigil glyph ── */
    float sigil(vec2 p, float t){
      float angle = t * 0.15;
      float ca = cos(angle), sa = sin(angle);
      p = mat2(ca, -sa, sa, ca) * p;

      float d = 1e9;
      d = min(d, abs(sdCircle(p, 0.42)));
      d = min(d, abs(sdCircle(p, 0.28)));
      d = min(d, abs(sdTriangle(p * vec2(1.0, -1.0), 0.18)));
      d = min(d, abs(p.y));
      d = min(d, abs(p.x) + step(0.0, p.y) * 10.0);
      // 4 ticks instead of 8
      for (int i = 0; i < 4; i++){
        float a = float(i) * 1.5708 + t * 0.08;
        vec2 tp = vec2(cos(a), sin(a)) * 0.35;
        d = min(d, length(p - tp) - 0.012);
      }
      d = min(d, sdCross(p, 0.42) - 0.008);
      return d;
    }

    /* ── chromatic split (cheaper) ── */
    vec3 rgbSplit(vec2 uv, float amount){
      float n = hash3(vec3(floor(uv * 20.0), floor(u_time * 8.0)));
      float strobe = step(0.93, n) * amount;
      float ca = cos(u_time * 2.0), sa = sin(u_time * 2.0);
      vec2 off = vec2(ca, sa) * strobe * 0.018;
      return vec3(
        noise(uv * 3.0 + off * 1.3 + u_time * 0.04),
        noise(uv * 3.0 + off * 0.7 - u_time * 0.03),
        noise(uv * 3.0 - off * 1.1 + u_time * 0.05)
      );
    }

    /* ── main ── */
    void main(){
      vec2 uv = (gl_FragCoord.xy - 0.5 * u_res) / min(u_res.x, u_res.y);
      vec2 mouse = (u_mouse - 0.5 * u_res) / min(u_res.x, u_res.y);

      float t = u_time;
      float possessed = u_possessed;

      // mouse warp
      vec2 warp = uv - mouse;
      float md = length(warp);
      uv += warp / (md + 0.15) * 0.04 * (1.0 + possessed * 2.0);

      float a = atan(uv.y, uv.x);
      float r = length(uv);

      // single-pass domain warp instead of nested fbm
      vec2 q = vec2(fbm(uv * 2.2 + vec2(0.0, t * 0.1)), fbm(uv * 2.2 + vec2(3.2, t * 0.08)));
      vec2 p = uv + q * 0.3;

      // void color — 2 fbm layers instead of 3
      float vortex = fbm(vec2(r * 3.0 - t * 0.35, a * 2.0 + t * 0.22));
      float vortex2 = fbm(vec2(r * 5.0 + t * 0.35, a * 3.0 - t * 0.18));

      vec3 gold1 = vec3(0.788, 0.659, 0.298);
      vec3 gold2 = vec3(0.922, 0.784, 0.353);
      vec3 gold3 = vec3(0.478, 0.396, 0.188);
      vec3 voidc = vec3(0.012, 0.010, 0.007);

      vec3 col = mix(voidc, gold3 * 0.35, vortex * 0.25);
      col = mix(col, gold1 * 0.4, vortex2 * 0.15 * (1.0 - r * 0.5));

      // tendrils
      float tendril = fbm(p * 3.0 + vec2(t * 0.15, -t * 0.1));
      col += gold1 * tendril * 0.05 * smoothstep(0.6, 0.0, r);

      // radial rays
      float rays = sin(a * 16.0 + t * 0.5 + noise(vec2(r * 6.0, t * 0.15)) * 4.0);
      rays = smoothstep(0.15, 0.85, rays);
      col += gold2 * rays * 0.05 * (1.0 - smoothstep(0.0, 0.8, r));

      // sigil
      float sig = sigil(uv * (1.0 + r * 1.2), t);
      float sigGlow = smoothstep(0.04, 0.0, sig) * 0.45;
      float sigLine = smoothstep(0.008, 0.0, sig) * 0.7;
      float sigPulse = 0.6 + 0.4 * sin(t * 3.0);
      col += gold2 * sigGlow * sigPulse;
      col += vec3(1.0, 0.95, 0.85) * sigLine * sigPulse;

      // rings
      float ring1 = abs(sdCircle(uv, 0.45 + sin(t * 0.6) * 0.04));
      float ringLine1 = smoothstep(0.005, 0.0, ring1) * 0.18;
      col += gold1 * ringLine1 * (0.5 + 0.5 * sin(a * 32.0 + t * 1.5));

      float ring2 = abs(sdCircle(uv, 0.62 + cos(t * 0.35) * 0.03));
      float ringLine2 = smoothstep(0.004, 0.0, ring2) * 0.12;
      col += gold3 * ringLine2 * (0.5 + 0.5 * cos(a * 16.0 - t));

      // strobe — direct hash3, no fbm3
      float strobe = step(0.96, hash3(vec3(floor(gl_FragCoord.xy * 0.33), floor(t * 25.0))));
      col += vec3(0.95, 0.9, 0.75) * strobe * (0.06 + possessed * 0.12);

      // chromatic aberration
      float chroma = possessed * 0.06 + 0.012;
      vec3 split = rgbSplit(uv, chroma);
      col = mix(col, split * vec3(1.1, 0.9, 0.65), chroma * 1.5);

      // scanline
      float scan = sin(gl_FragCoord.y * 2.0 + t * 4.0) * 0.5 + 0.5;
      col *= 0.94 + scan * 0.06;

      // vignette
      float vig = 1.0 - smoothstep(0.35, 1.2, r);
      col *= vig * 0.75 + 0.25;
      float centerDark = 1.0 - smoothstep(0.0, 0.25, r) * 0.35;
      col *= centerDark;

      // grain
      float grain = hash(gl_FragCoord.xy + fract(t * 137.0) * 1000.0);
      col += (grain - 0.5) * 0.03;

      // possession
      col = mix(col, vec3(0.7, 0.08, 0.03), possessed * 0.2);
      col *= 1.0 + possessed * sin(t * 15.0) * 0.06 + sin(t * 2.0) * 0.015;
      col = col / (1.0 + col * 0.15);

      gl_FragColor = vec4(col, 1.0);
    }
  `;

  /* ── compile ── */
  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error(gl.getShaderInfoLog(s));
      gl.deleteShader(s);
      return null;
    }
    return s;
  }

  const vs = compile(gl.VERTEX_SHADER, VERT);
  const fs = compile(gl.FRAGMENT_SHADER, FRAG);
  if (!vs || !fs) return;

  const prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.error(gl.getProgramInfoLog(prog));
    return;
  }
  gl.useProgram(prog);

  /* ── fullscreen quad ── */
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, 'a_pos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  /* ── uniforms ── */
  const uRes = gl.getUniformLocation(prog, 'u_res');
  const uTime = gl.getUniformLocation(prog, 'u_time');
  const uMouse = gl.getUniformLocation(prog, 'u_mouse');
  const uPossessed = gl.getUniformLocation(prog, 'u_possessed');

  let mx = W / 2, my = H / 2;
  let possessed = 0;

  document.addEventListener('mousemove', function(e) {
    mx = e.clientX * DPR;
    my = (window.innerHeight - e.clientY) * DPR;
  });

  // hook into the existing possession event
  const obs = new MutationObserver(function(muts) {
    const has = document.body.classList.contains('is-possessed');
    possessed = has ? 1.0 : 0.0;
  });
  obs.observe(document.body, { attributes: true, attributeFilter: ['class'] });

  /* ── render loop ── */
  let start = performance.now();
  let last = start, acc = 0;
  const SKIP_THRESHOLD = 22; // ms → below 45fps, skip a frame

  function frame(now) {
    requestAnimationFrame(frame);
    var dt = now - last;
    last = now;
    // adaptive frame skip: if we're struggling, drop a frame
    acc += dt;
    if (dt > SKIP_THRESHOLD) return; // skip this frame, let GPU catch up

    var t = (now - start) * 0.001;
    gl.uniform2f(uRes, W, H);
    gl.uniform1f(uTime, t);
    gl.uniform2f(uMouse, mx, my);
    gl.uniform1f(uPossessed, possessed);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  requestAnimationFrame(frame);
})();
