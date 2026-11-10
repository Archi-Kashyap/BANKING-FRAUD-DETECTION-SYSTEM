"""
BlurHash Placeholder Component for Banking Fraud Detection System.

Implements pure-Python base83 BlurHash encoding, decoding to data URLs,
and rich blurhash-backed placeholder dashboard skeletons for empty and loading states.
"""

import base64
import functools
import io
import math
from typing import Dict, Optional, Tuple, Union

import numpy as np
from PIL import Image

# BlurHash Base83 Alphabet
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%*+,-.:;=?@[]^_{|}~"
CHAR_MAP = {c: i for i, c in enumerate(CHARS)}

# Curated BlurHash Presets for Threat Intelligence
PRESET_BLURHASHES: Dict[str, str] = {
    "standby": "L113j[b_eli^kWkXg4emVBjFflbb",     # Deep cyber navy & subtle teal
    "loading": "L33b.3e9h#fkb^g2h0e.f,b_e-f6",     # Pulsing cyan & blue threat radar
    "safe": "L14,5j0000000000_300~q00_3~q",        # Ambient emerald security field
    "fraud": "L24o[Y%M00~q0000_300_300~q~q",       # Critical crimson alert field
    "suspicious": "L25#9E~q000000_30000_3~q00_3",  # Amber warning field
}


def decode83(s: str) -> int:
    """Decode a base83 string into an integer."""
    val = 0
    for char in s:
        val = val * 83 + CHAR_MAP[char]
    return val


