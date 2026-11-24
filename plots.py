"""Server-rendered SVG charts for Lab 04.

Charts only draw numeric series that came from a real ngspice run. They do no
engineering calculation: scaling, axes and text layout are presentation only.
"""

from __future__ import annotations

import html
import math


def _tick(value: float) -> str:
    if value == 0:
        return "0"
    return f"{value:.3g}"


def line_chart(
    series: list[dict],
    *,
    x_label: str,
    y_label: str,
    x_log: bool = False,
    width: int = 640,
    height: int = 260,
) -> str:
    """Return an SVG with axes, units, gridlines and a legend."""
    if not series or not any(series_item["points"] for series_item in series):
        return '<p class="chart-empty">ไม่มีข้อมูลจากการรันจริงที่จะ plot</p>'

    sampled = []
    for item in series:
        points = list(item["points"])
        if len(points) > 600:
            stride = math.ceil(len(points) / 600)
            points = points[::stride]
        sampled.append({**item, "points": points})

    all_x = [x for item in sampled for x, _ in item["points"]]
    all_y = [y for item in sampled for _, y in item["points"]]
    if x_log:
        all_x = [math.log10(x) for x in all_x if x > 0]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    if x_min == x_max:
        x_min -= 1
        x_max += 1
    if y_min == y_max:
        y_min -= 1
        y_max += 1
    padding_y = (y_max - y_min) * 0.08
    y_min -= padding_y
    y_max += padding_y

    left, right, top, bottom = 72, 18, 40, 52
    plot_width = width - left - right
    plot_height = height - top - bottom

    def to_x(value: float) -> float:
        scaled = math.log10(value) if x_log else value
        return left + (scaled - x_min) / (x_max - x_min) * plot_width

    def to_y(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    parts = [
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(x_label)} versus {html.escape(y_label)}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    for step in range(5):
        y_value = y_min + (y_max - y_min) * step / 4
        y_px = to_y(y_value)
        parts.append(f'<line x1="{left}" y1="{y_px:.1f}" x2="{width - right}" '
                     f'y2="{y_px:.1f}" stroke="#e7edf4"/>')
        parts.append(f'<text x="{left - 8}" y="{y_px + 4:.1f}" text-anchor="end" '
                     f'font-size="11" fill="#5d6b7c">{_tick(y_value)}</text>')
    for step in range(5):
        x_scaled = x_min + (x_max - x_min) * step / 4
        x_value = 10 ** x_scaled if x_log else x_scaled
        x_px = left + (x_scaled - x_min) / (x_max - x_min) * plot_width
        parts.append(f'<line x1="{x_px:.1f}" y1="{top}" x2="{x_px:.1f}" '
                     f'y2="{height - bottom}" stroke="#eef2f7"/>')
        parts.append(f'<text x="{x_px:.1f}" y="{height - bottom + 17}" text-anchor="middle" '
                     f'font-size="11" fill="#5d6b7c">{_tick(x_value)}</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#9aa9ba"/>')
    parts.append(f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" '
                 f'y2="{height - bottom}" stroke="#9aa9ba"/>')
    parts.append(f'<text x="{left + plot_width / 2:.1f}" y="{height - 8}" text-anchor="middle" '
                 f'font-size="12" fill="#1d2733">{html.escape(x_label)}</text>')
    parts.append(f'<text transform="translate(16 {top + plot_height / 2:.1f}) rotate(-90)" '
                 f'text-anchor="middle" font-size="12" fill="#1d2733">{html.escape(y_label)}</text>')

    for legend_index, item in enumerate(sampled):
        color = item.get("color", "#1f6feb")
        points_text = " ".join(
            f"{to_x(x):.1f},{to_y(y):.1f}" for x, y in item["points"] if (not x_log or x > 0)
        )
        if points_text:
            parts.append(f'<polyline points="{points_text}" fill="none" stroke="{color}" '
                         f'stroke-width="2" stroke-linejoin="round"/>')
        legend_x = left + legend_index * 170
        parts.append(f'<line x1="{legend_x}" y1="18" x2="{legend_x + 18}" y2="18" '
                     f'stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x + 24}" y="22" font-size="11" fill="#1d2733">'
                     f'{html.escape(item["name"])}</text>')
    parts.append("</svg>")
    return "".join(parts)
