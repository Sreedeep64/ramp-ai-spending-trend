from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ramp_ai_provider_adoption.csv"
SUMMARY_FILE = ROOT / "data" / "analysis_summary.csv"
PDF_FILE = ROOT / "output" / "pdf" / "Ramp-AI-Spending-Trend.pdf"
DOWNLOAD_PDF = Path.home() / "Downloads" / PDF_FILE.name
COVER_FILE = ROOT / "output" / "Ramp-AI-Spending-Trend-Cover.png"
DOWNLOAD_COVER = Path.home() / "Downloads" / COVER_FILE.name

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

NAVY = colors.HexColor("#10213A")
INK = colors.HexColor("#17243A")
MUTED = colors.HexColor("#5C6878")
LIGHT = colors.HexColor("#E4EAF0")
PANEL = colors.HexColor("#F5F7FA")
TEAL = colors.HexColor("#0C9A78")
ORANGE = colors.HexColor("#E7683C")
BLUE = colors.HexColor("#2E6DE6")
PURPLE = colors.HexColor("#7A55D7")
WHITE = colors.white


def load_data() -> list[dict[str, float | datetime]]:
    rows: list[dict[str, float | datetime]] = []
    with DATA_FILE.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "date": datetime.strptime(raw["observation_date"], "%Y-%m-%d"),
                    "overall": float(raw["RAMPAIALL"]),
                    "anthropic": float(raw["RAMPAIANTHROPIC"]),
                    "openai": float(raw["RAMPAIOPENAI"]),
                }
            )
    if not rows or rows[-1]["date"].strftime("%Y-%m-%d") != "2026-10-01":
        raise ValueError("Expected Ramp/FRED data through October 2026")
    for row in rows:
        row["minimum_overlap"] = max(
            0.0,
            float(row["anthropic"]) + float(row["openai"]) - float(row["overall"]),
        )
    return rows


def get_metrics(rows: list[dict[str, float | datetime]]) -> dict[str, float | str]:
    by_date = {row["date"].strftime("%Y-%m-%d"): row for row in rows}
    jan = by_date["2026-01-01"]
    oct_row = by_date["2026-10-01"]
    crossover = next(
        row for row in rows if float(row["anthropic"]) > float(row["openai"])
    )
    overlap_share = 100 * float(oct_row["minimum_overlap"]) / float(oct_row["overall"])
    metrics: dict[str, float | str] = {
        "jan_overall": float(jan["overall"]),
        "oct_overall": float(oct_row["overall"]),
        "overall_change": float(oct_row["overall"]) - float(jan["overall"]),
        "jan_anthropic": float(jan["anthropic"]),
        "oct_anthropic": float(oct_row["anthropic"]),
        "anthropic_change": float(oct_row["anthropic"]) - float(jan["anthropic"]),
        "jan_openai": float(jan["openai"]),
        "oct_openai": float(oct_row["openai"]),
        "openai_change": float(oct_row["openai"]) - float(jan["openai"]),
        "minimum_overlap": float(oct_row["minimum_overlap"]),
        "minimum_overlap_share": overlap_share,
        "crossover_month": crossover["date"].strftime("%B %Y"),
    }
    if not (50.2 < overlap_share < 50.4):
        raise ValueError("Unexpected October overlap calculation")
    return metrics


def write_summary(metrics: dict[str, float | str]) -> None:
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ("January 2026 overall adoption (%)", metrics["jan_overall"]),
        ("October 2026 overall adoption (%)", metrics["oct_overall"]),
        ("January to October overall change (percentage points)", metrics["overall_change"]),
        ("January 2026 Anthropic adoption (%)", metrics["jan_anthropic"]),
        ("October 2026 Anthropic adoption (%)", metrics["oct_anthropic"]),
        ("January to October Anthropic change (percentage points)", metrics["anthropic_change"]),
        ("January 2026 OpenAI adoption (%)", metrics["jan_openai"]),
        ("October 2026 OpenAI adoption (%)", metrics["oct_openai"]),
        ("January to October OpenAI change (percentage points)", metrics["openai_change"]),
        ("October 2026 minimum overlap (percentage points)", metrics["minimum_overlap"]),
        ("Minimum share of AI adopters paying both (%)", metrics["minimum_overlap_share"]),
        ("First month Anthropic exceeded OpenAI", metrics["crossover_month"]),
    ]
    with SUMMARY_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Metric", "Value"])
        writer.writerows(rows)


