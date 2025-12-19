"""
PDF generation utility for recommendation reports
"""
from typing import List
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.models.schemas import RecommendationResponse
from app.core.logging import log


class PDFGenerator:
    """Generate professional PDF reports for recommendations"""
    
    def __init__(self):
        """Initialize PDF generator"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Assessment title
        self.styles.add(ParagraphStyle(
            name='AssessmentTitle',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=6
        ))
    
    def generate_pdf(self, data: RecommendationResponse) -> BytesIO:
        """
        Generate PDF report from recommendation data
        
        Args:
            data: Recommendation response data
            
        Returns:
            BytesIO buffer containing PDF
        """
        log.info(f"Generating PDF for {len(data.recommendations)} recommendations")
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for PDF elements
        elements = []
        
        # Add header
        elements.extend(self._create_header(data))
        
        # Add summary section
        elements.extend(self._create_summary(data))
        
        # Add recommendations
        elements.extend(self._create_recommendations(data))
        
        # Add footer
        elements.extend(self._create_footer())
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        buffer.seek(0)
        log.info("PDF generated successfully")
        
        return buffer
    
    def _create_header(self, data: RecommendationResponse) -> List:
        """Create PDF header"""
        elements = []
        
        # Title
        title = Paragraph(
            "SHL Assessment Recommendations",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Subtitle with query info
        subtitle_text = f"Recommendation Report"
        if data.query_summary:
            subtitle_text += f" - {data.query_summary}"
        
        subtitle = Paragraph(subtitle_text, self.styles['CustomSubtitle'])
        elements.append(subtitle)
        
        # Metadata table
        metadata = [
            ['Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Engine Used:', data.engine_used.upper()],
            ['Total Results:', str(data.total_count)],
        ]
        
        metadata_table = Table(metadata, colWidths=[1.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Divider line
        line_table = Table([['']], colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#3b82f6')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_summary(self, data: RecommendationResponse) -> List:
        """Create summary section"""
        elements = []
        
        # Section header
        header = Paragraph("Summary", self.styles['SectionHeader'])
        elements.append(header)
        
        # Summary text
        summary_text = f"""
        This report contains {data.total_count} personalized assessment recommendations 
        generated using our {data.engine_used.upper()} recommendation engine. Each assessment 
        has been carefully selected based on your requirements and ranked by relevance.
        """
        
        summary = Paragraph(summary_text, self.styles['CustomBody'])
        elements.append(summary)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_recommendations(self, data: RecommendationResponse) -> List:
        """Create recommendations section"""
        elements = []
        
        # Section header
        header = Paragraph("Recommended Assessments", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 0.1*inch))
        
        # Add each recommendation
        for idx, item in enumerate(data.recommendations):
            elements.extend(self._create_recommendation_card(item, idx))
            
            # Add page break after every 2 recommendations (except last)
            if (idx + 1) % 2 == 0 and idx < len(data.recommendations) - 1:
                elements.append(PageBreak())
        
        return elements
    
    def _create_recommendation_card(self, item, index: int) -> List:
        """Create a single recommendation card"""
        elements = []
        assessment = item.assessment
        score = item.score
        
        # Rank and title
        title_text = f"#{item.rank}. {assessment.name}"
        title = Paragraph(title_text, self.styles['AssessmentTitle'])
        elements.append(title)
        
        # Score badge
        match_percent = int(score.total_score * 100)
        score_color = self._get_score_color(score.total_score)
        
        score_data = [[f"Match Score: {match_percent}%"]]
        score_table = Table(score_data, colWidths=[1.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), score_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Details table
        details = []
        
        if assessment.type:
            details.append(['Type:', assessment.type])
        if assessment.job_family:
            details.append(['Job Family:', assessment.job_family])
        if assessment.job_level:
            details.append(['Job Level:', assessment.job_level])
        if assessment.duration:
            details.append(['Duration:', f"{assessment.duration} minutes"])
        if assessment.languages:
            details.append(['Languages:', ', '.join(assessment.languages[:3])])
        
        if details:
            details_table = Table(details, colWidths=[1.2*inch, 4.8*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(details_table)
            elements.append(Spacer(1, 0.1*inch))
        
        # Skills
        if assessment.skills:
            skills_text = f"<b>Skills:</b> {', '.join(assessment.skills[:8])}"
            if len(assessment.skills) > 8:
                skills_text += f" (+{len(assessment.skills) - 8} more)"
            skills = Paragraph(skills_text, self.styles['CustomBody'])
            elements.append(skills)
        
        # Test types
        if assessment.test_types:
            test_types_text = f"<b>Test Types:</b> {', '.join(assessment.test_types)}"
            test_types = Paragraph(test_types_text, self.styles['CustomBody'])
            elements.append(test_types)
        
        # Description
        if assessment.description:
            desc_text = f"<b>Description:</b> {assessment.description[:300]}"
            if len(assessment.description) > 300:
                desc_text += "..."
            description = Paragraph(desc_text, self.styles['CustomBody'])
            elements.append(description)
        
        # Explanation
        if score.explanation:
            expl_text = f"<b>Why Recommended:</b> {score.explanation}"
            explanation = Paragraph(expl_text, self.styles['CustomBody'])
            elements.append(explanation)
        
        # Divider
        elements.append(Spacer(1, 0.2*inch))
        divider = Table([['']], colWidths=[6.5*inch])
        divider.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(divider)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_footer(self) -> List:
        """Create PDF footer"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        
        footer_text = """
        <para align=center>
        <font size=8 color="#94a3b8">
        Generated by SHL Assessment Recommendation Engine<br/>
        © 2025 All rights reserved<br/>
        For more information, visit our platform
        </font>
        </para>
        """
        
        footer = Paragraph(footer_text, self.styles['BodyText'])
        elements.append(footer)
        
        return elements
    
    def _get_score_color(self, score: float):
        """Get color based on score"""
        if score >= 0.8:
            return colors.HexColor('#10b981')  # Green
        elif score >= 0.6:
            return colors.HexColor('#3b82f6')  # Blue
        elif score >= 0.4:
            return colors.HexColor('#f59e0b')  # Orange
        else:
            return colors.HexColor('#ef4444')  # Red
