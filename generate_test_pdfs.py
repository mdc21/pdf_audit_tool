from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

# Helper to create PDF
def create_pdf(filename, content_func, title="Standard Document", author="Tester"):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setTitle(title)
    c.setAuthor(author)
    content_func(c)
    c.save()
    return filename

# 1. Textual Change
def text_orig(c):
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Quarterly Sales Report")
    c.drawString(100, 730, "The total revenue for Q1 was $50,000. Performance was stable.")

def text_mod(c):
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Quarterly Sales Report")
    c.drawString(100, 730, "The total revenue for Q1 was $55,000. Performance was strong.")

# 2. Formatting Change
def format_orig(c):
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "CONFIDENTIAL DOCUMENT")

def format_mod(c):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 750, "CONFIDENTIAL DOCUMENT")

# 3. Visual Change
def visual_orig(c):
    c.drawString(100, 750, "Logo Position Test")
    c.setStrokeColorRGB(0, 0, 1) 
    c.rect(100, 600, 50, 50, fill=1)

def visual_mod(c):
    c.drawString(100, 750, "Logo Position Test")
    c.setStrokeColorRGB(0, 0, 1) 
    c.rect(200, 600, 50, 50, fill=1) 

# 4. Metadata Change
def meta_content(c):
    c.drawString(100, 750, "This document tests internal metadata.")

# 5. Structural Change
def struct_orig(c):
    c.drawString(100, 750, "Page 1: Introduction")
    c.showPage()
    c.drawString(100, 750, "Page 2: Detailed Data")

def struct_mod(c):
    c.drawString(100, 750, "Page 1: Introduction")

# Execution
files = [
    ("textual_change_orig_01.pdf", text_orig),
    ("textual_change_mod_01.pdf", text_mod),
    ("formatting_change_orig_01.pdf", format_orig),
    ("formatting_change_mod_01.pdf", format_mod),
    ("visual_change_orig_01.pdf", visual_orig),
    ("visual_change_mod_01.pdf", visual_mod),
    ("metadata_change_orig_01.pdf", meta_content, "Original Title", "Author A"),
    ("metadata_change_mod_01.pdf", meta_content, "Modified Title", "Author B"),
    ("structural_change_orig_01.pdf", struct_orig),
    ("structural_change_mod_01.pdf", struct_mod)
]

for f in files:
    if len(f) == 2:
        create_pdf(f[0], f[1])
    else:
        create_pdf(f[0], f[1], f[2], f[3])