def paragraph(
    c: canvas.Canvas,
    text: str,
    x: float,
    y_top: float,
    width: float,
    height: float,
    *,
    size: float,
    leading: float,
    color: colors.Color = INK,
    bold: bool = False,
    align: int = TA_LEFT,
) -> float:
    style = ParagraphStyle(
        "body",
        fontName="ArialBold" if bold else "Arial",
        fontSize=size,
        leading=leading,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
    )
    p = Paragraph(text, style)
    _, h = p.wrap(width, height)
    p.drawOn(c, x, y_top - h)
    return h


def rounded_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: colors.Color, stroke: colors.Color | None = None) -> None:
    c.setFillColor(fill)
    if stroke is None:
        c.setStrokeColor(fill)
    else:
        c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1 if stroke else 0)


def draw_line_chart(
    c: canvas.Canvas,
    rows: list[dict[str, float | datetime]],
    metrics: dict[str, float | str],
    x: float,
    y: float,
    w: float,
    h: float,
) -> None:
    chart_rows = [row for row in rows if row["date"] >= datetime(2025, 1, 1)]
    left, right, bottom, top = 34, 62, 25, 31
    px0, px1 = x + left, x + w - right
    py0, py1 = y + bottom, y + h - top
    y_max = 60.0

    def px(index: int) -> float:
        return px0 + (px1 - px0) * index / (len(chart_rows) - 1)

    def py(value: float) -> float:
        return py0 + (py1 - py0) * value / y_max

    c.setFont("ArialBold", 9.2)
    c.setFillColor(INK)
    c.drawString(x, y + h - 9, "Paid AI adoption among Ramp businesses (%)")
    c.setFont("Arial", 7.2)
    c.setFillColor(MUTED)
    c.drawRightString(x + w, y + h - 9, "Monthly, Jan 2025-Oct 2026")

    c.saveState()
    c.setFont("Arial", 6.4)
    c.setFillColor(MUTED)
    c.translate(x + 6, (py0 + py1) / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "Adoption share (%)")
    c.restoreState()
    c.setFont("Arial", 6.4)
    c.setFillColor(MUTED)
    c.drawCentredString((px0 + px1) / 2, y - 1, "Month")

    c.setLineWidth(0.6)
    for tick in range(0, 61, 10):
        yy = py(tick)
        c.setStrokeColor(LIGHT)
        c.line(px0, yy, px1, yy)
        c.setFillColor(MUTED)
        c.setFont("Arial", 6.7)
        c.drawRightString(px0 - 6, yy - 2.2, f"{tick}")

    label_months = {(1, 2025), (4, 2025), (7, 2025), (10, 2025), (1, 2026), (4, 2026), (7, 2026), (10, 2026)}
    for i, row in enumerate(chart_rows):
        dt = row["date"]
        if (dt.month, dt.year) in label_months:
            c.setFillColor(MUTED)
            c.setFont("Arial", 6.7)
            c.drawCentredString(px(i), y + 7, dt.strftime("%b '%y"))

    series = [
        ("overall", "Any AI provider", NAVY, 2.4, None),
        ("anthropic", "Anthropic", ORANGE, 2.6, None),
        ("openai", "OpenAI", BLUE, 2.6, None),
        ("minimum_overlap", "Minimum overlap", PURPLE, 1.8, [4, 3]),
    ]
    for key, _, color, width, dash in series:
        c.setStrokeColor(color)
        c.setLineWidth(width)
        c.setDash(dash or [])
        points = [(px(i), py(float(row[key]))) for i, row in enumerate(chart_rows)]
        path = c.beginPath()
        path.moveTo(points[0][0], points[0][1])
        for point_x, point_y in points[1:]:
            path.lineTo(point_x, point_y)
        c.drawPath(path, stroke=1, fill=0)
        c.setDash([])
        c.setFillColor(color)
        c.circle(points[-1][0], points[-1][1], 2.6, fill=1, stroke=0)

    latest = chart_rows[-1]
    label_specs = [
        ("overall", "Any AI", NAVY, 2),
        ("anthropic", "Anthropic", ORANGE, 7),
        ("openai", "OpenAI", BLUE, -7),
        ("minimum_overlap", "Minimum overlap", PURPLE, 0),
    ]
    for key, name, color, dy in label_specs:
        yy = py(float(latest[key])) + dy
        c.setFillColor(color)
        c.setFont("ArialBold", 6.8)
        c.drawString(px1 + 6, yy - 1, f"{name} {float(latest[key]):.1f}%")

    cross_index = next(i for i, row in enumerate(chart_rows) if float(row["anthropic"]) > float(row["openai"]))
    cross_row = chart_rows[cross_index]
    cx = px(cross_index)
    cy = py((float(cross_row["anthropic"]) + float(cross_row["openai"])) / 2)
    c.setStrokeColor(ORANGE)
    c.setLineWidth(0.8)
    c.setDash([2, 2])
    c.line(cx, cy + 6, cx, py1 - 5)
    c.setDash([])
    c.setFillColor(ORANGE)
    c.setFont("ArialBold", 6.7)
    c.drawCentredString(cx, py1 + 5, "Anthropic passes OpenAI")

    rounded_box(c, px0 + 8, py1 - 47, 126, 38, colors.HexColor("#F2EEFC"))
    c.setFillColor(PURPLE)
    c.setFont("ArialBold", 12.5)
    c.drawString(px0 + 18, py1 - 27, f">= {float(metrics['minimum_overlap_share']):.1f}%")
    c.setFont("Arial", 6.3)
    c.setFillColor(INK)
    c.drawString(px0 + 18, py1 - 38, "of AI adopters paid both in October*")


