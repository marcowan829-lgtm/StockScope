"""Small, annotated SVG lessons. All figures are fictional teaching examples."""
from html import escape


INK = "#263449"
GREEN = "#087f68"
RED = "#cd3b4f"
BLUE = "#2863bf"
ORANGE = "#a35312"
PURPLE = "#7551ad"

EXAMPLE_SUMMARIES = {
    "price_line": "Read time across, price up the side, then compare the first and last values.",
    "price_area": "Read the top edge. The shaded space is decoration, not money or trading volume.",
    "price_baseline": "Colour compares price with the reference line. A price can rise while staying below it.",
    "price_candle": "The body shows start to finish; the thin wicks show the highest and lowest prices.",
    "intraday": "One candle is one time block. Here it is five minutes, not a whole day.",
    "stock": "One candle is one trading day. Its colour compares that day's close with its open.",
    "heatmap": "Read one cell at a time: group + month + average percentage change.",
    "ranking": "The bar measures percentage change, not the stock's dollar price.",
    "gainers": "These are daily percentage changes, even when your look-back window is a year.",
    "losers": "A bar left of zero shows a loss. Compare the percentages, not just the colours.",
    "volume": "A longer bar means more shares traded, not more profit or more dollars invested.",
    "comparison": "Everyone begins at 100. A level of 120 means +20%; 90 means −10%.",
    "risk": "Read both directions: up/down is past return; left/right is how variable daily returns were.",
}


