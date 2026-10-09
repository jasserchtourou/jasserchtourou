"""Render data/contributions.json as an animated terminal-style heatmap SVG."""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

W = 860
CELL, GAP = 11, 3
STEP = CELL + GAP
GRID_Y = 78
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    start = first.toordinal() - (first.isoweekday() % 7)  # Sunday of first week
    n_cols = (date.fromisoformat(days[-1]["date"]).toordinal() - start) // 7 + 1
    grid_x = (W - n_cols * STEP) // 2 + 14  # centred, leaving room for weekday labels

    cells, month_labels, last_month = [], [], None
    max_col = 0
    for d in days:
        dt = date.fromisoformat(d["date"])
        col, row = (dt.toordinal() - start) // 7, dt.isoweekday() % 7
        max_col = max(max_col, col)
        x, y = grid_x + col * STEP, GRID_Y + row * STEP
        delay = (col + row) * 0.018
        anim = "" if STATIC else f' class="c" style="animation-delay:{delay:.3f}s"'
        title = f"{d['count']} contribution{'s' if d['count'] != 1 else ''} on {d['date']}"
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[min(d["level"], 4)]}"{anim}><title>{title}</title></rect>'
        )
        if row == 0 and dt.month != last_month and dt.day <= 7:
            month_labels.append((x, MONTHS[dt.month - 1]))
            last_month = dt.month

    grid_bottom = GRID_Y + 7 * STEP
    H = grid_bottom + 92

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" font-size="11" fill="#8b949e">',
        "<style>",
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:pop .45s cubic-bezier(.2,.8,.3,1.3) forwards}"
        "@keyframes pop{from{opacity:0;transform:translate(-6px,-6px) scale(.3)}"
        "to{opacity:1;transform:none}}"
        ".f{opacity:0;animation:fade .6s ease-out forwards}"
        "@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
                ".k{fill:#7ee787}.v{fill:#e6edf3;font-weight:600}.p{fill:#58a6ff}",
        "</style>",
        f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        # title bar
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v20H0z" fill="#161b22"/>',
        f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
        '<circle cx="18" cy="15" r="5.5" fill="#ff5f56"/>'
        '<circle cx="36" cy="15" r="5.5" fill="#ffbd2e"/>'
        '<circle cx="54" cy="15" r="5.5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="12">'
        f'{esc(data["username"])}@github: ~/contributions</text>',
        # prompt line
        f'<text x="20" y="53" font-size="12"><tspan class="p">$</tspan> '
        f'<tspan fill="#e6edf3">heatmap --user {esc(data["username"])} --last-year</tspan></text>',
    ]
    parts += [f'<text x="{x}" y="{GRID_Y - 6}">{m}</text>' for x, m in month_labels]
    parts += [
        f'<text x="{grid_x - 8}" y="{GRID_Y + r * STEP + 10}" text-anchor="end">{lbl}</text>'
        for r, lbl in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    ]
    parts += cells

    # legend
    lx = grid_x + (max_col + 1) * STEP - 5 * STEP - 30
    ly = grid_bottom + 10
    fade = "" if STATIC else ' class="f" style="animation-delay:1.2s"'
    legend = [f'<g{fade}><text x="{lx - 34}" y="{ly + 10}">Less</text>']
    legend += [
        f'<rect x="{lx + i * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    ]
    legend.append(f'<text x="{lx + 5 * STEP + 4}" y="{ly + 10}">More</text></g>')
    parts += legend

    # stats footer
    best = data["best_day"]
    stats = [
        ("total", f'{data["total"]}'),
        ("active_days", f'{data["active_days"]}'),
        ("current_streak", f'{data["current_streak"]}d'),
        ("longest_streak", f'{data["longest_streak"]}d'),
        ("best_day", f'{best["count"]} @ {best["date"]}'),
    ]
    fy = grid_bottom + 52
    parts.append(f'<line x1="20" y1="{fy - 18}" x2="{W - 20}" y2="{fy - 18}" stroke="#21262d"/>')
    x = 20
    for i, (k, v) in enumerate(stats):
        f = "" if STATIC else f' class="f" style="animation-delay:{1.3 + i * 0.12:.2f}s"'
        parts.append(
            f'<text x="{x}" y="{fy}" font-size="12"{f}><tspan class="k">{k}</tspan>'
            f'<tspan fill="#8b949e">=</tspan><tspan class="v">{esc(v)}</tspan></text>'
        )
        x += (len(k) + len(v) + 1) * 7.3 + 26
    f = "" if STATIC else ' class="f" style="animation-delay:2s"'
    parts.append(
        f'<text x="{W - 20}" y="{fy + 22}" text-anchor="end" font-size="10" fill="#484f58"{f}>'
        f'updated {data["generated"]}</text>'
    )
    parts.append("</svg>")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT.name} ({W}x{H})")


if __name__ == "__main__":
    main()
