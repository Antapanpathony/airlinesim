"""UI theme constants and helpers for Airline Empire"""
import tkinter as tk
from tkinter import ttk

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = '#07101e'   # deepest background
BG2      = '#0d1d35'   # panel background
BG3      = '#122540'   # card / inset background
BORDER   = '#1a3a5c'   # borders
ACCENT   = '#1a78c2'   # primary blue
ACCENT2  = '#0fa3c2'   # teal accent
GOLD     = '#e8b04b'   # gold / highlight
GREEN    = '#27c870'   # profit / positive
RED      = '#e74c3c'   # loss / negative
ORANGE   = '#e8843a'   # warning
TEXT     = '#d4e9f7'   # primary text
TEXT2    = '#6fa8c8'   # secondary text
MUTED    = '#3d6080'   # muted text
WHITE    = '#ffffff'
HOVER    = '#1d3a60'
SEL      = '#1a4a80'

# Sky gradient colors for map
SKY_TOP  = '#07101e'
SKY_BOT  = '#0a1f3a'
LAND     = '#1a3326'   # continent fill
LAND2    = '#1f3d2e'   # continent highlight
OCEAN    = '#081828'   # ocean fill
ROUTE_C  = '#1a78c2'   # route line
ROUTE_A  = '#27c870'   # active route line
CITY_C   = '#e8b04b'   # city dot
HUB_C    = '#e8b04b'   # hub dot (larger)

# Fonts – fall back gracefully
def _pick_font(*candidates):
    import tkinter.font as tkfont
    try:
        avail = tkfont.families()
        for c in candidates:
            if c in avail:
                return c
    except Exception:
        pass
    return 'Helvetica'

_SANS = _pick_font('Inter', 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', 'Arial')
_MONO = _pick_font('JetBrains Mono', 'Fira Code', 'Consolas', 'Courier New', 'Courier')

F_TITLE   = (_SANS, 32, 'bold')
F_HEAD    = (_SANS, 15, 'bold')
F_SUBHEAD = (_SANS, 12, 'bold')
F_BODY    = (_SANS, 11)
F_SMALL   = (_SANS, 9)
F_MONO    = (_MONO, 10)
F_BIG_NUM = (_SANS, 22, 'bold')
F_MED_NUM = (_SANS, 16, 'bold')

def apply_theme(root: tk.Tk):
    """Apply ttk style theme."""
    style = ttk.Style(root)
    style.theme_use('clam')

    style.configure('.',
        background=BG2, foreground=TEXT,
        fieldbackground=BG3, troughcolor=BG,
        bordercolor=BORDER, darkcolor=BG, lightcolor=BG2,
        insertcolor=TEXT, arrowcolor=TEXT2,
        font=F_BODY)

    style.configure('TFrame', background=BG2)
    style.configure('Card.TFrame', background=BG3, relief='flat')
    style.configure('TLabel', background=BG2, foreground=TEXT, font=F_BODY)
    style.configure('Dim.TLabel', background=BG2, foreground=TEXT2, font=F_SMALL)
    style.configure('Card.TLabel', background=BG3, foreground=TEXT, font=F_BODY)
    style.configure('Head.TLabel', background=BG2, foreground=WHITE, font=F_HEAD)
    style.configure('Gold.TLabel', background=BG2, foreground=GOLD, font=F_SUBHEAD)
    style.configure('Green.TLabel', background=BG2, foreground=GREEN, font=F_BODY)
    style.configure('Red.TLabel', background=BG2, foreground=RED, font=F_BODY)

    style.configure('TButton', background=ACCENT, foreground=WHITE,
        borderwidth=0, focusthickness=0, font=F_BODY, padding=(12, 6))
    style.map('TButton',
        background=[('active', ACCENT2), ('disabled', MUTED)],
        foreground=[('disabled', TEXT2)])

    style.configure('Gold.TButton', background=GOLD, foreground=BG, font=(_SANS,11,'bold'), padding=(14,7))
    style.map('Gold.TButton', background=[('active', '#f0c060')])

    style.configure('Danger.TButton', background='#8b1a1a', foreground=WHITE, padding=(12,6))
    style.map('Danger.TButton', background=[('active', RED)])

    style.configure('Nav.TButton', background=BG2, foreground=TEXT2,
        borderwidth=0, font=F_SUBHEAD, padding=(10,8), anchor='w')
    style.map('Nav.TButton',
        background=[('active', HOVER), ('selected', SEL)],
        foreground=[('active', WHITE), ('selected', GOLD)])

    style.configure('TNotebook', background=BG, tabmargins=0)
    style.configure('TNotebook.Tab',
        background=BG2, foreground=TEXT2, padding=(14, 6),
        font=F_BODY, borderwidth=0)
    style.map('TNotebook.Tab',
        background=[('selected', BG3)],
        foreground=[('selected', WHITE)])

    style.configure('Treeview', background=BG3, foreground=TEXT,
        fieldbackground=BG3, rowheight=26, font=F_BODY, borderwidth=0)
    style.configure('Treeview.Heading', background=BG2, foreground=GOLD,
        font=(_SANS,10,'bold'), relief='flat', borderwidth=0)
    style.map('Treeview',
        background=[('selected', SEL)],
        foreground=[('selected', WHITE)])

    style.configure('TScrollbar', background=BG2, troughcolor=BG,
        borderwidth=0, arrowsize=12)

    style.configure('TEntry', background=BG3, foreground=TEXT,
        fieldbackground=BG3, insertcolor=TEXT, bordercolor=BORDER,
        font=F_BODY, padding=5)

    style.configure('TCombobox', background=BG3, foreground=TEXT,
        fieldbackground=BG3, arrowcolor=TEXT2, font=F_BODY)
    style.map('TCombobox', fieldbackground=[('readonly', BG3)])

    style.configure('TSeparator', background=BORDER)
    style.configure('TProgressbar', background=ACCENT, troughcolor=BG3,
        borderwidth=0, thickness=6)

    return style


def colored_label(parent, text, color=TEXT, font=F_BODY, bg=BG2, **kw):
    return tk.Label(parent, text=text, fg=color, bg=bg, font=font, **kw)


def icon_btn(parent, text, command=None, color=ACCENT, fg=WHITE, font=F_BODY,
             padx=14, pady=6, **kw):
    btn = tk.Button(parent, text=text, command=command,
                    bg=color, fg=fg, font=font,
                    activebackground=ACCENT2, activeforeground=WHITE,
                    relief='flat', bd=0, cursor='hand2',
                    padx=padx, pady=pady, **kw)
    return btn


def rounded_frame(parent, bg=BG3, **kw):
    f = tk.Frame(parent, bg=bg, **kw)
    return f


def separator(parent, orient='horizontal', color=BORDER):
    if orient == 'horizontal':
        return tk.Frame(parent, bg=color, height=1)
    else:
        return tk.Frame(parent, bg=color, width=1)


def money_str(amount: float) -> str:
    """Format an exact dollar amount with comma separators."""
    if amount < 0:
        return f'-${abs(amount):,.0f}'
    return f'${amount:,.0f}'


def pax_str(n: int) -> str:
    if n >= 1_000_000:
        return f'{n/1_000_000:.1f}M'
    elif n >= 1000:
        return f'{n/1000:.0f}K'
    return str(n)


def km_str(k: float) -> str:
    return f'{k:,.0f} km'


def lerp_color(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f'#{r:02x}{g:02x}{b:02x}'