def _text(x, y, value, *, size=13, colour=INK, anchor="start", weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{colour}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>'


def _line(x1, y1, x2, y2, colour="#c9d0d8", width=1.2, dash=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="{width}" stroke-dasharray="{dash}"/>'


def _ring(x, y, rx=22, ry=14):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="none" stroke="{ORANGE}" stroke-width="2" transform="rotate(-6 {x} {y})"/>'


def _note(prefix, number, x, y, lines, target, width=198):
    colour = [BLUE, PURPLE, ORANGE][number - 1]
    tint = ["#edf4ff", "#f3edfc", "#fff0c9"][number - 1]
    height = 58
    tx, ty = target
    sx, sy = x + width / 2, y + height if ty > y + height else y
    bend_x = (sx + tx) / 2 + (18 if number == 2 else -18)
    bend_y = (sy + ty) / 2
    arrow = f'<path d="M {sx} {sy} Q {bend_x} {bend_y} {tx} {ty}" fill="none" stroke="{colour}" stroke-width="2" stroke-linecap="round" marker-end="url(#{prefix}-arrow-{number})"/>'
    card = f'<g transform="rotate({-1 if number != 2 else 1} {x + width / 2} {y + height / 2})"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{tint}" stroke="{colour}" stroke-opacity=".25"/><circle cx="{x + 18}" cy="{y + 20}" r="11" fill="{colour}"/>'
    card += _text(x + 18, y + 24, number, size=13, colour="#fff", anchor="middle", weight=700)
    for i, content in enumerate(lines):
        card += f'<text x="{x + 36}" y="{y + 22 + i * 19}" font-size="13.5" fill="{INK}" font-family="Chalkboard SE, Comic Sans MS, Trebuchet MS, sans-serif">{escape(content)}</text>'
    return arrow + card + '</g>'


def _axes(*, y_label="Price ($)", x_label="Time →", zero_y=302):
    marks = ''.join(_line(65, y, 382, y, "#e8e7e0", 1) for y in (160, 210, 260))
    return (marks + _line(65, 137, 65, zero_y, "#8190a3")
            + _line(65, zero_y, 382, zero_y, "#8190a3")
            + _text(65, 127, y_label, size=12)
            + _text(382, zero_y + 27, x_label, size=12, anchor="end"))


def _price(topic, prefix):
    if topic == "price_baseline":
        xs = [80, 145, 210, 290, 365]
        values = [100, 98, 99, 102, 101]
        y = lambda v: 215 - (v - 100) * 30
        body = _axes() + _line(65, y(100), 382, y(100), "#6e7887", dash="5 4")
        for i in range(len(xs) - 1):
            a, b = values[i], values[i + 1]
            if (a - 100) * (b - 100) < 0:
                cross_x = xs[i] + (xs[i + 1] - xs[i]) * (100 - a) / (b - a)
                body += _line(xs[i], y(a), cross_x, y(100), GREEN if a >= 100 else RED, 3)
                body += _line(cross_x, y(100), xs[i + 1], y(b), GREEN if b >= 100 else RED, 3)
            else:
                body += _line(xs[i], y(a), xs[i + 1], y(b), GREEN if max(a, b) > 100 else RED, 3)
        body += _text(60, y(100) - 5, "$100 reference", size=12)
        body += _text(145, y(98) + 18, "$98", colour=RED, anchor="middle")
        body += _text(210, y(99) - 12, "$99", colour=RED, anchor="middle")
        body += _text(290, y(102) - 10, "$102", colour=GREEN, anchor="middle")
        body += _ring(179, 260, 46, 27)
        return (body + _note(prefix, 1, 12, 49, ["Find the", "$100 reference."], (335, y(100)))
                + _note(prefix, 2, 230, 49, ["Above = green", "Below = red"], (290, y(102)))
                + _note(prefix, 3, 94, 357, ["$98 → $99 rises,", "but stays red!"], (179, 270)))
    values = [100, 103, 101, 107, 106, 110] if topic == "price_line" else [50, 51, 50.5, 53.5, 53, 55]
    xs = [80, 137, 194, 251, 308, 365]
    low, high = values[0], values[-1]
    ys = [280 - (value - low) / (high - low) * 120 for value in values]
    body = _axes()
    if topic == "price_area":
        points = ' '.join(f'{x},{y}' for x, y in zip(xs, ys))
        body += f'<polygon points="80,302 {points} 365,302" fill="{GREEN}" opacity=".13"/>'
    body += f'<polyline points="{" ".join(f"{x},{y}" for x,y in zip(xs,ys))}" fill="none" stroke="{GREEN}" stroke-width="3.5" stroke-linejoin="round"/>'
    for x, y in [(xs[0], ys[0]), (xs[-1], ys[-1])]:
        body += f'<circle cx="{x}" cy="{y}" r="4" fill="{GREEN}"/>'
    body += _text(76, 272, f'${low:g}', anchor="end", size=12)
    body += _text(367, 148, f'${high:g}', colour=GREEN, weight=700)
    body += _text(80, 323, "Start", size=12)
    body += _ring(380, 144, 26, 14)
    change = (high / low - 1) * 100
    note3 = ["Read the top edge.", "Shading ≠ volume!"] if topic == "price_area" else [f"${low:g} → ${high:g}", f"That's a +{change:.0f}% change."]
    return (body + _note(prefix, 1, 12, 49, ["Read from earlier", "to later →"], (183, 302))
            + _note(prefix, 2, 230, 49, ["Higher on the page", "= higher price."], (365, 160))
            + _note(prefix, 3, 94, 357, note3, (265, 250) if topic == "price_area" else (308, ys[4])))


def _candles(topic, prefix):
    first = {"price_candle": (100, 105, 98, 103), "intraday": (100, 102, 99, 101), "stock": (100, 106, 97, 104)}[topic]
    second = (first[3] + 1, first[1] + 1, first[2], first[0] + 1)
    minimum, maximum = first[2] - 1, second[1] + 1
    y = lambda v: 266 - (v - minimum) / (maximum - minimum) * 122
    body = _axes(zero_y=280)
    for x, (open_, high, low, close), colour in [(151, first, GREEN), (291, second, RED)]:
        body += _line(x, y(high), x, y(low), colour, 2.5)
        body += f'<rect x="{x - 17}" y="{min(y(open_), y(close))}" width="34" height="{max(abs(y(open_) - y(close)),2)}" rx="1" fill="{colour}"/>'
        for value in [high, low]:
            body += _line(x - 8, y(value), x + 8, y(value), colour, 2)
    open_, high, low, close = first
    body += _text(127, y(close) + 4, f'Close ${close}', size=12, anchor="end")
    body += _text(127, y(open_) + 4, f'Open ${open_}', size=12, anchor="end")
    body += _text(173, y(high) + 4, f'High ${high}', size=12)
    body += _text(173, y(low) + 4, f'Low ${low}', size=12)
    body += _text(65, 302, "Volume", size=12)
    body += f'<rect x="134" y="318" width="34" height="16" fill="{GREEN}"/><rect x="274" y="302" width="34" height="32" fill="{RED}"/>'
    body += _text(151, 348, "10:00" if topic == "intraday" else "Day 1", anchor="middle", size=12)
    body += _text(291, 348, "10:05" if topic == "intraday" else "Day 2", anchor="middle", size=12)
    return (body + _note(prefix, 1, 12, 49, ["Body = start", "to finish."], (151, (y(open_) + y(close)) / 2))
            + _note(prefix, 2, 230, 49, ["Thin wicks show", "the high + low."], (151, y(high)))
            + _note(prefix, 3, 94, 357, ["Taller volume bar", "= more shares traded."], (291, 310)))


def _heatmap(prefix):
    body = ''
    months, groups = ["Jan", "Feb", "Mar"], ["Tech", "Energy"]
    values = [[4, -2, 1], [-3, 3, 0]]
    for col, month in enumerate(months):
        body += _text(136 + col * 90, 146, month, anchor="middle")
    for row, group in enumerate(groups):
        body += _text(83, 191 + row * 64, group, anchor="end", size=12)
        for col, value in enumerate(values[row]):
            x, y = 94 + col * 90, 162 + row * 64
            fill = "#c2e6d7" if value > 0 else "#f4c9ca" if value < 0 else "#f7edbf"
            body += f'<rect x="{x}" y="{y}" width="84" height="58" rx="5" fill="{fill}"/>'
            body += _text(x + 42, y + 34, f'{value:+d}%' if value else '0%', anchor="middle", size=17, weight=700)
    body += _ring(136, 191, 35, 23)
    body += _text(224, 313, "One cell = one group, one month", anchor="middle", size=12)
    return (body + _note(prefix, 1, 12, 49, ["Choose a group", "+ a month."], (94, 184))
            + _note(prefix, 2, 230, 49, ["Green = up", "Red = down"], (226, 190))
            + _note(prefix, 3, 80, 357, ["(+10% − 2%) ÷ 2", "= +4% group average"], (136, 214), width=228))


def _bars(topic, prefix):
    values = {"ranking": [20, 10, 5], "gainers": [3, 2, 1], "losers": [-5, -3, -1], "volume": [2, 1, 0.5]}[topic]
    negative, volume = topic == "losers", topic == "volume"
    zero = 348 if negative else 100
    scale = 235 / max(abs(value) for value in values)
    body = _line(zero, 144, zero, 301, "#8190a3") + _line(100, 301, 348, 301, "#8190a3")
    for i, value in enumerate(values):
        top, end = 158 + i * 46, zero + value * scale
        colour = RED if value < 0 else GREEN
        body += _text(88, top + 20, f'Stock {chr(65+i)}', anchor="end", size=12)
        body += f'<rect x="{min(zero,end)}" y="{top}" width="{abs(value)*scale}" height="27" rx="3" fill="{colour}"/>'
        label = f'{value:g}M' if volume else f'{value:+g}%'
        body += _text(end + (8 if negative else 7), top + 19, label, size=13, colour="#fff" if negative else INK)
    body += _text(zero, 320, "0", anchor="middle", size=12)
    body += _text(348, 340, "Shares traded (M = million)" if volume else "Price change (%)", anchor="end", size=12)
    if volume:
        third, second = ["2M = 2m shares", "NOT $2m of money."], ["Longer = more", "shares traded." ]
    elif topic == "ranking":
        third, second = ["$100 → $120", "means +20%."], ["Longer = bigger", "percentage change."]
    elif topic == "gainers":
        third, second = ["$50 → $51", "means +2% today."], ["Compare daily", "percentage moves."]
    else:
        third, second = ["$80 → $76", "means −5% today."], ["Left of zero", "= a price fall."]
    return (body + _note(prefix, 1, 12, 49, ["Each row is", "one stock."], (86, 178))
            + _note(prefix, 2, 230, 49, second, (min(zero+values[0]*scale,350), 165))
            + _note(prefix, 3, 94, 357, third, (zero+values[1]*scale, 219)))


def _comparison(prefix):
    body = _axes(y_label="Starting level = 100")
    body += _line(65, 252, 382, 252, "#8190a3", dash="5 4")
    body += f'<polyline points="80,252 145,225 205,238 280,185 360,160" fill="none" stroke="{BLUE}" stroke-width="3"/>'
    body += f'<polyline points="80,252 145,267 205,247 280,275 360,298" fill="none" stroke="{PURPLE}" stroke-width="3"/>'
    body += _text(60, 256, "100", anchor="end", size=12)
    body += _text(365, 154, "120", colour=BLUE, weight=700)
    body += _text(365, 294, "90", colour=PURPLE, weight=700)
    body += _text(251, 176, "Stock A", size=12, colour=BLUE)
    body += _text(251, 296, "Stock B", size=12, colour=PURPLE)
    body += _ring(80, 252, 12, 12)
    return (body + _note(prefix, 1, 12, 49, ["Start together", "at 100."], (80, 246))
            + _note(prefix, 2, 230, 49, ["120 means +20%", "since the start."], (360, 160))
            + _note(prefix, 3, 94, 357, ["90 means −10%.", "Not a share price!"], (360, 298)))


def _risk(prefix):
    body = _axes(y_label="Past return (%)", x_label="Annualized volatility (%)", zero_y=302)
    body += _line(65, 281, 382, 281, "#8190a3", dash="5 4")
    for y, label in [(281, "0%"), (221, "+5%"), (161, "+10%")]:
        body += _text(59, y + 4, label, anchor="end", size=12)
    for x, label in [(145, "20%"), (330, "40%")]:
        body += _text(x, 319, label, anchor="middle", size=12)
    for x, y, label, colour in [(145, 161, "A", BLUE), (330, 221, "B", PURPLE)]:
        body += f'<circle cx="{x}" cy="{y}" r="9" fill="{colour}"/>'
        body += _text(x + 14, y + 4, label, weight=700)
    body += _ring(145, 161, 17, 16)
    return (body + _note(prefix, 1, 12, 49, ["Up / down", "= past return."], (145, 161))
            + _note(prefix, 2, 230, 49, ["Further right", "= bigger swings."], (330, 221))
            + _note(prefix, 3, 80, 357, ["A: 20% volatility", "+10% past return"], (145, 180), width=228))


def annotated_example(topic: str) -> str:
    """Return an accessible drawing without scripts, external assets or live data."""
    summary = EXAMPLE_SUMMARIES[topic]
    prefix = f'lesson-{topic}'
    markers = ''.join(f'<marker id="{prefix}-arrow-{i}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M 0 0 L 6 3.5 L 0 7" fill="none" stroke="{colour}" stroke-width="1.5"/></marker>' for i, colour in enumerate([BLUE, PURPLE, ORANGE], start=1))
    if topic in {"price_line", "price_area", "price_baseline"}:
        marks = _price(topic, prefix)
    elif topic in {"price_candle", "intraday", "stock"}:
        marks = _candles(topic, prefix)
    elif topic == "heatmap":
        marks = _heatmap(prefix)
    elif topic in {"ranking", "gainers", "losers", "volume"}:
        marks = _bars(topic, prefix)
    elif topic == "comparison":
        marks = _comparison(prefix)
    else:
        marks = _risk(prefix)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 446" width="100%" role="img" aria-labelledby="{prefix}-title {prefix}-desc" style="display:block;background:#fffdf6;border:1px solid #e6e0d0;border-radius:14px;font-family:Trebuchet MS,Arial,sans-serif">
<title id="{prefix}-title">Annotated teaching example: {escape(topic.replace('_',' '))}</title>
<desc id="{prefix}-desc">Fictional figures. {escape(summary)} Follow notes 1, 2 and 3 and their arrows.</desc>
<defs>{markers}</defs>
{_text(18, 28, 'A LITTLE CHART FIELD NOTE', size=12, colour=BLUE, weight=700)}
{marks}
{_text(220, 435, 'Made-up numbers · learn the picture, not a prediction', size=11, colour='#667084', anchor='middle')}
</svg>'''
