from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

def build_full_pdf(path, variant=1):
    doc = SimpleDocTemplate(path)
    elements = []

    # Page 1 Header
    title = "ACME Insurance Company\nPension Benefit Statement"
    if variant == 2:
        title = "ACME INSURANCE CO.\nDEFERRED PENSION STATEMENT"

    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))

    # Member Details
    member_data = [
        ["Member Name", "Mr A B Sample"],
        ["Policy Number", "AC123456789" if variant == 1 else "AC000999888"],
        ["Date of Birth", "01 January 1970"],
        ["Address", "55 Sample Street, Taunton, Somerset, UK"],
        ["Statement Date", "31 March 2026"]
    ]

    table_style = [
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
    ]

    if variant == 2:
        table_style = [
            ('GRID', (0,0), (-1,-1), 1, colors.blue),
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke)
        ]

    table = Table(member_data)
    table.setStyle(TableStyle(table_style))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Pension Summary
    summary_data = [
        ["Description", "Value"],
        ["Accrued Pension", "£5,382.43" if variant == 1 else "£6,100.00"],
        ["Normal Retirement Date", "29 December 2033"],
        ["Estimated Pension at Retirement", "£14,403.39" if variant == 1 else "£15,750.00"],
        ["Tax-free Lump Sum", "£26,912.17"]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle(table_style))
    elements.append(summary_table)

    elements.append(PageBreak())

    # Page 2 Employment History
    elements.append(Paragraph("Employment and Contributions History", styles['Heading2']))
    elements.append(Spacer(1, 12))

    history_data = [
        ["Employer", "Start Date", "End Date"],
        ["ACME Schools", "01/09/2008", "31/12/2009"],
        ["ACME Schools", "01/09/2007", "31/08/2008"],
        ["ACME Education", "01/04/2002", "31/03/2005"],
        ["ACME Council", "20/01/2002", "31/03/2002"],
        ["Armed Forces Scheme", "29/12/1986", "16/02/1995"]
    ]

    history_table = Table(history_data)
    history_table.setStyle(TableStyle(table_style))
    elements.append(history_table)

    elements.append(Spacer(1, 20))

    # Actuarial Assumptions
    elements.append(Paragraph("Actuarial Assumptions", styles['Heading2']))
    elements.append(Paragraph(
        "Your projected pension has been calculated using assumptions including inflation at 2.5% per annum, "
        "salary growth where applicable, and statutory revaluation in line with current legislation. "
        "These assumptions may change in future and will affect final benefits.", styles['BodyText']
    ))

    elements.append(Spacer(1, 20))

    # Legal / Boilerplate
    elements.append(Paragraph("Important Legal Information", styles['Heading2']))
    elements.append(Paragraph(
        "This statement is provided for illustrative purposes only and does not constitute a guarantee of benefits. "
        "ACME Insurance Company reserves the right to amend scheme rules in accordance with governing legislation. "
        "Benefits are subject to scheme rules, taxation, and regulatory requirements in force at the time of payment. "
        "If there is any inconsistency between this statement and the formal scheme documentation, the latter will prevail.",
        styles['BodyText']
    ))

    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        "You have the right to request a transfer value, subject to applicable terms. "
        "Please contact our pension administration team for further information.",
        styles['BodyText']
    ))

    doc.build(elements)

# Generate files
file1 = "/Users/shilpadhall/agentic_ai_projects/pdf_audit_tool/data/refernce/acme_pixel_perfect_v1.pdf"
file2 = "/Users/shilpadhall/agentic_ai_projects/pdf_audit_tool/data/uch/acme_pixel_test_v1.pdf"

build_full_pdf(file1, variant=1)
build_full_pdf(file2, variant=2)

file1, file2