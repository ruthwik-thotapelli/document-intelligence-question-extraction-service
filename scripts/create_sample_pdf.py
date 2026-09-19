"""
Generate sample PDF and image files for demonstration.
Run: python scripts/create_sample_pdf.py
"""

import os


def create_sample_pdf():
    """Create a simple sample question paper PDF."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        print("reportlab not installed. Install with: pip install reportlab")
        print("Creating a placeholder PDF instead...")
        with open("samples/question_paper.pdf", "wb") as f:
            # Minimal valid PDF
            f.write(b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF""")
        print("Created samples/question_paper.pdf (placeholder)")
        return

    os.makedirs("samples", exist_ok=True)
    c = canvas.Canvas("samples/question_paper.pdf", pagesize=A4)
    width, height = A4

    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 60, "Sample Examination Paper")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, "Subject: General Knowledge & Science | Time: 1 Hour | Marks: 50")
    c.line(50, height - 90, width - 50, height - 90)

    questions = [
        ("1.", "What is the capital of France?", ["A. Berlin", "B. Madrid", "C. Paris", "D. Rome"]),
        (
            "2.",
            "Which planet is known as the Red Planet?",
            ["A. Earth", "B. Mars", "C. Jupiter", "D. Saturn"],
        ),
        ("3.", "What is the chemical symbol for water?", ["A. CO2", "B. H2O", "C. NaCl", "D. O2"]),
        (
            "4.",
            "Who developed the theory of relativity?",
            ["A. Isaac Newton", "B. Nikola Tesla", "C. Albert Einstein", "D. Stephen Hawking"],
        ),
        (
            "5.",
            "Explain in detail the process of photosynthesis and its significance "
            "to life on Earth. Your answer should cover the light-dependent and "
            "light-independent reactions. (This question continues on the next page.)",
            None,
        ),
    ]

    y = height - 130
    for num, text, options in questions:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, num)
        c.setFont("Helvetica", 11)
        # Wrap long text
        words = text.split()
        line, lines = "", []
        for word in words:
            if len(line + " " + word) < 80:
                line += " " + word if line else word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        for i, l in enumerate(lines):
            c.drawString(70, y - (i * 14), l)
        y -= len(lines) * 14 + 10
        if options:
            c.setFont("Helvetica", 10)
            for opt in options:
                c.drawString(90, y, opt)
                y -= 14
        y -= 20
        if y < 150:
            c.showPage()
            y = height - 60

    # Answer key section
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 60, "ANSWER KEY")
    c.line(50, height - 70, width - 50, height - 70)
    c.setFont("Helvetica", 11)
    answers = ["1. C", "2. B", "3. B", "4. C"]
    y = height - 100
    for ans in answers:
        c.drawString(70, y, ans)
        y -= 20

    c.save()
    print("✓ Created samples/question_paper.pdf")


def create_sample_image():
    """Create a simple PNG question image."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not installed. Creating placeholder PNG instead.")
        import struct
        import zlib

        def create_png(width, height, color=(255, 255, 255)):
            def make_chunk(chunk_type, data):
                c = chunk_type + data
                return (
                    struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
                )

            header = b"\x89PNG\r\n\x1a\n"
            ihdr = make_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            raw = b"".join(b"\x00" + bytes(color) * width for _ in range(height))
            idat = make_chunk(b"IDAT", zlib.compress(raw))
            iend = make_chunk(b"IEND", b"")
            return header + ihdr + idat + iend

        with open("samples/question_image.png", "wb") as f:
            f.write(create_png(400, 200))
        print("✓ Created samples/question_image.png (placeholder)")
        return

    os.makedirs("samples", exist_ok=True)
    img = Image.new("RGB", (800, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text(
        (20, 20), "Q1. What is the boiling point of water at standard pressure?", fill=(0, 0, 0)
    )
    draw.text((40, 60), "A. 90°C", fill=(0, 0, 0))
    draw.text((40, 90), "B. 100°C", fill=(0, 0, 0))
    draw.text((40, 120), "C. 110°C", fill=(0, 0, 0))
    draw.text((40, 150), "D. 120°C", fill=(0, 0, 0))
    draw.text(
        (20, 200),
        "Q2. True or False: The Earth is the largest planet in our solar system.",
        fill=(0, 0, 0),
    )
    draw.text((20, 240), "Answer: False", fill=(50, 150, 50))
    img.save("samples/question_image.png")
    print("✓ Created samples/question_image.png")


if __name__ == "__main__":
    os.makedirs("samples", exist_ok=True)
    create_sample_pdf()
    create_sample_image()
    print("\nSample documents created in samples/")
