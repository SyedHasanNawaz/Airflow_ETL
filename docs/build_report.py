#!/usr/bin/env python3
"""
build_report.py - Deterministic PDF report builder using ReportLab.
Pure black text on white, no color, no logos.
Font: 'Old English Text MT' if installed, else fallback to 'DejaVu Serif' without noting anything.
Page numbers in footer, no header text.
"""

import json
import os
import subprocess
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' in the footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont(getattr(self, "_footer_font", "Serif"), 9)
        self.setFillColor(colors.black)
        
        # Don't print page number on title page (page 1)
        if self._pageNumber > 1:
            footer_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 54, 36, footer_text)
        self.restoreState()


def get_git_commit_hash():
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "N/A"


def setup_fonts():
    # Try finding Old English Text MT
    old_english_paths = [
        "/usr/share/fonts/truetype/msttcorefonts/Old_English_Text_MT.ttf",
        "/usr/share/fonts/truetype/oldenglish.ttf",
        "/usr/share/fonts/Old English Text MT.ttf",
    ]
    old_english_found = None
    for p in old_english_paths:
        if os.path.exists(p):
            old_english_found = p
            break

    if old_english_found:
        pdfmetrics.registerFont(TTFont("Serif", old_english_found))
        pdfmetrics.registerFont(TTFont("Serif-Bold", old_english_found))
        pdfmetrics.registerFont(TTFont("Serif-Italic", old_english_found))
        pdfmetrics.registerFont(TTFont("Serif-BoldItalic", old_english_found))
    else:
        # Fall back to DejaVu Serif
        serif_regular = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
        serif_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
        serif_italic = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
        serif_bold_italic = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"

        if os.path.exists(serif_regular):
            pdfmetrics.registerFont(TTFont("Serif", serif_regular))
            pdfmetrics.registerFont(TTFont("Serif-Bold", serif_bold if os.path.exists(serif_bold) else serif_regular))
            pdfmetrics.registerFont(TTFont("Serif-Italic", serif_italic if os.path.exists(serif_italic) else serif_regular))
            pdfmetrics.registerFont(TTFont("Serif-BoldItalic", serif_bold_italic if os.path.exists(serif_bold_italic) else serif_regular))
        else:
            # Fall back to Times-Roman
            return "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"

    return "Serif", "Serif-Bold", "Serif-Italic", "Serif-BoldItalic"


def build_pdf(manifest_path, output_pdf_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    f_reg, f_bold, f_italic, f_bitalic = setup_fonts()
    NumberedCanvas._footer_font = f_reg

    # Margins: 0.75 in (54 pt)
    margin = 54
    usable_width = letter[0] - (margin * 2)  # 612 - 108 = 504 pt
    usable_height = letter[1] - (margin * 2) # 792 - 108 = 684 pt

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        fontName=f_bold,
        fontSize=24,
        leading=30,
        alignment=1, # Center
        textColor=colors.black,
        spaceAfter=15
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        fontName=f_reg,
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.black,
        spaceAfter=25
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        fontName=f_bold,
        fontSize=11,
        leading=16,
        textColor=colors.black
    )

    meta_val_style = ParagraphStyle(
        "MetaVal",
        fontName=f_reg,
        fontSize=11,
        leading=16,
        textColor=colors.black
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        fontName=f_bold,
        fontSize=15,
        leading=20,
        textColor=colors.black,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        fontName=f_bold,
        fontSize=12,
        leading=16,
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    caption_style = ParagraphStyle(
        "Caption_Custom",
        fontName=f_italic,
        fontSize=9,
        leading=12,
        alignment=1, # Center
        textColor=colors.black,
        spaceBefore=4,
        spaceAfter=12
    )

    story = []

    # -------------------------------------------------------------------------
    # TITLE PAGE
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 40))
    story.append(Paragraph(manifest.get("course", "MLOps / Advanced Operations (Fall 2026)"), subtitle_style))
    story.append(Paragraph(manifest.get("title", "Task 3: Building Airflow ETL Pipeline"), title_style))
    story.append(Spacer(1, 30))

    # Title metadata block
    commit_hash = manifest.get("commit_hash") or get_git_commit_hash()
    metadata_rows = [
        ("Student Name:", manifest.get("student_name", "Syed Hasan Nawaz")),
        ("Roll Number:", manifest.get("roll_number", "23i0703")),
        ("GitHub Repository:", manifest.get("github_url", "https://github.com/SyedHasanNawaz/Airflow_ETL.git")),
        ("Final Commit Hash:", commit_hash),
        ("Execution Environment:", "Ubuntu 24.04 LTS (Astro CLI + Docker + MongoDB)"),
        ("Submission Date:", "November 12, 2026"),
    ]

    for label, val in metadata_rows:
        story.append(Paragraph(f"<b>{label}</b> &nbsp;&nbsp; {val}", meta_val_style))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 40))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # REPORT SECTIONS (Structure only: Heading -> Subheading -> Screenshots + Captions)
    # -------------------------------------------------------------------------
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    screenshots_dir = os.path.join(project_root, "docs", "screenshots")

    for idx, section in enumerate(manifest.get("sections", [])):
        if idx > 0:
            story.append(PageBreak())

        story.append(Paragraph(section["section_title"], h1_style))
        story.append(Spacer(1, 4))

        for sub in section.get("subheadings", []):
            story.append(Paragraph(sub["subheading_title"], h2_style))
            story.append(Spacer(1, 4))

            for shot in sub.get("screenshots", []):
                shot_path = os.path.join(screenshots_dir, shot["file"])
                if os.path.exists(shot_path):
                    with PILImage.open(shot_path) as im:
                        orig_w, orig_h = im.size

                    # Scale to fit usable width and usable height without cropping
                    scale_w = usable_width / float(orig_w)
                    max_allowed_h = 490 # Fits comfortably with headings and caption
                    scale_h = max_allowed_h / float(orig_h)

                    scale = min(scale_w, scale_h)
                    target_w = orig_w * scale
                    target_h = orig_h * scale

                    img = Image(shot_path, width=target_w, height=target_h)
                    img.hAlign = 'CENTER'
                    cap = Paragraph(shot["caption"], caption_style)
                    
                    # Keep image and caption together
                    story.append(KeepTogether([img, cap]))
                else:
                    placeholder = Paragraph(f"<i>[Screenshot {shot['file']} pending]</i>", caption_style)
                    story.append(placeholder)
                
                story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report successfully generated at: {output_pdf_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_f = os.path.join(base_dir, "docs", "report_manifest.json")
    roll_num = "23i0703"
    pdf_out = os.path.join(base_dir, f"{roll_num}_Airflow_ETL.pdf")
    build_pdf(manifest_f, pdf_out)
