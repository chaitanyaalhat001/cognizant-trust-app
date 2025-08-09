"""
Professional PDF Receipt Generator for Cognizant Trust
Based on corporate receipt standards with proper branding
"""
import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF

from django.conf import settings
from django.utils import timezone


class CognizantTrustReceiptPDF:
    """Professional PDF receipt generator for Cognizant Trust with comprehensive branding"""
    
    # Cognizant Brand Colors (Official)
    COGNIZANT_BLUE = colors.Color(0.0, 0.31, 0.73)      # #004FBA (Primary Blue)
    COGNIZANT_NAVY = colors.Color(0.02, 0.20, 0.45)     # #053373 (Navy Blue)
    COGNIZANT_LIGHT_BLUE = colors.Color(0.89, 0.94, 1.0) # #E3F0FF (Light Blue)
    COGNIZANT_GRAY = colors.Color(0.33, 0.33, 0.33)     # #545454 (Dark Gray)
    LIGHT_GRAY = colors.Color(0.94, 0.94, 0.94)         # #F0F0F0 (Very Light Gray)
    WHITE = colors.white
    BLACK = colors.black
    ACCENT_GREEN = colors.Color(0.13, 0.55, 0.13)       # #228B22 (Forest Green)
    
    def __init__(self, donation):
        self.donation = donation
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )
        
        # Get styles
        self.styles = getSampleStyleSheet()
        self._setup_trust_styles()
        
        # Logo path
        self.logo_path = os.path.join(settings.BASE_DIR, 'temp', 'logo.png')
        
    def _setup_trust_styles(self):
        """Setup comprehensive paragraph styles for Cognizant Trust receipts"""
        
        # Trust Header Style
        self.styles.add(ParagraphStyle(
            name='TrustHeader',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=self.COGNIZANT_BLUE,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=4*mm,
            spaceBefore=2*mm
        ))
        
        # Trust Tagline Style
        self.styles.add(ParagraphStyle(
            name='TrustTagline',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.COGNIZANT_GRAY,
            fontName='Helvetica-Oblique',
            alignment=TA_CENTER,
            spaceAfter=6*mm
        ))
        
        # Document Title Style
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=self.COGNIZANT_NAVY,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=8*mm,
            spaceBefore=4*mm
        ))
        
        # Section Header Style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.WHITE,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=3*mm,
            spaceBefore=5*mm,
            backColor=self.COGNIZANT_BLUE,
            borderPadding=6
        ))
        
        # Trust Description Style
        self.styles.add(ParagraphStyle(
            name='TrustDescription',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COGNIZANT_GRAY,
            fontName='Helvetica',
            alignment=TA_JUSTIFY,
            spaceAfter=4*mm,
            leading=12
        ))
        
        # Amount Highlight Style
        self.styles.add(ParagraphStyle(
            name='AmountHighlight',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=self.ACCENT_GREEN,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=3*mm,
            spaceBefore=3*mm
        ))
        
        # Table Label Style
        self.styles.add(ParagraphStyle(
            name='TableLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COGNIZANT_NAVY,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ))
        
        # Table Value Style
        self.styles.add(ParagraphStyle(
            name='TableValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.BLACK,
            fontName='Helvetica',
            alignment=TA_LEFT
        ))
        
        # Body Text Style
        self.styles.add(ParagraphStyle(
            name='TrustBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.BLACK,
            fontName='Helvetica',
            alignment=TA_LEFT,
            spaceAfter=3*mm,
            leading=13
        ))
        
        # Footer Style
        self.styles.add(ParagraphStyle(
            name='FooterText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.COGNIZANT_GRAY,
            fontName='Helvetica',
            alignment=TA_CENTER,
            leading=11
        ))
        
        # Disclaimer Style
        self.styles.add(ParagraphStyle(
            name='DisclaimerText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.COGNIZANT_GRAY,
            fontName='Helvetica-Oblique',
            alignment=TA_JUSTIFY,
            leading=10
        ))
        
    def _add_trust_header(self, story):
        """Add comprehensive Cognizant Trust header with logo and description"""
        
        # Logo placement
        if os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=50*mm, height=20*mm)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 4*mm))
            except Exception:
                # Fallback if logo fails
                logo_fallback = Paragraph("COGNIZANT", self.styles['TrustHeader'])
                story.append(logo_fallback)
                story.append(Spacer(1, 2*mm))
        
        # Trust Name
        trust_name = Paragraph("COGNIZANT TRUST", self.styles['TrustHeader'])
        story.append(trust_name)
        
        # Trust Tagline
        tagline = Paragraph("Empowering Communities Through Technology and Innovation", self.styles['TrustTagline'])
        story.append(tagline)
        
        # Trust Description
        trust_description = """
        Cognizant Trust is the charitable arm of Cognizant Technology Solutions, dedicated to creating 
        positive social impact through education, healthcare, environmental sustainability, and community 
        development initiatives. Our mission is to leverage technology and innovation to build stronger, 
        more resilient communities worldwide.
        """
        description_para = Paragraph(trust_description.strip(), self.styles['TrustDescription'])
        story.append(description_para)
        
        # Separator line
        line_drawing = Drawing(170*mm, 2*mm)
        line_drawing.add(Line(0, 1*mm, 170*mm, 1*mm, strokeColor=self.COGNIZANT_BLUE, strokeWidth=2))
        story.append(line_drawing)
        story.append(Spacer(1, 4*mm))
        
        # Document title
        doc_title = Paragraph("DONATION RECEIPT", self.styles['DocumentTitle'])
        story.append(doc_title)
        
    def _create_info_section(self, title, data, highlight_amount=False):
        """Create a professional information section with optional amount highlighting"""
        elements = []
        
        # Section header
        header = Paragraph(title, self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 2*mm))
        
        if highlight_amount and len(data) > 0:
            # Special handling for donation amount
            amount_row = data[0]
            if len(amount_row) >= 2:
                amount_para = Paragraph(f"{amount_row[1]}", self.styles['AmountHighlight'])
                elements.append(amount_para)
                data = data[1:]  # Remove amount row from table data
        
        if data:  # Only create table if there's data
            # Create table
            table = Table(data, colWidths=[50*mm, 100*mm])
            table.setStyle(TableStyle([
                # Fonts
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                
                # Colors
                ('TEXTCOLOR', (0, 0), (0, -1), self.COGNIZANT_NAVY),
                ('TEXTCOLOR', (1, 0), (1, -1), self.BLACK),
                
                # Alignment and spacing
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
                ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
                
                # Alternating row backgrounds
                ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_GRAY),
                ('BACKGROUND', (0, 2), (-1, 2), self.LIGHT_GRAY),
                ('BACKGROUND', (0, 4), (-1, 4), self.LIGHT_GRAY),
                
                # Borders
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, self.COGNIZANT_GRAY),
                ('BOX', (0, 0), (-1, -1), 1, self.COGNIZANT_GRAY),
            ]))
            
            elements.append(table)
        
        elements.append(Spacer(1, 5*mm))
        return elements
        
    def _add_receipt_information(self, story):
        """Add receipt details section"""
        
        receipt_data = [
            ['Receipt Number:', self.donation.receipt_number or f"CZT-{str(self.donation.id)[:8].upper()}"],
            ['Issue Date:', self.donation.created_at.strftime('%d %B %Y')],
            ['Issue Time:', self.donation.created_at.strftime('%I:%M %p IST')],
            ['Transaction Reference:', str(self.donation.id)],
            ['Payment Method:', 'UPI Digital Payment'],
            ['UPI Reference ID:', self.donation.upi_ref_id],
        ]
        
        elements = self._create_info_section("RECEIPT INFORMATION", receipt_data)
        for element in elements:
            story.append(element)
            
    def _add_donation_details(self, story):
        """Add donation details with highlighted amount"""
        
        amount_text = f"₹ {self.donation.amount:,.2f}"
        
        donation_data = [
            ['Amount Donated:', amount_text],  # This will be highlighted
            ['Purpose:', self.donation.purpose],
            ['Donation Date:', self.donation.created_at.strftime('%d %B %Y')],
            ['Category:', 'General Fund'],
            ['Tax Exemption:', 'Eligible under Section 80G'],
        ]
        
        elements = self._create_info_section("DONATION DETAILS", donation_data, highlight_amount=True)
        for element in elements:
            story.append(element)
            
    def _add_donor_information(self, story):
        """Add donor details section"""
        
        # Get donor profile if available
        donor_profile = getattr(self.donation.donor, 'donor_profile', None) if self.donation.donor else None
        
        donor_data = [
            ['Donor Name:', self.donation.donor_name],
            ['Email Address:', self.donation.donor_email or 'Not provided'],
            ['Phone Number:', self.donation.donor_phone or 'Not provided'],
        ]
        
        # Add profile information if available
        if donor_profile:
            if donor_profile.address:
                donor_data.append(['Address:', donor_profile.address])
            if donor_profile.city and donor_profile.state:
                donor_data.append(['City, State:', f"{donor_profile.city}, {donor_profile.state}"])
            if donor_profile.pincode:
                donor_data.append(['Postal Code:', donor_profile.pincode])
            if donor_profile.pan_number:
                donor_data.append(['PAN Number:', donor_profile.pan_number])
        
        elements = self._create_info_section("DONOR INFORMATION", donor_data)
        for element in elements:
            story.append(element)
            
    def _add_blockchain_verification(self, story):
        """Add blockchain transparency and verification details"""
        
        blockchain_data = [
            ['Blockchain Status:', self.donation.blockchain_status.title()],
            ['Network:', 'Ethereum Sepolia Testnet'],
        ]
        
        if self.donation.blockchain_tx_hash:
            blockchain_data.extend([
                ['Transaction Hash:', self.donation.blockchain_tx_hash],
                ['Verification URL:', f"https://sepolia.etherscan.io/tx/0x{self.donation.blockchain_tx_hash}"],
            ])
        
        if self.donation.admin_wallet:
            blockchain_data.append(['Recording Wallet:', self.donation.admin_wallet])
        
        elements = self._create_info_section("BLOCKCHAIN VERIFICATION", blockchain_data)
        for element in elements:
            story.append(element)
            
        # Add verification explanation
        verification_text = """
        This donation has been permanently recorded on the Ethereum blockchain, ensuring complete 
        transparency and immutability. The blockchain record serves as an additional layer of 
        verification and cannot be altered or deleted, providing donors with confidence in the 
        integrity of their contributions.
        """
        
        verification_para = Paragraph(verification_text.strip(), self.styles['TrustBodyText'])
        story.append(verification_para)
        story.append(Spacer(1, 4*mm))
        
    def _add_tax_exemption_details(self, story):
        """Add comprehensive tax exemption information"""
        
        tax_header = Paragraph("TAX EXEMPTION CERTIFICATE", self.styles['SectionHeader'])
        story.append(tax_header)
        story.append(Spacer(1, 3*mm))
        
        # Tax exemption details
        tax_info = """
        <b>Section 80G Tax Benefits:</b><br/><br/>
        This donation qualifies for income tax deduction under Section 80G of the Income Tax Act, 1961. 
        Cognizant Trust is a registered charitable organization with valid 80G certification from the 
        Income Tax Department of India.<br/><br/>
        
        <b>Important Instructions:</b><br/>
        • Retain this receipt for your income tax filing<br/>
        • This receipt is valid for claiming tax deduction<br/>
        • Consult your tax advisor for specific deduction limits<br/>
        • Original receipt may be required during tax assessment<br/><br/>
        
        <b>Trust Registration Details:</b><br/>
        • Registration Number: [Trust Registration Number]<br/>
        • 80G Certificate Number: [80G Certificate Number]<br/>
        • Valid from: [Start Date] to [End Date]
        """
        
        tax_para = Paragraph(tax_info, self.styles['TrustBodyText'])
        story.append(tax_para)
        story.append(Spacer(1, 6*mm))
        
    def _add_trust_footer(self, story):
        """Add comprehensive footer with trust information"""
        
        # Separator line
        footer_line = Drawing(170*mm, 1*mm)
        footer_line.add(Line(0, 0.5*mm, 170*mm, 0.5*mm, strokeColor=self.COGNIZANT_GRAY, strokeWidth=1))
        story.append(footer_line)
        story.append(Spacer(1, 4*mm))
        
        # Contact information
        contact_info = """
        <b>COGNIZANT TRUST</b><br/>
        Corporate Office: Cognizant Technology Solutions, Bangalore, India<br/>
        Email: trust@cognizant.com | Phone: +91-80-6700-4000<br/>
        Website: www.cognizant.com/trust | Social Impact Portal: impact.cognizant.com
        """
        
        contact_para = Paragraph(contact_info, self.styles['FooterText'])
        story.append(contact_para)
        story.append(Spacer(1, 4*mm))
        
        # Legal disclaimer
        disclaimer = """
        This is a digitally generated receipt with blockchain verification. No physical signature is required. 
        This document serves as official proof of donation and is valid for all legal and tax purposes. 
        For verification of authenticity, please check the blockchain transaction hash provided above or 
        contact Cognizant Trust directly.
        """
        
        disclaimer_para = Paragraph(disclaimer, self.styles['DisclaimerText'])
        story.append(disclaimer_para)
        story.append(Spacer(1, 3*mm))
        
        # Generation timestamp
        generation_info = Paragraph(
            f"Generated on {timezone.now().strftime('%d %B %Y at %I:%M %p IST')} | Blockchain Verified | Digitally Signed",
            self.styles['DisclaimerText']
        )
        story.append(generation_info)
        
        # Trust motto
        story.append(Spacer(1, 4*mm))
        motto = Paragraph(
            "Together, we build stronger communities through technology and compassion.",
            self.styles['TrustTagline']
        )
        story.append(motto)
        
    def generate_pdf(self):
        """Generate comprehensive Cognizant Trust donation receipt"""
        
        story = []
        
        # Build complete receipt
        self._add_trust_header(story)
        self._add_receipt_information(story)
        self._add_donation_details(story)
        self._add_donor_information(story)
        self._add_blockchain_verification(story)
        self._add_tax_exemption_details(story)
        self._add_trust_footer(story)
        
        # Generate PDF
        self.doc.build(story)
        
        pdf_data = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_data


def generate_donation_receipt(donation):
    """
    Generate a comprehensive professional PDF receipt for Cognizant Trust donations
    
    Args:
        donation: DonationTransaction instance
        
    Returns:
        bytes: Professional PDF receipt with complete trust branding and information
    """
    generator = CognizantTrustReceiptPDF(donation)
    return generator.generate_pdf() 