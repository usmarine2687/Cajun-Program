"""PDF generation for tickets and estimates using ReportLab."""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_ticket_pdf(ticket_details, customer, boat, output_path):
    """Generate professional invoice PDF for a ticket."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a3a52'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d6a9f'),
        spaceAfter=12
    )
    
    # Title
    story.append(Paragraph("CAJUN MARINE", title_style))
    story.append(Paragraph(f"Invoice #{ticket_details['ticket_id']}", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    # Date and status
    date_created = ticket_details.get('date_created', 'N/A')
    date_completed = ticket_details.get('date_completed', 'In Progress')
    status = ticket_details.get('status', 'Open')
    
    info_data = [
        ['Date Created:', date_created, 'Status:', status],
        ['Date Completed:', date_completed, '', '']
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Customer information
    story.append(Paragraph("Customer Information", heading_style))
    customer_data = [
        ['Name:', customer.get('name', 'N/A')],
        ['Phone:', customer.get('phone', 'N/A')],
        ['Email:', customer.get('email', 'N/A')],
    ]
    customer_table = Table(customer_data, colWidths=[1.5*inch, 4.5*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Boat information
    if boat:
        story.append(Paragraph("Boat Information", heading_style))
        boat_data = [
            ['Year:', str(boat.get('year', 'N/A'))],
            ['Make:', boat.get('make', 'N/A')],
            ['Model:', boat.get('model', 'N/A')],
        ]
        boat_table = Table(boat_data, colWidths=[1.5*inch, 4.5*inch])
        boat_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(boat_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Parts
    parts = ticket_details.get('parts', [])
    if parts:
        story.append(Paragraph("Parts", heading_style))
        parts_data = [['Part Name', 'Qty', 'Unit Price', 'Total']]
        for part in parts:
            parts_data.append([
                part['part_name'],
                str(part['quantity']),
                f"${part['price']:.2f}",
                f"${part['line_total']:.2f}"
            ])
        
        parts_table = Table(parts_data, colWidths=[3*inch, 0.75*inch, 1.25*inch, 1*inch])
        parts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a9f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(parts_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Labor
    labor = ticket_details.get('labor', [])
    if labor:
        story.append(Paragraph("Labor", heading_style))
        labor_data = [['Description', 'Hours', 'Rate', 'Total']]
        for l in labor:
            labor_data.append([
                l['work_description'],
                str(l['hours_worked']),
                f"${l['labor_rate']:.2f}",
                f"${l['labor_total']:.2f}"
            ])
        
        labor_table = Table(labor_data, colWidths=[3*inch, 0.75*inch, 1.25*inch, 1*inch])
        labor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a9f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(labor_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Totals
    subtotal = ticket_details.get('subtotal', 0)
    tax = ticket_details.get('tax_amount', 0)
    total = ticket_details.get('total', 0)
    
    totals_data = [
        ['Subtotal:', f"${subtotal:.2f}"],
        ['Tax (9.75%):', f"${tax:.2f}"],
        ['Total:', f"${total:.2f}"],
    ]
    
    # Add deposits/payments if any
    deposits = ticket_details.get('deposits', [])
    total_paid = sum(d['amount'] for d in deposits)
    if total_paid > 0:
        totals_data.append(['Payments:', f"${total_paid:.2f}"])
        balance = total - total_paid
        totals_data.append(['Balance Due:', f"${balance:.2f}"])
    
    totals_table = Table(totals_data, colWidths=[4.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Payment history
    if deposits:
        story.append(Paragraph("Payment History", heading_style))
        payment_data = [['Date', 'Method', 'Amount']]
        for d in deposits:
            payment_data.append([
                d['date_paid'],
                d['payment_method'],
                f"${d['amount']:.2f}"
            ])
        
        payment_table = Table(payment_data, colWidths=[2*inch, 2*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a9f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(payment_table)
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Thank you for your business!", footer_style))
    story.append(Paragraph("Cajun Marine - Your Tohatsu Dealer", footer_style))
    
    # Build PDF
    doc.build(story)
    return output_path


def generate_estimate_pdf(estimate_details, customer, output_path):
    """Generate professional estimate/quote PDF."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a3a52'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d6a9f'),
        spaceAfter=12
    )
    
    # Title
    story.append(Paragraph("CAJUN MARINE", title_style))
    story.append(Paragraph(f"Estimate #{estimate_details['estimate_id']}", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    # Date and validity
    estimate_date = estimate_details.get('estimate_date', datetime.now().strftime('%Y-%m-%d'))
    
    info_data = [
        ['Date:', estimate_date],
        ['Valid Until:', '30 days from date'],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Customer information
    story.append(Paragraph("Customer Information", heading_style))
    customer_data = [
        ['Name:', customer.get('name', 'N/A')],
        ['Phone:', customer.get('phone', 'N/A')],
        ['Email:', customer.get('email', 'N/A')],
    ]
    
    # Add insurance info if present
    if estimate_details.get('insurance_info'):
        customer_data.append(['Insurance:', estimate_details['insurance_info']])
    
    customer_table = Table(customer_data, colWidths=[1.5*inch, 4.5*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Line items
    line_items = estimate_details.get('line_items', [])
    if line_items:
        story.append(Paragraph("Estimate Details", heading_style))
        items_data = [['Description', 'Qty', 'Unit Price', 'Total']]
        for item in line_items:
            items_data.append([
                item['description'],
                str(item['quantity']),
                f"${item['unit_price']:.2f}",
                f"${item['line_total']:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 0.75*inch, 1.25*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a9f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Totals
    subtotal = estimate_details.get('subtotal', 0)
    tax = estimate_details.get('tax_amount', 0)
    total = estimate_details.get('total', 0)
    
    totals_data = [
        ['Subtotal:', f"${subtotal:.2f}"],
        ['Tax (9.75%):', f"${tax:.2f}"],
        ['Estimated Total:', f"${total:.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[4.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Notes
    if estimate_details.get('notes'):
        story.append(Paragraph("Notes", heading_style))
        story.append(Paragraph(estimate_details['notes'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # Terms
    story.append(Spacer(1, 0.5*inch))
    terms_style = ParagraphStyle(
        'Terms',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey
    )
    story.append(Paragraph("<b>Terms & Conditions:</b>", terms_style))
    story.append(Paragraph("This estimate is valid for 30 days from the date above. Final pricing may vary based on actual parts and labor required. A 50% deposit is required to begin work.", terms_style))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Thank you for considering Cajun Marine!", footer_style))
    story.append(Paragraph("Your Authorized Tohatsu Dealer", footer_style))
    
    # Build PDF
    doc.build(story)
    return output_path
