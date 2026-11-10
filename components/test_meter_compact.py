import math
from playwright.sync_api import sync_playwright

def render_gauge_svg(score: float) -> str:
    cx, cy, r, sw = 150, 135, 105, 16
    score_clamped = max(0.0, min(100.0, float(score)))

    def pt(deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy - r * math.sin(rad)

    x0, y0 = pt(180)
    x1, y1 = pt(126)
    x2, y2 = pt(72)
    x3, y3 = pt(0)

    needle_deg = 180.0 - (score_clamped / 100.0) * 180.0
    needle_len = r * 0.76
    needle_rad = math.radians(needle_deg)
    tx = cx + needle_len * math.cos(needle_rad)
    ty = cy - needle_len * math.sin(needle_rad)

    # Return as single-line string with no indentation so Markdown cannot mangle it
    svg = (
        f'<svg viewBox="0 0 300 185" class="gauge-svg" xmlns="http://www.w3.org/2000/svg" style="display:block;width:100%;height:auto;">'
        f'<path d="M {x0:.2f} {y0:.2f} A {r} {r} 0 0 1 {x1:.2f} {y1:.2f}" fill="none" stroke="#16c479" stroke-width="{sw}" stroke-linecap="butt" />'
        f'<path d="M {x1:.2f} {y1:.2f} A {r} {r} 0 0 1 {x2:.2f} {y2:.2f}" fill="none" stroke="#da9c1f" stroke-width="{sw}" stroke-linecap="butt" />'
        f'<path d="M {x2:.2f} {y2:.2f} A {r} {r} 0 0 1 {x3:.2f} {y3:.2f}" fill="none" stroke="#da4754" stroke-width="{sw}" stroke-linecap="butt" />'
        f'<line x1="{cx}" y1="{cy}" x2="{tx:.2f}" y2="{ty:.2f}" stroke="#d5e6f5" stroke-width="3.5" stroke-linecap="round" />'
        f'<circle cx="{cx}" cy="{cy}" r="8.5" fill="#d5e6f5" />'
        f'<text x="{cx}" y="{cy + 30}" text-anchor="middle" font-family="\'JetBrains Mono\', monospace" font-size="26" font-weight="700" fill="#d5e6f5">{score_clamped:.1f}</text>'
        f'</svg>'
    )
    return svg

if __name__ == '__main__':
    print('Testing single line SVG...')
    s = render_gauge_svg(9.0)
    print('Has newlines:', '\n' in s)
    print('Length:', len(s))
