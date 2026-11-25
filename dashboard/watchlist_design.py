"""Local company marks and the watchlist's compact quote-row presentation."""
import base64
from functools import lru_cache
import html
import json
import math
from pathlib import Path


ASSET_DIR = Path(__file__).resolve().parent / "assets" / "company-icons"
ICON_MANIFEST = json.loads((ASSET_DIR / "manifest.json").read_text())
FALLBACK_COLORS = ["#2962ff", "#7c3aed", "#087f8c", "#a43b57", "#926417", "#345482"]
FUND_SYMBOLS = {"SPY", "QQQ", "DIA"}

WATCHLIST_STYLE = """<style>
  .st-key-watchlist_panel {--watchlist-row-height:76px;background:#fff;border:1px solid #e0e3eb;border-radius:18px;padding:.9rem;gap:.6rem;}
  .watchlist-heading {font-size:1.12rem;font-weight:750;letter-spacing:-.025em;margin:0;color:#131722;}
  .watchlist-summary {font-size:.8rem;line-height:1.4;color:#787b86;margin:.2rem 0 0;}
  .watchlist-group-title {display:flex;align-items:center;justify-content:space-between;color:#787b86;font-size:.75rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;margin:.6rem .1rem .15rem;}
  .watchlist-count {font-size:.75rem;color:#787b86;border:1px solid #e0e3eb;border-radius:20px;padding:0 .4rem;letter-spacing:0;}
  div[class*="st-key-wlrow_"] {position:relative!important;gap:0!important;height:var(--watchlist-row-height)!important;min-height:var(--watchlist-row-height)!important;}
  div[class*="st-key-wlrow_"] > div:has([data-testid="stButton"]) {position:absolute!important;inset:0!important;z-index:2!important;}
  div[class*="st-key-wlrow_"] [data-testid="stButton"],
  div[class*="st-key-wlrow_"] [data-testid="stButton"] button {position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-height:100%!important;margin:0!important;}
  div[class*="st-key-wlrow_"] [data-testid="stButton"] button {background:transparent!important;border:0!important;border-radius:12px!important;box-shadow:none!important;}
  div[class*="st-key-wlrow_"] [data-testid="stButton"] button > div {opacity:0;}
  div[class*="st-key-wlrow_"]:hover .watchlist-row {border-color:#b2b5be;}
  div[class*="st-key-wlrow_"]:has(button:focus-visible) .watchlist-row {outline:2px solid #2962ff;outline-offset:2px;}
  .watchlist-row {position:relative;display:grid;grid-template-columns:36px minmax(0,1fr) auto;align-items:center;gap:.6rem;height:var(--watchlist-row-height);min-height:var(--watchlist-row-height);padding:.65rem .6rem;border:1px solid #ebeef3;border-radius:12px;background:#fff;transition:border-color .15s;}
  .watchlist-row.is-selected {border-color:#2962ff;box-shadow:inset 3px 0 0 #2962ff;}
  .watchlist-avatar {width:36px;height:36px;display:grid;place-items:center;flex-shrink:0;border-radius:50%;border:1px solid #e0e3eb;background:#fff;overflow:hidden;color:#fff;font-size:.8rem;font-weight:750;letter-spacing:-.03em;}
  .watchlist-avatar img {display:block;width:23px;height:23px;object-fit:contain;}
  .watchlist-avatar.is-index {font-size:.8rem;border:0;}
  .watchlist-avatar.is-fund {background:#fff;color:#2962ff;font-size:.65rem;letter-spacing:.01em;}
  .watchlist-identity {min-width:0;}
  .watchlist-name {color:#131722;font-size:.95rem;line-height:1.3;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .watchlist-ticker {display:inline-block;margin-top:.35rem;padding:.12rem .35rem;border-radius:5px;background:#f2f4f7;color:#6a6d78;font-size:.75rem;line-height:1.25;font-weight:650;letter-spacing:.025em;}
  .watchlist-quote {min-width:0;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
  .watchlist-last {font-size:.94rem;font-weight:700;color:#131722;line-height:1.3;}
  .watchlist-change {font-size:.875rem;font-weight:650;line-height:1.4;margin-top:.35rem;}
  .watchlist-change.is-up {color:#087f6d;}
  .watchlist-change.is-down {color:#e3364f;}
  .watchlist-change.is-flat {color:#787b86;}
  .st-key-watchlist_header [data-testid="stPopover"] button {min-height:2.2rem;border-radius:10px;padding:.2rem .45rem;}
  .st-key-watchlist_panel [data-testid="stCaptionContainer"] p {font-size:.8rem;line-height:1.55;}
  @media(min-width:760px) and (max-width:1150px) {
    .st-key-watchlist_panel {--watchlist-row-height:92px;}
    .watchlist-row {grid-template-columns:30px minmax(0,1fr);gap:.5rem;padding:.6rem;}
    .watchlist-avatar {width:30px;height:30px;}
    .watchlist-avatar img {width:21px;height:21px;}
    .watchlist-quote {grid-column:2;text-align:left;display:flex;align-items:baseline;gap:.45rem;}
    .watchlist-change {margin-top:0;}
  }
</style>"""


