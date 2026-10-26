"""Shared desktop typography, surfaces and accessible interaction states."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, ttk

from .widgets import ui_font

BG = "#F1F5FA"
SURFACE = "#FFFFFF"
INK = "#15263E"
MUTED = "#43536A"
PRIMARY = "#214F8C"
BORDER = "#CDD7E5"
BLUE_TINT = "#EDF2FF"
RED = "#A62F3A"
GREEN = "#145C46"
NAVY = "#1D3152"
NAV_TEXT = "#F3F6FC"
NAV_MUTED = "#CAD6E7"
NAV_SELECTED = "#34527B"


def configure_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    family = ui_font(root)[0]
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                 "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        tkfont.nametofont(name, root=root).configure(family=family, size=12)
    root.option_add("*Menu.font", (family, 12))
    root.option_add("*Menu.background", SURFACE)
    root.option_add("*Menu.foreground", INK)
    root.option_add("*Menu.activeBackground", BLUE_TINT)
    root.option_add("*Menu.activeForeground", PRIMARY)
    style.configure(".", font=ui_font(root, 12), background=BG, foreground=INK)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=INK)
    style.configure("Title.TLabel", font=ui_font(root, 24, "bold"))
    style.configure("Subtitle.TLabel", foreground=MUTED, font=ui_font(root, 11))
    style.configure("Section.TLabel", font=ui_font(root, 14, "bold"))
    style.configure("Kicker.TLabel", foreground=PRIMARY, font=ui_font(root, 10, "bold"))
    for prefix in ("Surface", "Card"):
        style.configure(f"{prefix}.TFrame", background=SURFACE)
        style.configure(f"{prefix}.TLabel", background=SURFACE, foreground=INK)
    style.configure("Side.TFrame", background=NAVY)
    style.configure("Side.TLabel", background=NAVY, foreground=NAV_TEXT)
    style.configure("Border.TFrame", background=BORDER)
    style.configure("Card.TFrame", bordercolor=BORDER, borderwidth=1, relief="solid")
    style.configure("Field.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 11, "bold"))
    style.configure("Hint.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 11))
    style.configure("CalendarMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 11))
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 13, "bold"))
    style.configure("CardMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 11))
    style.configure("CardBody.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 12))
    style.configure("Footer.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 10))
    style.configure("CardStatus.TLabel", background=BLUE_TINT, foreground=PRIMARY, padding=(8, 3), font=ui_font(root, 11, "bold"))
    style.configure("Pill.TLabel", background=BLUE_TINT, foreground=PRIMARY, padding=(9, 4), font=ui_font(root, 10, "bold"))
    for key, fg, bg in (("Todo", "#594713", "#FFF4C9"), ("Progress", PRIMARY, BLUE_TINT),
                        ("Done", GREEN, "#E9F6F0"), ("Canceled", MUTED, "#E9EEF4"),
                        ("Late", RED, "#FCEEF0")):
        style.configure(f"{key}.Pill.TLabel", background=bg, foreground=fg, padding=(8, 3), font=ui_font(root, 11, "bold"))
    style.configure("Late.TLabel", background=SURFACE, foreground=RED, font=ui_font(root, 11, "bold"))
    style.configure("Metric.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 24, "bold"))
    style.configure("MetricMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 11))
    style.configure("Blue.Metric.TLabel", foreground=PRIMARY)
    style.configure("Red.Metric.TLabel", foreground=RED)
    style.configure("Side.TLabel", background=NAVY, foreground=NAV_TEXT, font=ui_font(root, 16, "bold"))
    style.configure("SideMeta.TLabel", background=NAVY, foreground=NAV_MUTED, font=ui_font(root, 10))
    style.configure("SideSection.TLabel", background=NAVY, foreground=NAV_MUTED, font=ui_font(root, 10, "bold"))

    style.configure("TButton", padding=(12, 8), relief="flat", borderwidth=1,
                    background=SURFACE, foreground=INK, bordercolor=BORDER,
                    lightcolor=SURFACE, darkcolor=SURFACE, focuscolor=PRIMARY,
                    font=ui_font(root, 11))
    style.map("TButton", background=[("disabled", "#F0F2F6"), ("pressed", "#E3EAF9"), ("active", "#F0F4FC")],
              foreground=[("disabled", "#9CA7B7")], bordercolor=[("focus", PRIMARY)])
    style.configure("Secondary.TButton", background=SURFACE)
    style.configure("Accent.TButton", background=PRIMARY, foreground=SURFACE, bordercolor=PRIMARY,
                    lightcolor=PRIMARY, darkcolor=PRIMARY, font=ui_font(root, 11, "bold"))
    style.map("Accent.TButton", background=[("disabled", "#A8B8F8"), ("pressed", "#183B69"), ("active", "#193E70")],
              foreground=[("disabled", SURFACE), ("!disabled", SURFACE)], bordercolor=[("!disabled", PRIMARY)])
    style.configure("Quiet.TButton", background=SURFACE, foreground=MUTED, borderwidth=0)
    style.configure("Danger.TButton", background=SURFACE, foreground=RED, bordercolor="#EDCED2")
    style.map("Danger.TButton", background=[("active", "#FCEEF0")], foreground=[("!disabled", RED)])
    style.configure("Compact.TButton", padding=(8, 5), font=ui_font(root, 11))
    style.configure("Nav.TButton", anchor="w", padding=(12, 7), borderwidth=0,
                    background=NAVY, foreground=NAV_TEXT, font=ui_font(root, 11))
    style.map("Nav.TButton", background=[("active", "#294367")], foreground=[("!disabled", NAV_TEXT)])
    style.configure("Selected.Nav.TButton", background=NAV_SELECTED, foreground="white", font=ui_font(root, 11, "bold"))
    style.map("Selected.Nav.TButton", background=[("active", "#3C5D89"), ("!active", NAV_SELECTED)], foreground=[("!disabled", "white")])
    style.configure("Utility.TMenubutton", padding=(12, 7), background=NAVY,
                    foreground=NAV_TEXT, arrowcolor=NAV_TEXT, relief="flat", borderwidth=0, font=ui_font(root, 11))
    style.map("Utility.TMenubutton", background=[("active", "#294367")], foreground=[("!disabled", NAV_TEXT)])
    style.configure("TEntry", padding=(9, 7), fieldbackground=SURFACE, foreground=INK,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, insertcolor=INK)
    style.map("TEntry", bordercolor=[("focus", PRIMARY), ("invalid", RED)])
    style.configure("TCombobox", padding=(8, 6), fieldbackground=SURFACE, background=SURFACE,
                    foreground=INK, arrowcolor=MUTED, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE)], selectbackground=[("readonly", BLUE_TINT)],
              selectforeground=[("readonly", INK)], bordercolor=[("focus", PRIMARY)])
    style.configure("TSpinbox", padding=(8, 6), fieldbackground=SURFACE, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, arrowcolor=MUTED)
    style.configure("TCheckbutton", background=BG, foreground=INK, padding=(0, 3))
    style.configure("Surface.TCheckbutton", background=SURFACE)
    style.map("Surface.TCheckbutton", background=[("active", SURFACE)])
    style.configure("TRadiobutton", background=BG, foreground=INK, padding=(0, 3))
    style.layout("Segment.TRadiobutton", style.layout("Toolbutton"))
    style.configure("Segment.TRadiobutton", background=SURFACE, foreground=MUTED,
                    padding=(16, 7), relief="flat", borderwidth=0, font=ui_font(root, 11))
    style.map("Segment.TRadiobutton", background=[("selected", PRIMARY), ("active", BLUE_TINT)],
              foreground=[("selected", SURFACE), ("active", PRIMARY)])
    style.configure("TLabelframe", background=SURFACE, bordercolor=BORDER, borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=SURFACE, foreground=INK, font=ui_font(root, 12, "bold"))
    style.configure("Treeview", rowheight=round(38 * getattr(root, "_layout_scale", 1.0)), font=ui_font(root, 11), background=SURFACE,
                    fieldbackground=SURFACE, foreground=INK, borderwidth=0, bordercolor=BORDER)
    style.configure("Treeview.Heading", font=ui_font(root, 11, "bold"), padding=(10, 9),
                    background="#F2F5FA", foreground=MUTED, relief="flat", borderwidth=0)
    style.map("Treeview", background=[("selected", BLUE_TINT)], foreground=[("selected", PRIMARY)])
    style.configure("TSeparator", background=BORDER)
    style.configure("Side.TSeparator", background="#425A7D")
    style.configure("Vertical.TScrollbar", background="#CDD5E2", troughcolor=BG,
                    bordercolor=BG, arrowcolor=MUTED, relief="flat", borderwidth=0, width=10)
    style.configure("Day.TButton", background=SURFACE, padding=(7, 5), bordercolor=BORDER)
    style.configure("Today.Day.TButton", background=BLUE_TINT, foreground=PRIMARY, bordercolor="#C8D5FF")
    style.map("Today.Day.TButton", background=[("active", "#DFE8FF")])
    style.configure("Selected.Day.TButton", background=PRIMARY, foreground=SURFACE, bordercolor=PRIMARY)
    style.map("Selected.Day.TButton", background=[("active", "#193E70"), ("!active", PRIMARY)], foreground=[("!disabled", SURFACE)])
    style.configure("Month.TButton", background=SURFACE, foreground=INK, padding=(12, 8), font=ui_font(root, 12))


def line_icon(root, name: str, color: str = MUTED, size: int = 18):
    """Draw crisp line icons without depending on an installed symbol font."""
    from PIL import Image, ImageDraw, ImageTk
    scale = 3
    picture = Image.new("RGBA", (size * scale, size * scale))
    draw = ImageDraw.Draw(picture)
    def line(points):
        draw.line([(int(x * size / 24 * scale), int(y * size / 24 * scale)) for x, y in points], fill=color, width=2 * scale, joint="curve")
    def box(rect, radius=2):
        draw.rounded_rectangle([int(v * size / 24 * scale) for v in rect], radius=radius * scale, outline=color, width=2 * scale)
    if name == "calendar":
        box((3, 5, 21, 22)); line(((3, 10), (21, 10))); line(((8, 2), (8, 7))); line(((16, 2), (16, 7)))
        for x, y in ((8, 14), (15, 14), (8, 18), (15, 18)):
            line(((x, y), (x + 1, y)))
    elif name in ("due", "in_progress"):
        draw.ellipse([3 * scale, 3 * scale, (size - 3) * scale, (size - 3) * scale], outline=color, width=2 * scale)
        line(((12, 6), (12, 12), (16, 14)))
    elif name == "completed":
        box((3, 3, 21, 21)); line(((7, 12), (10, 15), (17, 8)))
    elif name == "canceled":
        box((3, 3, 21, 21)); line(((8, 8), (16, 16))); line(((16, 8), (8, 16)))
    elif name == "bell":
        line(((5, 17), (7, 14), (7, 9), (9, 5), (15, 5), (17, 9), (17, 14), (19, 17), (5, 17)))
        line(((10, 21), (14, 21)))
    else:
        box((3, 3, 21, 21))
        for y in (8, 12, 16):
            line(((7, y), (17, y)))
    picture = picture.resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(picture, master=root)
