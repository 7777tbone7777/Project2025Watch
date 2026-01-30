import tempfile
from typing import Dict, List
from fpdf import FPDF


def generate_pdf_report(progress_data: List[Dict], events: List[Dict]) -> str:
    """Generate a PDF report and return the file path."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Project 2025 Weekly Intelligence Report", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, txt="Progress Overview", ln=True)
    pdf.set_font("Arial", size=11)
    for item in progress_data:
        pdf.cell(
            200,
            8,
            txt=f"{item['title']}: {item['progress']}% (Last Updated: {item['last_updated']})",
            ln=True,
        )

    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, txt="Recent Events", ln=True)
    pdf.set_font("Arial", size=11)
    for event in events:
        pdf.cell(200, 8, txt=f"{event['title']} ({event['date']})", ln=True)
        summary_text = str(event["summary"]).encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, txt=summary_text)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name
