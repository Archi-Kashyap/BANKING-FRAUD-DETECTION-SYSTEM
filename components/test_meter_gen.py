import math

def render_meter_svg(score: float, cx=150, cy=140, r=105, sw=16) -> str:
    score_clamped = max(0.0, min(100.0, float(score)))

    # Arc 1: Green (score 0 to 30 -> 180 deg to 126 deg)
    # Arc 2: Amber (score 30 to 60 -> 126 deg to 72 deg)
    # Arc 3: Red (score 60 to 100 -> 72 deg to 0 deg)

    def pt(deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy - r * math.sin(rad)

    x0, y0 = pt(180)
    x1, y1 = pt(126)
    x2, y2 = pt(72)
    x3, y3 = pt(0)

    # Needle tip (score 0 -> 180 deg, score 100 -> 0 deg)
    needle_deg = 180.0 - (score_clamped / 100.0) * 180.0
    needle_len = r * 0.76
    needle_rad = math.radians(needle_deg)
    tx = cx + needle_len * math.cos(needle_rad)
    ty = cy - needle_len * math.sin(needle_rad)

    svg = f'''<svg viewBox="0 0 300 190" class="gauge-svg" xmlns="http://www.w3.org/2000/svg">
  <!-- 3 Gauge Arc Segments: Green, Amber, Red with flat ends -->
  <path d="M {x0:.2f} {y0:.2f} A {r} {r} 0 0 1 {x1:.2f} {y1:.2f}" fill="none" stroke="#16c479" stroke-width="{sw}" stroke-linecap="butt" />
  <path d="M {x1:.2f} {y1:.2f} A {r} {r} 0 0 1 {x2:.2f} {y2:.2f}" fill="none" stroke="#da9c1f" stroke-width="{sw}" stroke-linecap="butt" />
  <path d="M {x2:.2f} {y2:.2f} A {r} {r} 0 0 1 {x3:.2f} {y3:.2f}" fill="none" stroke="#da4754" stroke-width="{sw}" stroke-linecap="butt" />

  <!-- Needle -->
  <line x1="{cx}" y1="{cy}" x2="{tx:.2f}" y2="{ty:.2f}" stroke="#d5e6f5" stroke-width="3.5" stroke-linecap="round" />

  <!-- Center Solid Pivot -->
  <circle cx="{cx}" cy="{cy}" r="8.5" fill="#d5e6f5" />

  <!-- Score Value under needle -->
  <text x="{cx}" y="{cy + 32}" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="26" font-weight="700" fill="#d5e6f5">{score_clamped:.1f}</text>
</svg>'''
    return svg

if __name__ == '__main__':
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
body {{ background: #06261a; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
svg {{ width: 300px; height: 190px; }}
</style>
</head>
<body>
{render_meter_svg(9.0)}
</body>
</html>'''

    with open('components/_test_meter.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Generated components/_test_meter.html')
