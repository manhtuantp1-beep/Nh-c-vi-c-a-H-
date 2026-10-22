"""Shared desktop typography, surfaces and accessible interaction states."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, ttk

from .widgets import ui_font

BG = "#F4F6FA"
SURFACE = "#FFFFFF"
INK = "#17243B"
MUTED = "#67758B"
PRIMARY = "#315EFB"
BORDER = "#E3E8F0"
BLUE_TINT = "#EDF2FF"
RED = "#BA3B44"
GREEN = "#148263"


def configure_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    family = ui_font(root)[0]
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                 "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        tkfont.nametofont(name, root=root).configure(family=family, size=11)
    root.option_add("*Menu.font", (family, 11))
    root.option_add("*Menu.background", SURFACE)
    root.option_add("*Menu.foreground", INK)
    root.option_add("*Menu.activeBackground", BLUE_TINT)
    root.option_add("*Menu.activeForeground", PRIMARY)
    style.configure(".", font=ui_font(root, 11), background=BG, foreground=INK)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=INK)
    style.configure("Title.TLabel", font=ui_font(root, 24, "bold"))
    style.configure("Subtitle.TLabel", foreground=MUTED, font=ui_font(root, 10))
    style.configure("Section.TLabel", font=ui_font(root, 13, "bold"))
    style.configure("Kicker.TLabel", foreground=PRIMARY, font=ui_font(root, 9, "bold"))
    for prefix in ("Surface", "Side", "Card"):
        style.configure(f"{prefix}.TFrame", background=SURFACE)
        style.configure(f"{prefix}.TLabel", background=SURFACE, foreground=INK)
    style.configure("Border.TFrame", background=BORDER)
    style.configure("Card.TFrame", bordercolor=BORDER, borderwidth=1, relief="solid")
    style.configure("Field.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 10, "bold"))
    style.configure("Hint.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 10))
    style.configure("CalendarMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 10))
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 12, "bold"))
    style.configure("CardMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 10))
    style.configure("CardStatus.TLabel", background=BLUE_TINT, foreground=PRIMARY, padding=(8, 3), font=ui_font(root, 9, "bold"))
    style.configure("Pill.TLabel", background=BLUE_TINT, foreground=PRIMARY, padding=(9, 4), font=ui_font(root, 9, "bold"))
    for key, fg, bg in (("Todo", "#5B6780", "#F0F3F8"), ("Progress", PRIMARY, BLUE_TINT),
                        ("Done", GREEN, "#E9F6F0"), ("Canceled", MUTED, "#F0F2F6"),
                        ("Late", RED, "#FCEEF0")):
        style.configure(f"{key}.Pill.TLabel", background=bg, foreground=fg, padding=(8, 3), font=ui_font(root, 9, "bold"))
    style.configure("Late.TLabel", background=SURFACE, foreground=RED, font=ui_font(root, 10, "bold"))
    style.configure("Metric.TLabel", background=SURFACE, foreground=INK, font=ui_font(root, 22, "bold"))
    style.configure("MetricMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 10))
    style.configure("Blue.Metric.TLabel", foreground=PRIMARY)
    style.configure("Red.Metric.TLabel", foreground=RED)
    style.configure("Side.TLabel", foreground=INK, font=ui_font(root, 15, "bold"))
    style.configure("SideMeta.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 9))
    style.configure("SideSection.TLabel", background=SURFACE, foreground=MUTED, font=ui_font(root, 9, "bold"))

    style.configure("TButton", padding=(12, 8), relief="flat", borderwidth=1,
                    background=SURFACE, foreground=INK, bordercolor=BORDER,
                    lightcolor=SURFACE, darkcolor=SURFACE, focuscolor=PRIMARY,
                    font=ui_font(root, 10))
    style.map("TButton", background=[("disabled", "#F0F2F6"), ("pressed", "#E3EAF9"), ("active", "#F0F4FC")],
              foreground=[("disabled", "#9CA7B7")], bordercolor=[("focus", PRIMARY)])
    style.configure("Secondary.TButton", background=SURFACE)
    style.configure("Accent.TButton", background=PRIMARY, foreground=SURFACE, bordercolor=PRIMARY,
                    lightcolor=PRIMARY, darkcolor=PRIMARY, font=ui_font(root, 10, "bold"))
    style.map("Accent.TButton", background=[("disabled", "#A8B8F8"), ("pressed", "#2248D5"), ("active", "#264FE3")],
              foreground=[("disabled", SURFACE), ("!disabled", SURFACE)], bordercolor=[("!disabled", PRIMARY)])
    style.configure("Quiet.TButton", background=SURFACE, foreground=MUTED, borderwidth=0)
    style.configure("Danger.TButton", background=SURFACE, foreground=RED, bordercolor="#EDCED2")
    style.map("Danger.TButton", background=[("active", "#FCEEF0")], foreground=[("!disabled", RED)])
    style.configure("Compact.TButton", padding=(8, 5), font=ui_font(root, 10))
    style.configure("Nav.TButton", anchor="w", padding=(12, 9), borderwidth=0,
                    background=SURFACE, foreground=MUTED, font=ui_font(root, 10))
    style.map("Nav.TButton", background=[("active", "#F4F6FB")])
    style.configure("Selected.Nav.TButton", background=BLUE_TINT, foreground=PRIMARY, font=ui_font(root, 10, "bold"))
    style.map("Selected.Nav.TButton", background=[("active", "#E4ECFF"), ("!active", BLUE_TINT)], foreground=[("!disabled", PRIMARY)])
    style.configure("Utility.TMenubutton", padding=(12, 8), background=SURFACE,
                    foreground=MUTED, relief="flat", borderwidth=0, font=ui_font(root, 10))
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
                    padding=(16, 7), relief="flat", borderwidth=0, font=ui_font(root, 10))
    style.map("Segment.TRadiobutton", background=[("selected", PRIMARY), ("active", BLUE_TINT)],
              foreground=[("selected", SURFACE), ("active", PRIMARY)])
    style.configure("TLabelframe", background=SURFACE, bordercolor=BORDER, borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=SURFACE, foreground=INK, font=ui_font(root, 11, "bold"))
    style.configure("Treeview", rowheight=36, font=ui_font(root, 10), background=SURFACE,
                    fieldbackground=SURFACE, foreground=INK, borderwidth=0, bordercolor=BORDER)
    style.configure("Treeview.Heading", font=ui_font(root, 10, "bold"), padding=(10, 9),
                    background="#F2F5FA", foreground=MUTED, relief="flat", borderwidth=0)
    style.map("Treeview", background=[("selected", BLUE_TINT)], foreground=[("selected", PRIMARY)])
    style.configure("TSeparator", background=BORDER)
    style.configure("Vertical.TScrollbar", background="#CDD5E2", troughcolor=BG,
                    bordercolor=BG, arrowcolor=MUTED, relief="flat", borderwidth=0, width=10)
    style.configure("Day.TButton", background=SURFACE, padding=(7, 5), bordercolor=BORDER)
    style.configure("Today.Day.TButton", background=BLUE_TINT, foreground=PRIMARY, bordercolor="#C8D5FF")
    style.map("Today.Day.TButton", background=[("active", "#DFE8FF")])
    style.configure("Selected.Day.TButton", background=PRIMARY, foreground=SURFACE, bordercolor=PRIMARY)
    style.map("Selected.Day.TButton", background=[("active", "#264FE3"), ("!active", PRIMARY)], foreground=[("!disabled", SURFACE)])
    style.configure("Month.TButton", background=SURFACE, foreground=INK, padding=(12, 8), font=ui_font(root, 11))


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