def _number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def quote_labels(last, change, change_pct, *, is_index=False):
    last, change, change_pct = map(_number, (last, change, change_pct))
    last_text = "—" if last is None else ("" if is_index else "$") + f"{last:,.2f}"
    if change is not None and change_pct is not None:
        change_text = f"{change:+,.2f} ({change_pct:+.2f}%)"
    elif change_pct is not None:
        change_text = f"{change_pct:+.2f}%"
    elif change is not None:
        change_text = f"{change:+,.2f}"
    else:
        change_text = "—"
    direction = change_pct if change_pct is not None else (change or 0)
    state = "is-up" if direction > 0 else "is-down" if direction < 0 else "is-flat"
    return last_text, change_text, state


@lru_cache(maxsize=128)
def _brand_image(ticker):
    meta = ICON_MANIFEST.get(ticker)
    if not meta:
        return None
    path = ASSET_DIR / meta["file"]
    if not path.is_file():
        return None
    if path.suffix == ".svg":
        color = "#FFC72C" if ticker == "MCD" else meta["color"]
        data = path.read_text().replace("<svg ", f'<svg fill="{color}" ', 1).encode()
        mime = "image/svg+xml"
    else:
        data = path.read_bytes()
        mime = meta["mime"]
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def company_icon_html(ticker, *, index_badge=None, index_color="#2962ff"):
    if index_badge is not None:
        return f'<span class="watchlist-avatar is-index" style="background:{html.escape(index_color, quote=True)}">{html.escape(str(index_badge))}</span>'
    if ticker in FUND_SYMBOLS:
        return '<span class="watchlist-avatar is-fund">ETF</span>'
    image = _brand_image(ticker)
    if image:
        background = ' style="background:#DA291C;border-color:#DA291C"' if ticker == "MCD" else ""
        return f'<span class="watchlist-avatar"{background}><img src="{image}" alt="" width="23" height="23"></span>'
    letters = "".join(char for char in ticker.upper() if char.isalnum())[:2] or "?"
    color = FALLBACK_COLORS[sum((i + 1) * ord(char) for i, char in enumerate(ticker)) % len(FALLBACK_COLORS)]
    return f'<span class="watchlist-avatar" style="background:{color};border-color:{color}">{html.escape(letters)}</span>'


def watchlist_row_html(ticker, name, symbol, last, change, change_pct, *, selected=False,
                       index_badge=None, index_color="#2962ff"):
    last_text, change_text, state = quote_labels(last, change, change_pct, is_index=index_badge is not None)
    avatar = company_icon_html(ticker, index_badge=index_badge, index_color=index_color)
    selected_class = " is-selected" if selected else ""
    return (
        f'<div class="watchlist-row{selected_class}" aria-hidden="true">{avatar}'
        f'<div class="watchlist-identity"><div class="watchlist-name" title="{html.escape(name, quote=True)}">{html.escape(name)}</div>'
        f'<span class="watchlist-ticker">{html.escape(symbol)}</span></div>'
        f'<div class="watchlist-quote"><div class="watchlist-last">{html.escape(last_text)}</div>'
        f'<div class="watchlist-change {state}">{html.escape(change_text)}</div></div></div>'
    )