def encode83(val: int, length: int) -> str:
    """Encode an integer into a base83 string of specified length."""
    res = []
    for i in range(1, length + 1):
        digit = (val // (83 ** (length - i))) % 83
        res.append(CHARS[digit])
    return "".join(res)


def srgb_to_linear(val: Union[int, float]) -> float:
    """Convert sRGB 0-255 integer or 0.0-1.0 float to linear color space."""
    v = val / 255.0 if val > 1.0 else float(val)
    if v <= 0.04045:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def linear_to_srgb(val: float) -> int:
    """Convert linear float color to sRGB 0-255 integer."""
    v = max(0.0, min(1.0, val))
    if v <= 0.0031308:
        return int(v * 12.92 * 255.0 + 0.5)
    return int((1.055 * (v ** (1.0 / 2.4)) - 0.055) * 255.0 + 0.5)


@functools.lru_cache(maxsize=64)
def decode_blurhash_to_data_url(
    blurhash: str,
    width: int = 32,
    height: int = 32,
    punch: float = 1.0,
) -> str:
    """
    Decode a BlurHash string into a base64 PNG data URL suitable for CSS background-image
    or HTML img src.
    """
    if not blurhash or len(blurhash) < 6:
        blurhash = PRESET_BLURHASHES["standby"]

    size_flag = decode83(blurhash[0])
    num_y = (size_flag // 9) + 1
    num_x = (size_flag % 9) + 1
    quantised_max_val = decode83(blurhash[1])
    max_val = (quantised_max_val + 1) / 166.0

    colors = []
    dc_val = decode83(blurhash[2:6])
    colors.append((
        srgb_to_linear((dc_val >> 16) & 255),
        srgb_to_linear((dc_val >> 8) & 255),
        srgb_to_linear(dc_val & 255),
    ))

    expected_len = 6 + (num_x * num_y - 1) * 2
    if len(blurhash) >= expected_len:
        for i in range(num_x * num_y - 1):
            ac_val = decode83(blurhash[6 + i * 2 : 8 + i * 2])
            qr = ac_val // (19 * 19)
            qg = (ac_val // 19) % 19
            qb = ac_val % 19
            colors.append((
                math.copysign(((abs(qr - 9) / 9.0) ** 2.0), qr - 9) * max_val * punch,
                math.copysign(((abs(qg - 9) / 9.0) ** 2.0), qg - 9) * max_val * punch,
                math.copysign(((abs(qb - 9) / 9.0) ** 2.0), qb - 9) * max_val * punch,
            ))
    else:
        # Fill remaining with zero AC coefficients
        for _ in range(num_x * num_y - 1 - len(colors) + 1):
            colors.append((0.0, 0.0, 0.0))

    xs = np.arange(width)
    ys = np.arange(height)
    cos_x = np.cos(np.pi * np.outer(xs, np.arange(num_x)) / width)
    cos_y = np.cos(np.pi * np.outer(ys, np.arange(num_y)) / height)

    img_arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            r, g, b = 0.0, 0.0, 0.0
            idx = 0
            for j in range(num_y):
                for i in range(num_x):
                    basis = cos_x[x, i] * cos_y[y, j]
                    c = colors[idx]
                    r += c[0] * basis
                    g += c[1] * basis
                    b += c[2] * basis
                    idx += 1
            img_arr[y, x, 0] = linear_to_srgb(r)
            img_arr[y, x, 1] = linear_to_srgb(g)
            img_arr[y, x, 2] = linear_to_srgb(b)

    pil_img = Image.fromarray(img_arr)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


def encode_image_to_blurhash(
    image: Union[Image.Image, np.ndarray],
    x_comp: int = 4,
    y_comp: int = 3,
) -> str:
    """
    Encode an image into a BlurHash string.
    """
    if isinstance(image, np.ndarray):
        pil_img = Image.fromarray(image).convert("RGB")
    else:
        pil_img = image.convert("RGB")

    # Resize to modest resolution for quick DCT
    pil_img.thumbnail((100, 100))
    arr = np.array(pil_img)
    h, w, _ = arr.shape

    linear_img = np.vectorize(srgb_to_linear)(arr)

    factors = []
    for j in range(y_comp):
        for i in range(x_comp):
            norm = 2.0 if (i > 0 or j > 0) else 1.0
            xs = np.arange(w)
            ys = np.arange(h)
            cos_x = np.cos(np.pi * i * xs / w)
            cos_y = np.cos(np.pi * j * ys / h)
            basis = np.outer(cos_y, cos_x)
            r = np.sum(linear_img[:, :, 0] * basis) * (norm / (w * h))
            g = np.sum(linear_img[:, :, 1] * basis) * (norm / (w * h))
            b = np.sum(linear_img[:, :, 2] * basis) * (norm / (w * h))
            factors.append((r, g, b))

    dc = factors[0]
    ac = factors[1:]

    size_flag = (x_comp - 1) + (y_comp - 1) * 9
    hash_str = encode83(size_flag, 1)

    if ac:
        actual_max = max(max(abs(c[0]), abs(c[1]), abs(c[2])) for c in ac)
        quant_max = int(max(0, min(82, math.floor(actual_max * 166.0 - 0.5))))
        max_val = (quant_max + 1) / 166.0
        hash_str += encode83(quant_max, 1)
    else:
        hash_str += encode83(0, 1)
        max_val = 1.0

    dc_val = (linear_to_srgb(dc[0]) << 16) + (linear_to_srgb(dc[1]) << 8) + linear_to_srgb(dc[2])
    hash_str += encode83(dc_val, 4)

    for r, g, b in ac:
        qr = int(max(0, min(18, math.floor(math.copysign((abs(r / max_val) ** 0.5) * 9.0, r) + 9.5))))
        qg = int(max(0, min(18, math.floor(math.copysign((abs(g / max_val) ** 0.5) * 9.0, g) + 9.5))))
        qb = int(max(0, min(18, math.floor(math.copysign((abs(b / max_val) ** 0.5) * 9.0, b) + 9.5))))
        ac_val = qr * 19 * 19 + qg * 19 + qb
        hash_str += encode83(ac_val, 2)

    return hash_str


def render_blurhash_dashboard_placeholder(
    is_loading: bool = False,
    custom_hash: Optional[str] = None,
    caption: Optional[str] = None,
) -> str:
    """
    Generate responsive HTML/CSS for a BlurHash-backed dashboard placeholder skeleton.
    Supports standby mode and active loading mode with animated cyber shimmer.
    """
    active_hash = custom_hash or (PRESET_BLURHASHES["loading"] if is_loading else PRESET_BLURHASHES["standby"])
    bg_data_url = decode_blurhash_to_data_url(active_hash, width=32, height=32)

    pulse_class = "blurhash-pulse" if is_loading else ""
    status_label = "ANALYZING THREAT VECTORS..." if is_loading else "AWAITING ANALYSIS"
    status_color = "#00e5ff" if is_loading else "#637d9b"
    guide_text = (
        "Multi-agent consensus engine is currently processing transaction telemetry..."
        if is_loading
        else "Choose a transaction and select Analyze. The verdict, gauge telemetry, and multi-agent reasoning will materialize here."
    )
    if caption:
        guide_text = caption

    return f"""
    <div class="blurhash-dashboard-wrapper {pulse_class}">
      <!-- BlurHash Ambient Backdrop -->
      <div class="blurhash-backdrop" style="background-image: url('{bg_data_url}');"></div>
      <div class="blurhash-scanlines"></div>

      <!-- Content Container -->
      <div class="blurhash-content">
        <!-- Hero Verdict Skeleton -->
        <div class="blurhash-hero-skeleton">
          <div class="blurhash-hero-left">
            <div class="blurhash-tag-bar">
              <span class="blurhash-status-pill" style="border-color: {status_color}; color: {status_color};">
                <span class="blurhash-dot" style="background: {status_color};"></span>
                {status_label}
              </span>
              <span class="blurhash-hash-badge" title="Source BlurHash">hash: {active_hash}</span>
            </div>
            <div class="blurhash-title-bar"></div>
            <div class="blurhash-sub-bar"></div>
          </div>
          <div class="blurhash-hero-right">
            <div class="blurhash-gauge-skeleton">
              <svg viewBox="0 0 100 100" class="blurhash-gauge-svg">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#12263f" stroke-width="8" stroke-dasharray="180 80" stroke-linecap="round"/>
                <circle cx="50" cy="50" r="40" fill="none" stroke="{status_color}" stroke-width="8" stroke-dasharray="25 240" stroke-linecap="round" opacity="0.6"/>
              </svg>
              <div class="blurhash-gauge-score">--</div>
            </div>
          </div>
        </div>

        <!-- 4 Metric Cards Skeleton -->
        <div class="blurhash-metrics-grid">
          <div class="blurhash-metric-card">
            <div class="blurhash-metric-hdr">Behavior</div>
            <div class="blurhash-metric-val">--.-</div>
            <div class="blurhash-metric-track"><div class="blurhash-metric-fill" style="width: 35%;"></div></div>
            <div class="blurhash-metric-badge">STANDBY</div>
          </div>
          <div class="blurhash-metric-card">
            <div class="blurhash-metric-hdr">Risk</div>
            <div class="blurhash-metric-val">--.-</div>
            <div class="blurhash-metric-track"><div class="blurhash-metric-fill" style="width: 45%;"></div></div>
            <div class="blurhash-metric-badge">STANDBY</div>
          </div>
          <div class="blurhash-metric-card">
            <div class="blurhash-metric-hdr">Anomaly</div>
            <div class="blurhash-metric-val">--.-</div>
            <div class="blurhash-metric-track"><div class="blurhash-metric-fill" style="width: 20%;"></div></div>
            <div class="blurhash-metric-badge">STANDBY</div>
          </div>
          <div class="blurhash-metric-card">
            <div class="blurhash-metric-hdr">Velocity</div>
            <div class="blurhash-metric-val">--.-</div>
            <div class="blurhash-metric-track"><div class="blurhash-metric-fill" style="width: 30%;"></div></div>
            <div class="blurhash-metric-badge">STANDBY</div>
          </div>
        </div>

        <!-- Agent Network Skeleton -->
        <div class="blurhash-network-skeleton">
          <div class="blurhash-network-header">
            <span>MULTI-AGENT ORCHESTRATION PIPELINE</span>
            <span style="opacity: 0.6; font-size: 11px;">BLURHASH PREVIEW</span>
          </div>
          <div class="blurhash-nodes-row">
            <div class="blurhash-node">
              <div class="blurhash-node-icon">01</div>
              <div class="blurhash-node-label">Behavior</div>
            </div>
            <div class="blurhash-connector"></div>
            <div class="blurhash-node">
              <div class="blurhash-node-icon">02</div>
              <div class="blurhash-node-label">Risk</div>
            </div>
            <div class="blurhash-connector"></div>
            <div class="blurhash-node">
              <div class="blurhash-node-icon">03</div>
              <div class="blurhash-node-label">Validator</div>
            </div>
            <div class="blurhash-connector"></div>
            <div class="blurhash-node">
              <div class="blurhash-node-icon">04</div>
              <div class="blurhash-node-label">Synthesizer</div>
            </div>
          </div>
        </div>

        <!-- Guide Notice -->
        <div class="blurhash-footer-notice">
          {guide_text}
        </div>
      </div>
    </div>

    <style>
      .blurhash-dashboard-wrapper {{
        position: relative;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #14324f;
        background: #060e19;
        margin-top: 18px;
        margin-bottom: 24px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }}
      .blurhash-backdrop {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-size: cover;
        background-position: center;
        filter: blur(20px);
        opacity: 0.12;
        transform: scale(1.04);
        pointer-events: none;
      }}
      .blurhash-scanlines {{
        display: none !important;
      }}
      .blurhash-content {{
        position: relative;
        z-index: 2;
        padding: 24px 28px;
        background: rgba(6, 14, 25, 0.72);
        backdrop-filter: blur(12px);
      }}
      .blurhash-hero-skeleton {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 24px;
        border-radius: 6px;
        background: rgba(10, 24, 45, 0.45);
        border: 1px solid rgba(22, 53, 89, 0.6);
        margin-bottom: 18px;
      }}
      .blurhash-hero-left {{
        flex: 1;
      }}
      .blurhash-tag-bar {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
      }}
      .blurhash-status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        border-radius: 4px;
        border: 1px solid;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
      }}
      .blurhash-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
      }}
      .blurhash-hash-badge {{
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 10px;
        color: #4a6a8c;
        background: rgba(14, 34, 60, 0.6);
        padding: 2px 6px;
        border-radius: 3px;
      }}
      .blurhash-title-bar {{
        width: 48%;
        height: 20px;
        border-radius: 4px;
        background: rgba(30, 65, 105, 0.45);
        margin-bottom: 10px;
      }}
      .blurhash-sub-bar {{
        width: 28%;
        height: 12px;
        border-radius: 3px;
        background: rgba(22, 50, 82, 0.4);
      }}
      .blurhash-hero-right {{
        margin-left: 24px;
      }}
      .blurhash-gauge-skeleton {{
        position: relative;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .blurhash-gauge-svg {{
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }}
      .blurhash-gauge-score {{
        position: absolute;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 18px;
        font-weight: 700;
        color: #557796;
      }}
      .blurhash-metrics-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 18px;
      }}
      .blurhash-metric-card {{
        background: rgba(9, 21, 38, 0.5);
        border: 1px solid rgba(20, 50, 79, 0.55);
        border-radius: 6px;
        padding: 14px 16px;
      }}
      .blurhash-metric-hdr {{
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #557796;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
      }}
      .blurhash-metric-val {{
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 20px;
        font-weight: 700;
        color: #8bb0d6;
        margin-bottom: 8px;
      }}
      .blurhash-metric-track {{
        width: 100%;
        height: 5px;
        background: rgba(18, 38, 64, 0.7);
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 8px;
      }}
      .blurhash-metric-fill {{
        height: 100%;
        background: #1b4975;
        border-radius: 3px;
      }}
      .blurhash-metric-badge {{
        display: inline-block;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 10px;
        color: #4a6a8c;
        background: rgba(14, 32, 56, 0.6);
        padding: 2px 6px;
        border-radius: 3px;
      }}
      .blurhash-network-skeleton {{
        background: rgba(7, 16, 28, 0.55);
        border: 1px solid rgba(18, 44, 72, 0.5);
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 16px;
      }}
      .blurhash-network-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 11px;
        font-weight: 700;
        color: #4a6a8c;
        letter-spacing: 0.8px;
        margin-bottom: 16px;
      }}
      .blurhash-nodes-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
      }}
      .blurhash-node {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
      }}
      .blurhash-node-icon {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(14, 35, 62, 0.7);
        border: 1px solid rgba(30, 75, 125, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 11px;
        font-weight: 700;
        color: #638eb8;
      }}
      .blurhash-node-label {{
        font-size: 11px;
        color: #557796;
      }}
      .blurhash-connector {{
        flex: 1;
        height: 2px;
        background: linear-gradient(90deg, rgba(20, 50, 79, 0.2), rgba(30, 80, 130, 0.6), rgba(20, 50, 79, 0.2));
        margin: 0 10px;
      }}
      .blurhash-footer-notice {{
        text-align: center;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 12px;
        color: #638eb8;
        padding-top: 6px;
      }}
      .blurhash-pulse .blurhash-backdrop {{
        animation: blurhashGlow 2.4s ease-in-out infinite alternate;
      }}
      .blurhash-pulse .blurhash-title-bar,
      .blurhash-pulse .blurhash-metric-fill {{
        animation: blurhashShimmer 1.8s ease-in-out infinite;
      }}
      @keyframes blurhashGlow {{
        0% {{ opacity: 0.22; filter: blur(24px) saturate(140%); }}
        100% {{ opacity: 0.38; filter: blur(32px) saturate(220%); }}
      }}
      @keyframes blurhashShimmer {{
        0% {{ opacity: 0.5; }}
        50% {{ opacity: 0.85; }}
        100% {{ opacity: 0.5; }}
      }}
    </style>
    """