def build_pdf(rows: list[dict[str, float | datetime]], metrics: dict[str, float | str]) -> None:
    PDF_FILE.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("Arial", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("ArialBold", FONT_BOLD))
    c = canvas.Canvas(str(PDF_FILE), pagesize=LETTER)
    finding_headline = (
        f"At least {float(metrics['minimum_overlap_share']):.1f}% of AI-adopting Ramp businesses "
        "paid both Anthropic and OpenAI in October."
    )
    c.setTitle(finding_headline)
    c.setAuthor("Sreedeep Reddy Dugasani")
    c.setSubject("Analysis of AI provider adoption using the Ramp AI Index")
    c.setCreator("Sreedeep Reddy Dugasani")
    width, height = LETTER
    c.setTitle(finding_headline)
    c.setAuthor("Sreedeep Reddy Dugasani")

    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    c.setFillColor(TEAL)
    c.roundRect(42, 751, 168, 18, 9, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("ArialBold", 7.2)
    c.drawString(51, 757, "RAMP AI INDEX  |  PROVIDER ADOPTION")

    paragraph(c, finding_headline, 42, 741, 528, 74, size=22.5, leading=24.5, color=NAVY, bold=True)
    deck = (
        "Steady OpenAI adoption points to expansion, not a one-for-one exodus."
    )
    paragraph(c, deck, 42, 679, 528, 42, size=10.2, leading=13.2, color=MUTED)

    draw_line_chart(c, rows, metrics, 42, 385, 528, 244)
    chart_source = (
        'Source: <link href="https://ramp.com/data/ai-index"><u>Ramp Data (ramp.com/data)</u></link>, October 2026.'
    )
    paragraph(c, chart_source, 42, 380, 528, 12, size=6.2, leading=7.2, color=MUTED)

    box_y, box_h, gap = 238, 126, 12
    box_w = (528 - gap) / 2
    rounded_box(c, 42, box_y, box_w, box_h, colors.HexColor("#FFF5F0"), colors.HexColor("#F4D8CB"))
    rounded_box(c, 42 + box_w + gap, box_y, box_w, box_h, colors.HexColor("#EFF8F5"), colors.HexColor("#C9E7DE"))

    c.setFillColor(ORANGE)
    c.setFont("ArialBold", 8.2)
    c.drawString(55, box_y + box_h - 20, "EXPLANATION 1  |  PROVIDER SWITCHING")
    switching = (
        "<b>Supports it:</b> Anthropic passed OpenAI in May; Ramp reports low lock-in.<br/><br/>"
        "<b>Weakens it:</b> OpenAI stayed near 41%; an exodus should reduce it."
    )
    paragraph(c, switching, 55, box_y + box_h - 31, box_w - 26, 88, size=8.1, leading=10.2, color=INK)

    c.setFillColor(TEAL)
    c.setFont("ArialBold", 8.2)
    c.drawString(55 + box_w + gap, box_y + box_h - 20, "EXPLANATION 2  |  MULTI-PROVIDER EXPANSION")
    expansion = (
        f"<b>Supports it:</b> Overall adoption rose {float(metrics['overall_change']):.1f} points while OpenAI stayed flat; "
        f"at least {float(metrics['minimum_overlap_share']):.1f}% paid both.<br/><br/>"
        "<b>Best fit:</b> Firms added Anthropic alongside OpenAI."
    )
    paragraph(c, expansion, 55 + box_w + gap, box_y + box_h - 31, box_w - 26, 90, size=8.1, leading=10.2, color=INK)

    rounded_box(c, 42, 171, 528, 52, NAVY)
    c.setFillColor(colors.HexColor("#7CE4C8"))
    c.setFont("ArialBold", 8)
    c.drawString(55, 205, "VERDICT")
    verdict = (
        "Buyers should plan for multiple providers. Switching remains possible; expansion fits better. "
        "Microsoft's Oct. 28 launch supports plausibility, not cause."
    )
    paragraph(c, verdict, 55, 199, 500, 30, size=9, leading=11.2, color=WHITE)

    c.setFillColor(INK)
    c.setFont("ArialBold", 7.4)
    c.drawString(42, 148, "HOW THE LOWER BOUND WORKS")
    lower_bound = (
        "44.8% + 40.6% - 56.8% = 28.5% of Ramp firms, or 50.3% of AI adopters. "
        "Other vendors make this a minimum, not an exact share."
    )
    paragraph(c, lower_bound, 42, 140, 528, 42, size=7.4, leading=9.2, color=MUTED)

    c.setStrokeColor(LIGHT)
    c.setLineWidth(0.7)
    c.line(42, 91, 570, 91)
    c.setFillColor(INK)
    c.setFont("ArialBold", 6.8)
    c.drawString(42, 79, "SOURCE AND METHOD")
    source = (
        'Sources: <link href="https://ramp.com/data/ai-index"><u>Ramp AI Index</u></link>; '
        '<link href="https://fred.stlouisfed.org/release?rid=23"><u>FRED/Ramp series</u></link>; '
        '<link href="https://ramp.com/reports/2026-summer-spending-benchmarks"><u>Ramp Summer 2026 report</u></link>. '
        '<link href="https://blogs.microsoft.com/blog/2026/10/28/introducing-the-microsoft-copilot-harness-unlocking-the-potential-of-truly-multi-model-agentic-work/"><u>Microsoft multi-model announcement</u></link>. '
        "Monthly through Oct 2026. Adoption means an observed business payment."
    )
    paragraph(c, source, 42, 72, 340, 46, size=6.0, leading=7.3, color=MUTED)

    c.setFillColor(INK)
    c.setFont("ArialBold", 6.8)
    c.drawString(396, 79, "LIMITS")
    limits = (
        "Payments miss free and personal use. Ramp customers may not represent all U.S. firms; estimates can change."
    )
    paragraph(c, limits, 396, 72, 174, 44, size=6.3, leading=7.8, color=MUTED)

    c.setFillColor(MUTED)
    c.setFont("Arial", 5.7)
    c.drawRightString(570, 18, "*Minimum overlap from inclusion-exclusion; percentages rounded. Analysis by Sreedeep Reddy Dugasani.")
    c.showPage()
    c.save()
    DOWNLOAD_PDF.write_bytes(PDF_FILE.read_bytes())


def pil_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)


