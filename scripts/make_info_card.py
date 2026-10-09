"""Hand-built neofetch-style info card (info-card.svg). Edit ROWS to update it.

STATIC=1 renders a frozen final frame (handy for local previews).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

W, H = 490, 377  # H matches ascii-portrait.svg so both sit level in the README table
PAD_X, FIRST_Y, LH = 20, 80, 17.4
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
KEY_W = 11  # characters

USER, HOST = "jasser", "chtourou"
ROWS = [
    ("Role", "AI Engineer · LLM & Agentic AI Systems"),
    ("Location", "Hannover, DE · open to Germany + remote"),
    ("Prev", "AI/Automation Eng. @ Finest Travel GmbH"),
    ("", "AI Backend Eng. @ AiNext · AI Eng. @ Plug&Plai"),
    ("", "Python Backend Eng. @ Keejob (2M+ users)"),
    ("Education", "Eng. Diploma AI & Data Science (≙ M.Sc.)"),
    ("AI/LLM", "RAG · LangGraph · LangChain · Azure OpenAI"),
    ("Backend", "Python · FastAPI · Django/DRF · Celery"),
    ("Data", "PostgreSQL/pgvector · Redis · Pinecone"),
    ("Infra", "Docker · GitHub Actions · Azure · AWS"),
    ("Shipped", "Plug&Chat multi-tenant RAG · 1k+ uses/mo"),
    ("Building", "SentryMesh LLM gateway · multi-agent O2C"),
    ("Languages", "AR · FR · EN (C1) · DE (B1)"),
]
BLOCKS = ["#484f58", "#ff7b72", "#7ee787", "#d29922", "#79c0ff", "#d2a8ff", "#56d4dd", "#e6edf3"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def line(i: int, body: str) -> str:
    y = FIRST_Y + i * LH
    if STATIC:
        return f'<g transform="translate(0 {y:.1f})">{body}</g>'
    return (
        f'<g transform="translate(0 {y:.1f})"><g class="l" style="animation-delay:{0.35 + i * 0.11:.2f}s">'
        f"{body}</g></g>"
    )


def main() -> None:
    cw = 12.5 * 0.6
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" font-size="12.5" fill="#c9d1d9">',
        "<style>",
        ".l{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
        ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".k{fill:#7ee787;font-weight:700}.u{fill:#79c0ff;font-weight:700}.d{fill:#484f58}",
        "</style>",
        f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v20H0z" fill="#161b22"/>',
        f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
        '<circle cx="18" cy="15" r="5.5" fill="#ff5f56"/>'
        '<circle cx="36" cy="15" r="5.5" fill="#ffbd2e"/>'
        '<circle cx="54" cy="15" r="5.5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="12" fill="#8b949e">'
        f"{USER}@{HOST}: ~ — neofetch</text>",
        f'<text x="{PAD_X}" y="54"><tspan fill="#58a6ff">$</tspan> neofetch</text>',
    ]

    i = 0
    title = f"{USER}@{HOST}"
    out.append(line(i, f'<text x="{PAD_X}"><tspan class="u">{USER}</tspan>@<tspan class="u">{HOST}</tspan></text>'))
    i += 1
    out.append(line(i, f'<text x="{PAD_X}" class="d">{"─" * len(title)}</text>'))
    i += 1
    for key, val in ROWS:
        k = f'<tspan class="k">{esc(key)}</tspan><tspan fill="#8b949e">:</tspan>' if key else ""
        out.append(line(i, f'<text x="{PAD_X}">{k}</text>'
                           f'<text x="{PAD_X + KEY_W * cw:.1f}">{esc(val)}</text>'))
        i += 1

    blocks = "".join(
        f'<rect x="{PAD_X + j * 26}" y="-4" width="24" height="12" rx="2" fill="{c}"/>'
        for j, c in enumerate(BLOCKS)
    )
    out.append(line(i, blocks))
    i += 1
    cursor = "" if STATIC else ' class="cur"'
    y = FIRST_Y + i * LH + 4
    out.append(line(i, f'<text x="{PAD_X}" y="4"><tspan fill="#58a6ff">$</tspan></text>'
                       f'<rect x="{PAD_X + 2 * cw:.1f}" y="-7" width="{cw:.1f}" height="14" '
                       f'fill="#7ee787"{cursor}/>'))
    out.append("</svg>")

    bottom = y + 14
    if bottom > H:
        print(f"warning: content ends at y={bottom:.0f}, taller than H={H}")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.name} ({W}x{H})")


if __name__ == "__main__":
    main()
