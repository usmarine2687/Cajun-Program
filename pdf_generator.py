"""PDF generation for tickets and estimates using ReportLab."""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_ticket_pdf(ticket_details, customer, boat, output_path, engine=None, company_brand=None, logo_path=None):
    """Generate compact invoice PDF.

    Layout: minimal header (<=1/4 page), three-column info (invoice/customer/equipment), parts table (left) and labor table (right) side-by-side, totals block near bottom, optional notes, minimal footer.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=30, bottomMargin=30, leftMargin=36, rightMargin=36)
    story = []
    styles = getSampleStyleSheet()

    brand = company_brand or {
        'name': 'CAJUN MARINE',
        'tagline': 'Your Authorized Tohatsu Dealer',
        'color_primary': '#1a3a52',
        'color_secondary': '#2d6a9f'
    }
    primary = colors.HexColor(brand['color_primary'])
    secondary = colors.HexColor(brand['color_secondary'])

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=primary, spaceAfter=6, alignment=TA_CENTER)
    section_label = ParagraphStyle('SectionLabel', parent=styles['Normal'], fontSize=9, textColor=colors.grey, spaceAfter=2)
    small_text = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9, spaceAfter=2)
    table_header_bg = secondary

    # Header compact
    header_cells = []
    if logo_path and os.path.exists(logo_path):
        from reportlab.platypus import Image
        try:
            img = Image(logo_path, width=0.9*inch, height=0.9*inch)
            header_cells.append(img)
        except Exception:
            header_cells.append(Paragraph(brand['name'], title_style))
    else:
        header_cells.append(Paragraph(brand['name'], title_style))
    header_cells.append(Paragraph(f"Invoice #{ticket_details['ticket_id']}", ParagraphStyle('InvNum', parent=styles['Heading2'], fontSize=14, textColor=secondary, spaceAfter=4, alignment=TA_RIGHT)))
    header_table = Table([header_cells], colWidths=[2*inch, 4.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    story.append(header_table)

    # Info block (invoice + customer + equipment) within ~1/4 page
    date_created = ticket_details.get('date_created', 'N/A')
    date_completed = ticket_details.get('date_completed', 'In Progress')
    status = ticket_details.get('status', 'Open')

    invoice_info = [
        ['Date Opened', date_created],
        ['Date Closed', date_completed],
        ['Status', status]
    ]
    customer_info = [
        ['Customer', customer.get('name','N/A')],
        ['Phone', customer.get('phone','N/A')],
        ['Email', customer.get('email','N/A')]
    ]
    equipment_info = []
    if boat:
        equipment_info.extend([
            ['Boat Year', str(boat.get('year','N/A'))],
            ['Boat Make', boat.get('make','N/A')],
            ['Boat Model', boat.get('model','N/A')]
        ])
    if engine:
        equipment_info.extend([
            ['Engine HP', str(engine.get('hp','N/A'))],
            ['Engine Model', engine.get('model','N/A')],
            ['Engine Serial', engine.get('serial_number','N/A')]
        ])
    if not equipment_info:
        equipment_info.append(['Equipment', '—'])

    def build_info_table(rows):
        t = Table(rows, colWidths=[1.1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        return t

    info_container = Table([
        [build_info_table(invoice_info), build_info_table(customer_info), build_info_table(equipment_info)]
    ], colWidths=[2.6*inch, 2.6*inch, 2.6*inch])
    info_container.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(info_container)
    story.append(Spacer(1, 6))

    # Parts and Labor side-by-side
    parts = ticket_details.get('parts', [])
    labor = ticket_details.get('labor', [])

    parts_data = [['Part #', 'Description', 'Qty', 'Unit', 'Total']]
    for p in parts:
        parts_data.append([
            p.get('part_number') or '',
            p['part_name'],
            str(p['quantity']),
            f"${p['price']:.2f}",
            f"${p['line_total']:.2f}"
        ])
    if len(parts_data) == 1:  # show empty row
        parts_data.append(['', 'No Parts', '', '', ''])

    labor_data = [['Description', 'Hrs', 'Rate', 'Total', 'Tech']]
    for l in labor:
        labor_data.append([
            l['work_description'] or '—',
            str(l['hours_worked']),
            f"${l['labor_rate']:.2f}",
            f"${l['labor_total']:.2f}",
            l.get('mechanic_name','')
        ])
    if len(labor_data) == 1:
        labor_data.append(['No Labor', '', '', '', ''])

    parts_table = Table(parts_data, colWidths=[0.7*inch, 1.5*inch, 0.4*inch, 0.7*inch, 0.8*inch])
    parts_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), table_header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (2,1), (4,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))

    labor_table = Table(labor_data, colWidths=[1.6*inch, 0.4*inch, 0.7*inch, 0.8*inch, 0.6*inch])
    labor_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), table_header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (1,1), (3,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))

    # Add thin spacer between parts and labor
    spacer_width = 0.25*inch
    pl_container = Table([[parts_table, Spacer(spacer_width, 0), labor_table]], colWidths=[4.0*inch, spacer_width, 4.0*inch])
    pl_container.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(pl_container)

    # Column-specific subtotals under each table
    parts_subtotal = sum(p.get('line_total', 0.0) or 0.0 for p in parts)
    labor_subtotal = sum(l.get('labor_total', 0.0) or 0.0 for l in labor)

    parts_sub_table = Table([['Parts Subtotal', f"${parts_subtotal:.2f}"]], colWidths=[1.2*inch, 0.9*inch])
    parts_sub_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    labor_sub_table = Table([['Labor Subtotal', f"${labor_subtotal:.2f}"]], colWidths=[1.2*inch, 0.9*inch])
    labor_sub_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))

    sub_container = Table([[parts_sub_table, Spacer(spacer_width, 0), labor_sub_table]], colWidths=[4.0*inch, spacer_width, 4.0*inch])
    sub_container.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'RIGHT'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(sub_container)

    # Notes (optional, minimal spacing) - prefer customer_notes over description
    notes_text_val = ticket_details.get('customer_notes') or ticket_details.get('description')
    if notes_text_val:
        story.append(Spacer(1, 6))
        story.append(Paragraph('Notes', ParagraphStyle('NotesLabel', parent=styles['Heading4'], fontSize=10, textColor=secondary)))
        story.append(Paragraph(notes_text_val, small_text))

    # Totals at bottom
    subtotal = ticket_details.get('subtotal', 0.0)
    tax = ticket_details.get('tax_amount', 0.0)
    total = ticket_details.get('total', 0.0)
    deposits = ticket_details.get('deposits', [])
    total_paid = sum(d.get('amount',0.0) for d in deposits)
    balance = total - total_paid

    totals_rows = [
        ['Subtotal', f"${subtotal:.2f}"],
        ['Tax (9.75%)', f"${tax:.2f}"],
        ['Total', f"${total:.2f}"],
    ]
    if total_paid > 0:
        totals_rows.append(['Payments', f"${total_paid:.2f}"])
        totals_rows.append(['Balance Due', f"${balance:.2f}"])

    totals_table = Table(totals_rows, colWidths=[1.3*inch, 1.0*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LINEABOVE', (0,0), (-1,0), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    totals_container = Table([[Spacer(1,0), totals_table]], colWidths=[6.9*inch, 1.5*inch])
    totals_container.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM')
    ]))
    story.append(Spacer(1, 12))
    story.append(totals_container)

    # Footer minimal
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Spacer(1, 6))
    story.append(Paragraph(brand['tagline'], footer_style))

    doc.build(story)
    return output_path

def generate_estimate_pdf(estimate_details, customer, output_path, boat=None, engine=None, company_brand=None, logo_path=None):
    """Generate compact estimate PDF matching invoice style.

    Layout: minimal header (<=1/4 page), three-column info (estimate/customer/equipment), line items table, totals block near bottom, optional notes, minimal footer.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=30, bottomMargin=30, leftMargin=36, rightMargin=36)
    story = []
    styles = getSampleStyleSheet()

    brand = company_brand or {
        'name': 'CAJUN MARINE',
        'tagline': 'Your Authorized Tohatsu Dealer',
        'color_primary': '#1a3a52',
        'color_secondary': '#2d6a9f'
    }
    primary = colors.HexColor(brand['color_primary'])
    secondary = colors.HexColor(brand['color_secondary'])

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=primary, spaceAfter=6, alignment=TA_CENTER)
    section_label = ParagraphStyle('SectionLabel', parent=styles['Normal'], fontSize=9, textColor=colors.grey, spaceAfter=2)
    small_text = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9, spaceAfter=2)
    table_header_bg = secondary

    # Header compact
    header_cells = []
    if logo_path and os.path.exists(logo_path):
        from reportlab.platypus import Image
        try:
            img = Image(logo_path, width=0.9*inch, height=0.9*inch)
            header_cells.append(img)
        except Exception:
            header_cells.append(Paragraph(brand['name'], title_style))
    else:
        header_cells.append(Paragraph(brand['name'], title_style))
    header_cells.append(Paragraph(f"Estimate #{estimate_details['estimate_id']}", ParagraphStyle('EstNum', parent=styles['Heading2'], fontSize=14, textColor=secondary, spaceAfter=4, alignment=TA_RIGHT)))
    header_table = Table([header_cells], colWidths=[2*inch, 4.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    story.append(header_table)

    # Info block (estimate date + customer + equipment) within ~1/4 page
    estimate_date = estimate_details.get('estimate_date', datetime.now().strftime('%Y-%m-%d'))

    estimate_info = [
        ['Date', estimate_date],
        ['Valid Until', '30 days'],
        ['Status', 'ESTIMATE']
    ]
    customer_info = [
        ['Customer', customer.get('name','N/A')],
        ['Phone', customer.get('phone','N/A')],
        ['Email', customer.get('email','N/A')]
    ]
    
    # Add address if available
    if customer.get('address'):
        customer_info.append(['Address', customer.get('address')[:30]])
    
    equipment_info = []
    if boat:
        equipment_info.extend([
            ['Boat Year', str(boat.get('year','N/A'))],
            ['Boat Make', boat.get('make','N/A')],
            ['Boat Model', boat.get('model','N/A')]
        ])
    if engine:
        equipment_info.extend([
            ['Engine HP', str(engine.get('hp','N/A'))],
            ['Engine Model', engine.get('model','N/A')],
            ['Engine Serial', engine.get('serial_number','N/A')]
        ])
    if estimate_details.get('insurance_company'):
        equipment_info.append(['Insurance', estimate_details['insurance_company'][:25]])
    if estimate_details.get('claim_number'):
        equipment_info.append(['Claim #', estimate_details['claim_number']])
    
    if not equipment_info:
        equipment_info.append(['Equipment', '—'])

    def build_info_table(rows):
        t = Table(rows, colWidths=[1.1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        return t

    info_container = Table([
        [build_info_table(estimate_info), build_info_table(customer_info), build_info_table(insurance_info)]
    ], colWidths=[2.6*inch, 2.6*inch, 2.6*inch])
    info_container.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(info_container)
    story.append(Spacer(1, 6))

    # Line items table
    line_items = estimate_details.get('line_items', [])
    items_data = [['Description', 'Quantity', 'Unit Price', 'Line Total']]
    
    for item in line_items:
        items_data.append([
            item['description'],
            str(item['quantity']),
            f"${item['unit_price']:.2f}",
            f"${item['line_total']:.2f}"
        ])
    
    if len(items_data) == 1:  # show empty row
        items_data.append(['No line items', '', '', ''])

    items_table = Table(items_data, colWidths=[3.5*inch, 1.0*inch, 1.2*inch, 1.3*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), table_header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (1,1), (3,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6))

    # Notes (optional, minimal spacing)
    notes_text_val = estimate_details.get('notes')
    if notes_text_val:
        story.append(Spacer(1, 6))
        story.append(Paragraph('Notes', ParagraphStyle('NotesLabel', parent=styles['Heading4'], fontSize=10, textColor=secondary)))
        story.append(Paragraph(notes_text_val, small_text))

    # Totals at bottom
    subtotal = estimate_details.get('subtotal', 0.0)
    tax = estimate_details.get('tax_amount', 0.0)
    total = estimate_details.get('total', 0.0)

    totals_rows = [
        ['Subtotal', f"${subtotal:.2f}"],
        ['Tax (9.75%)', f"${tax:.2f}"],
        ['Estimated Total', f"${total:.2f}"],
    ]

    totals_table = Table(totals_rows, colWidths=[1.3*inch, 1.0*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LINEABOVE', (0,0), (-1,0), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    totals_container = Table([[Spacer(1,0), totals_table]], colWidths=[6.7*inch, 1.5*inch])
    totals_container.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM')
    ]))
    story.append(Spacer(1, 12))
    story.append(totals_container)

    # Terms
    story.append(Spacer(1, 12))
    terms_style = ParagraphStyle('Terms', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    story.append(Paragraph("<b>Terms:</b> This estimate is valid for 30 days. Final pricing may vary based on actual parts and labor. A 50% deposit is required to begin work.", terms_style))

    # Footer minimal
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Thank you for considering " + brand['name'] + "!", footer_style))
    story.append(Paragraph(brand['tagline'], footer_style))

    doc.build(story)
    return output_path
