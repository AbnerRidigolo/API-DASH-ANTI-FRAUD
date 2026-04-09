from fpdf import FPDF

try:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, 'Período atual · Gerado em ')
    out = pdf.output()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