def wrap_pil(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = word if not line else f"{line} {word}"
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def build_cover(rows: list[dict[str, float | datetime]], metrics: dict[str, float | str]) -> None:
    width, height = 1800, 1200
    image = Image.new("RGB", (width, height), "#091522")
    draw = ImageDraw.Draw(image)

    for y in range(height):
        t = y / height
        base = (9, 21, 34)
        glow = (18, 50, 62)
        color = tuple(int(base[i] * (1 - t) + glow[i] * t) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    for x in range(0, width, 120):
        draw.line((x, 0, x, height), fill="#132A38", width=1)
    for y in range(0, height, 120):
        draw.line((0, y, width, y), fill="#132A38", width=1)

    draw.rounded_rectangle((90, 70, 520, 120), radius=25, fill="#0C9A78")
    draw.text((118, 82), "RAMP AI INDEX  |  OCTOBER 2026", font=pil_font(23, True), fill="white")

    headline = f"At least {float(metrics['minimum_overlap_share']):.1f}% paid both Anthropic and OpenAI"
    hfont = pil_font(68, True)
    lines = wrap_pil(draw, headline, hfont, 690)
    y = 170
    for line in lines:
        draw.text((90, y), line, font=hfont, fill="#F7FAFC")
        y += 82
    deck = "Among AI-adopting Ramp businesses in October - evidence of expansion, not an exodus."
    dfont = pil_font(31)
    for line in wrap_pil(draw, deck, dfont, 720):
        draw.text((92, y + 20), line, font=dfont, fill="#B9C8D5")
        y += 42

    draw.rounded_rectangle((90, 665, 730, 1015), radius=28, fill="#10243A", outline="#28445A", width=2)
    draw.text((135, 715), f">= {float(metrics['minimum_overlap_share']):.1f}%", font=pil_font(96, True), fill="#79E0C4")
    draw.text((140, 830), "of AI adopters paid both", font=pil_font(38, True), fill="white")
    draw.text((140, 885), "Anthropic and OpenAI", font=pil_font(38, True), fill="white")
    draw.text((140, 950), "Minimum overlap, not an exact share", font=pil_font(24), fill="#AAB9C7")

    chart_left, chart_top, chart_right, chart_bottom = 870, 180, 1710, 1015
    draw.rounded_rectangle((835, 145, 1745, 1050), radius=32, fill="#0D1C2C", outline="#294155", width=2)
    draw.text((885, 190), "Paid adoption among Ramp businesses", font=pil_font(30, True), fill="white")
    draw.text((885, 230), "January 2025-October 2026", font=pil_font(22), fill="#9EB0BF")
    chart_rows = [row for row in rows if row["date"] >= datetime(2025, 1, 1)]
    plot_left, plot_right = chart_left + 25, chart_right - 260
    plot_top, plot_bottom = chart_top + 120, chart_bottom - 65

    def px(index: int) -> float:
        return plot_left + (plot_right - plot_left) * index / (len(chart_rows) - 1)

    def py(value: float) -> float:
        return plot_bottom - (plot_bottom - plot_top) * value / 60.0

    for tick in range(0, 61, 10):
        yy = py(tick)
        draw.line((plot_left, yy, plot_right, yy), fill="#294052", width=1)
        draw.text((plot_left - 48, yy - 11), str(tick), font=pil_font(18), fill="#8094A4")
    series = [
        ("overall", "Any AI", "#E9EFF5", 6),
        ("anthropic", "Anthropic", "#F07B4F", 7),
        ("openai", "OpenAI", "#5B8CFF", 7),
        ("minimum_overlap", "Minimum overlap", "#A68AFA", 5),
    ]
    for key, name, color, width_px in series:
        pts = [(px(i), py(float(row[key]))) for i, row in enumerate(chart_rows)]
        draw.line(pts, fill=color, width=width_px, joint="curve")
        ex, ey = pts[-1]
        draw.ellipse((ex - 7, ey - 7, ex + 7, ey + 7), fill=color)
        draw.text((ex + 18, ey - 15), f"{name} {float(chart_rows[-1][key]):.1f}%", font=pil_font(20, True), fill=color)
    for idx, row in enumerate(chart_rows):
        dt = row["date"]
        if (dt.month, dt.year) in {(1, 2025), (7, 2025), (1, 2026), (7, 2026), (10, 2026)}:
            label = dt.strftime("%b '%y")
            box = draw.textbbox((0, 0), label, font=pil_font(18))
            draw.text((px(idx) - (box[2] - box[0]) / 2, plot_bottom + 20), label, font=pil_font(18), fill="#8094A4")

    draw.text((90, 1100), "Source: Ramp AI Index via FRED. Paid transactions; free and personal-account use are not captured.", font=pil_font(22), fill="#9EB0BF")
    draw.text((1710, 1100), "Sreedeep Reddy Dugasani", anchor="ra", font=pil_font(22, True), fill="#79E0C4")
    COVER_FILE.parent.mkdir(parents=True, exist_ok=True)
    image.save(COVER_FILE, "PNG", optimize=True)
    DOWNLOAD_COVER.write_bytes(COVER_FILE.read_bytes())


def main() -> None:
    rows = load_data()
    metrics = get_metrics(rows)
    write_summary(metrics)
    build_pdf(rows, metrics)
    build_cover(rows, metrics)
    print(f"PDF: {PDF_FILE}")
    print(f"Download PDF: {DOWNLOAD_PDF}")
    print(f"Cover: {DOWNLOAD_COVER}")
    print(f"Minimum overlap share: {float(metrics['minimum_overlap_share']):.1f}%")


if __name__ == "__main__":
    main()
