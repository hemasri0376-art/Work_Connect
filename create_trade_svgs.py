"""Script to generate high quality visual SVG illustrations for all trade categories."""
from pathlib import Path

TRADES = {
    "mason.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="masonBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF6B4A"/>
      <stop offset="100%" stop-color="#D9381E"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#masonBg)"/>
  <g filter="url(#shadow)" transform="translate(18, 20)">
    <!-- Brick Wall -->
    <rect x="10" y="38" width="64" height="34" rx="4" fill="#FFE8E2"/>
    <path d="M10 49 H74 M10 61 H74 M32 38 V49 M52 38 V49 M20 49 V61 M42 49 V61 M64 49 V61 M32 61 V72 M52 61 V72" stroke="#FF6B4A" stroke-width="2.5" stroke-linecap="round"/>
    <!-- Mason Trowel -->
    <path d="M30 32 L46 16 C48 14 52 14 54 16 L62 24 C64 26 64 30 62 32 L46 48 Z" fill="#FFFFFF"/>
    <path d="M26 36 L16 46 C14 48 14 52 16 54 L18 56 C20 58 24 58 26 56 L36 46 Z" fill="#FFE2B8"/>
    <path d="M28 34 L38 44" stroke="#D9381E" stroke-width="3" stroke-linecap="round"/>
    <!-- Hard Hat Icon -->
    <path d="M42 14 C42 6 30 6 30 14 Z" fill="#FFC837"/>
  </g>
</svg>""",

    "driver.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="driverBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2D7FF9"/>
      <stop offset="100%" stop-color="#1452B8"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#driverBg)"/>
  <g filter="url(#shadow)" transform="translate(20, 20)">
    <!-- Steering Wheel -->
    <circle cx="40" cy="40" r="32" fill="none" stroke="#FFFFFF" stroke-width="7"/>
    <circle cx="40" cy="40" r="11" fill="#FFFFFF"/>
    <!-- Spokes -->
    <line x1="12" y1="40" x2="29" y2="40" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round"/>
    <line x1="51" y1="40" x2="68" y2="40" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round"/>
    <line x1="40" y1="51" x2="40" y2="68" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round"/>
    <!-- Speed/Transport Details -->
    <circle cx="40" cy="40" r="4" fill="#2D7FF9"/>
    <path d="M26 22 L32 26" stroke="#93C5FD" stroke-width="3" stroke-linecap="round"/>
    <path d="M54 22 L48 26" stroke="#93C5FD" stroke-width="3" stroke-linecap="round"/>
  </g>
</svg>""",

    "electrician.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="elecBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F59E0B"/>
      <stop offset="100%" stop-color="#D97706"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#elecBg)"/>
  <g filter="url(#shadow)" transform="translate(24, 16)">
    <!-- Light Bulb & Energy Flash -->
    <path d="M36 6 C22 6 12 17 12 30 C12 39 18 46 22 52 L22 60 C22 62 24 64 26 64 L46 64 C48 64 50 62 50 60 L50 52 C54 46 60 39 60 30 C60 17 50 6 36 6 Z" fill="#FEF3C7"/>
    <path d="M26 64 L28 72 C28 74 30 76 32 76 L40 76 C42 76 44 74 44 72 L46 64 Z" fill="#9CA3AF"/>
    <!-- Bright Lightning Bolt -->
    <path d="M38 16 L24 38 L34 38 L30 54 L46 32 L36 32 Z" fill="#F59E0B"/>
    <!-- Glow lines -->
    <line x1="36" y1="0" x2="36" y2="4" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>
    <line x1="8" y1="20" x2="4" y2="18" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>
    <line x1="64" y1="20" x2="68" y2="18" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>
  </g>
</svg>""",

    "painter.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="painterBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#6D28D9"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#painterBg)"/>
  <g filter="url(#shadow)" transform="translate(20, 20)">
    <!-- Paint Roller -->
    <rect x="8" y="12" width="56" height="22" rx="7" fill="#FFFFFF"/>
    <!-- Fresh Paint Stripe -->
    <rect x="14" y="16" width="34" height="14" rx="4" fill="#C4B5FD"/>
    <!-- Roller Arm -->
    <path d="M64 23 H70 C72 23 74 25 74 27 V42 C74 44 72 46 70 46 H40 V54" stroke="#E2E8F0" stroke-width="5" stroke-linecap="round" fill="none"/>
    <!-- Wooden Handle -->
    <rect x="34" y="52" width="12" height="26" rx="4" fill="#FDE68A"/>
    <!-- Paint Drip -->
    <circle cx="20" cy="44" r="4" fill="#C4B5FD"/>
    <path d="M32 34 Q32 46 35 48 Q38 46 38 34 Z" fill="#C4B5FD"/>
  </g>
</svg>""",

    "farm_worker.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="farmBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10B981"/>
      <stop offset="100%" stop-color="#047857"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#farmBg)"/>
  <g filter="url(#shadow)" transform="translate(20, 18)">
    <!-- Golden Wheat Stalks & Green Sprout -->
    <!-- Center Stalk -->
    <path d="M40 76 V22" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
    <!-- Wheat Grains Right -->
    <path d="M40 28 C48 24 54 28 50 36 C44 38 40 32 40 28 Z" fill="#FDE047"/>
    <path d="M40 42 C50 38 56 42 52 50 C44 52 40 46 40 42 Z" fill="#FDE047"/>
    <path d="M40 56 C50 52 56 56 52 64 C44 66 40 60 40 56 Z" fill="#FDE047"/>
    <!-- Wheat Grains Left -->
    <path d="M40 28 C32 24 26 28 30 36 C36 38 40 32 40 28 Z" fill="#FDE047"/>
    <path d="M40 42 C30 38 24 42 28 50 C36 52 40 46 40 42 Z" fill="#FDE047"/>
    <path d="M40 56 C30 52 24 56 28 64 C36 66 40 60 40 56 Z" fill="#FDE047"/>
    <!-- Top Leaf -->
    <path d="M40 22 C36 12 44 8 40 8 C36 8 38 14 40 22 Z" fill="#A7F3D0"/>
  </g>
</svg>""",

    "carpenter.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="carpBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#B45309"/>
      <stop offset="100%" stop-color="#78350F"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#carpBg)"/>
  <g filter="url(#shadow)" transform="translate(20, 20)">
    <!-- Hand Saw & Hammer Cross -->
    <path d="M12 60 L56 16 L66 26 L22 70 Z" fill="#E2E8F0"/>
    <path d="M12 60 L18 56 L20 62 L26 58 L28 64 L34 60 L36 66 L42 62 L44 68 L50 64 L52 70" stroke="#78350F" stroke-width="2"/>
    <path d="M54 14 C58 10 68 12 70 20 C72 26 66 32 60 30 Z" fill="#FDE68A"/>
    <circle cx="62" cy="20" r="4" fill="#78350F"/>
  </g>
</svg>""",

    "plumber.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="plumbBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06B6D4"/>
      <stop offset="100%" stop-color="#0891B2"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#plumbBg)"/>
  <g filter="url(#shadow)" transform="translate(20, 20)">
    <!-- Water Pipe & Droplet -->
    <path d="M12 28 H44 V68 H28 V44 H12 Z" fill="#E0F2FE"/>
    <!-- Water Drop -->
    <path d="M56 46 C56 46 68 58 68 66 C68 72 63 78 56 78 C49 78 44 72 44 66 C44 58 56 46 56 46 Z" fill="#FFFFFF"/>
    <!-- Valve wheel -->
    <circle cx="28" cy="18" r="10" fill="none" stroke="#FFFFFF" stroke-width="4"/>
    <line x1="28" y1="8" x2="28" y2="28" stroke="#FFFFFF" stroke-width="3"/>
  </g>
</svg>""",

    "helper.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="helpBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366F1"/>
      <stop offset="100%" stop-color="#4338CA"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="120" height="120" rx="28" fill="url(#helpBg)"/>
  <g filter="url(#shadow)" transform="translate(20, 20)">
    <!-- Helping Hands & Toolkit Box -->
    <rect x="14" y="32" width="52" height="38" rx="8" fill="#FFFFFF"/>
    <path d="M28 32 V24 C28 20 32 16 36 16 H44 C48 16 52 20 52 24 V32" stroke="#FFFFFF" stroke-width="4" fill="none"/>
    <rect x="22" y="44" width="36" height="6" rx="3" fill="#6366F1"/>
    <!-- Star/Excellence badge -->
    <circle cx="40" cy="58" r="8" fill="#FBBF24"/>
  </g>
</svg>"""
}

out_dir = Path(__file__).resolve().parent / "static" / "images" / "trades"
out_dir.mkdir(parents=True, exist_ok=True)

for fname, content in TRADES.items():
    (out_dir / fname).write_text(content.strip(), encoding="utf-8")
    print(f"Generated {fname}")
print("All trade icons generated successfully!")
