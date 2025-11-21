"""
PDF Executive Report Generator
Generates professional PDF reports from organizational genome insights
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, List


class PDFExecutiveReport:
    """
    Generate professional PDF executive reports

    Features:
    - Executive summary with key metrics
    - Mutation risk analysis table
    - ROI analysis and recommendations
    - Talent redundancy alerts
    - Workforce readiness dashboard
    - Critical actions list
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        """Add custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=20
        ))

        # Metric label
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666')
        ))

        # Metric value
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            fontName='Helvetica-Bold'
        ))

    def generate_report(self, insights: Dict[str, Any]) -> BytesIO:
        """
        Generate PDF report from insights data

        Args:
            insights: Comprehensive insights data from AdvancedInsights.generate_comprehensive_insights()

        Returns:
            BytesIO buffer containing PDF data
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Build story (content elements)
        story = []

        # Header
        story.extend(self._create_header())

        # Executive Summary
        story.extend(self._create_executive_summary(insights.get('executive_summary', {})))

        # Workforce Readiness
        story.extend(self._create_workforce_readiness(insights.get('workforce_readiness', {})))

        # Mutation Risk Analysis
        story.extend(self._create_mutation_risk_section(insights.get('mutation_risk_analysis', [])))

        # Talent Redundancy Alerts
        story.extend(self._create_redundancy_alerts(insights.get('talent_redundancy_alerts', [])))

        # ROI Analysis
        story.extend(self._create_roi_section(insights.get('roi_analysis', [])))

        # Mentorship Recommendations
        story.extend(self._create_mentorship_section(insights.get('mentorship_recommendations', [])))

        # Critical Actions
        story.extend(self._create_critical_actions(insights.get('critical_actions', [])))

        # Footer
        story.extend(self._create_footer())

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_header(self) -> List:
        """Create report header"""
        elements = []

        # Title
        title = Paragraph("🧬 Skill DNA Executive Report", self.styles['CustomTitle'])
        elements.append(title)

        # Subtitle with date
        subtitle = Paragraph(
            f"<i>Organizational Genome Intelligence Analysis</i><br/>{datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb')))
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_executive_summary(self, summary: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []

        # Section header
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        # Key metrics table
        metrics_data = [
            ['Total Skills', str(summary.get('total_skills', 'N/A'))],
            ['Total Employees', str(summary.get('total_employees', 'N/A'))],
            ['High-Risk Skills', str(summary.get('high_risk_skills', 'N/A'))],
            ['Emerging Skills', str(summary.get('emerging_skills', 'N/A'))],
            ['Workforce Readiness Score', f"{summary.get('workforce_readiness_score', 0):.1f}/100"],
            ['Avg Mutation Risk', f"{summary.get('avg_mutation_risk', 0):.2f}"],
            ['Critical Redundancy Risks', str(summary.get('critical_redundancy_risks', 0))],
            ['Mentorship Programs', str(summary.get('mentorship_programs_recommended', 0))]
        ]

        metrics_table = Table(metrics_data, colWidths=[3.5 * inch, 2 * inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a1a1a')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb'))
        ]))

        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_workforce_readiness(self, readiness: Dict[str, Any]) -> List:
        """Create workforce readiness section"""
        elements = []

        # Section header
        elements.append(Paragraph("Workforce Readiness Assessment", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        # Overall score with grade
        score = readiness.get('overall_score', 0)
        grade = readiness.get('grade', 'N/A')

        score_text = f"""
        <b>Overall Readiness Score: {score:.1f}/100</b> (Grade: {grade})<br/>
        <i>Composite metric measuring organizational preparedness for future skill demands</i>
        """
        elements.append(Paragraph(score_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.15 * inch))

        # Component breakdown
        components_data = [
            ['Component', 'Score'],
            ['Future Skills Coverage', f"{readiness.get('future_skills_coverage', 0):.1f}%"],
            ['Critical Skills Availability', f"{readiness.get('critical_skills_availability', 0):.1f}%"],
            ['Adaptation Velocity', f"{readiness.get('adaptation_velocity', 0):.2f} skills/month"]
        ]

        components_table = Table(components_data, colWidths=[3.5 * inch, 2 * inch])
        components_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb'))
        ]))

        elements.append(components_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_mutation_risk_section(self, risk_analysis: List[Dict[str, Any]]) -> List:
        """Create mutation risk analysis section"""
        elements = []

        # Section header
        elements.append(Paragraph("High-Risk Skills Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        if not risk_analysis:
            elements.append(Paragraph("<i>No high-risk skills identified.</i>", self.styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
            return elements

        # Show top 10 high-risk skills
        top_risks = sorted(risk_analysis, key=lambda x: x.get('mutation_risk', 0), reverse=True)[:10]

        risk_data = [['Skill', 'Risk', 'Employees', 'Recommended Transition', 'Urgency']]

        for skill in top_risks:
            risk_data.append([
                skill.get('skill', 'N/A')[:25],
                f"{skill.get('mutation_risk', 0):.2f}",
                str(skill.get('employees_affected', 0)),
                skill.get('recommended_transition', 'N/A')[:30],
                skill.get('urgency', 'N/A')
            ])

        risk_table = Table(risk_data, colWidths=[1.8 * inch, 0.7 * inch, 0.9 * inch, 1.8 * inch, 0.8 * inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fecaca'))
        ]))

        elements.append(risk_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_redundancy_alerts(self, alerts: List[Dict[str, Any]]) -> List:
        """Create talent redundancy alerts section"""
        elements = []

        # Section header
        elements.append(Paragraph("Talent Redundancy Alerts (Single Points of Failure)", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        if not alerts:
            elements.append(Paragraph("<i>No critical redundancy risks identified.</i>", self.styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
            return elements

        # Show top 10 critical alerts
        critical_alerts = sorted(alerts, key=lambda x: x.get('criticality_score', 0), reverse=True)[:10]

        alert_data = [['Skill', 'Employees', 'Criticality', 'Risk Level', 'Recommendation']]

        for alert in critical_alerts:
            employees_str = ', '.join(alert.get('employees', [])[:2])
            if len(alert.get('employees', [])) > 2:
                employees_str += '...'

            alert_data.append([
                alert.get('skill', 'N/A')[:20],
                str(alert.get('employee_count', 0)),
                f"{alert.get('criticality_score', 0):.1f}",
                alert.get('risk_level', 'N/A'),
                alert.get('recommendation', 'N/A')[:30]
            ])

        alert_table = Table(alert_data, colWidths=[1.8 * inch, 0.8 * inch, 0.9 * inch, 0.9 * inch, 1.6 * inch])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fffbeb')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fde68a'))
        ]))

        elements.append(alert_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_roi_section(self, roi_analysis: List[Dict[str, Any]]) -> List:
        """Create ROI analysis section"""
        elements = []

        # Section header
        elements.append(Paragraph("High-ROI Training Opportunities", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        if not roi_analysis:
            elements.append(Paragraph("<i>No ROI analysis available.</i>", self.styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
            return elements

        # Show top 10 high-ROI skills
        top_roi = sorted(roi_analysis, key=lambda x: x.get('training_roi_percent', 0), reverse=True)[:10]

        roi_data = [['Skill', 'Current Employees', 'Demand Growth', 'ROI %', 'Strategic Value']]

        for skill in top_roi:
            roi_data.append([
                skill.get('skill', 'N/A')[:25],
                str(skill.get('current_employees', 0)),
                f"{skill.get('demand_growth', 0) * 100:.0f}%",
                f"{skill.get('training_roi_percent', 0):.0f}%",
                skill.get('strategic_value', 'N/A')
            ])

        roi_table = Table(roi_data, colWidths=[2.2 * inch, 1.2 * inch, 1.0 * inch, 0.8 * inch, 1.0 * inch])
        roi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbf7d0'))
        ]))

        elements.append(roi_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_mentorship_section(self, mentorship: List[Dict[str, Any]]) -> List:
        """Create mentorship recommendations section"""
        elements = []

        # Section header
        elements.append(Paragraph("Mentorship & Transition Programs", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        if not mentorship:
            elements.append(Paragraph("<i>No mentorship recommendations available.</i>", self.styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
            return elements

        # Show top 8 mentorship programs
        top_mentorship = mentorship[:8]

        mentorship_data = [['From Skill', 'To Skill', 'Employees', 'Mentors', 'ROI %', 'Timeline']]

        for program in top_mentorship:
            mentorship_data.append([
                program.get('from_skill', 'N/A')[:20],
                program.get('to_skill', 'N/A')[:20],
                str(program.get('employees_needing_transition', 0)),
                str(program.get('mentors_available', 0)),
                f"{program.get('expected_roi_percent', 0):.0f}%",
                f"{program.get('timeline_months', 0)} mo"
            ])

        mentorship_table = Table(mentorship_data, colWidths=[1.5 * inch, 1.5 * inch, 0.9 * inch, 0.8 * inch, 0.7 * inch, 0.7 * inch])
        mentorship_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#eef2ff')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c7d2fe'))
        ]))

        elements.append(mentorship_table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_critical_actions(self, actions: List[Dict[str, Any]]) -> List:
        """Create critical actions section"""
        elements = []

        # Section header
        elements.append(Paragraph("Critical Actions & Recommendations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        if not actions:
            elements.append(Paragraph("<i>No critical actions identified.</i>", self.styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
            return elements

        # Show top 10 actions
        top_actions = actions[:10]

        for i, action in enumerate(top_actions, 1):
            # Handle both string actions and dict actions
            if isinstance(action, str):
                # Simple string action
                action_text = f"<b>{i}. {action}</b>"
            else:
                # Dict action with metadata
                action_text = f"""
                <b>{i}. {action.get('action', 'N/A')}</b><br/>
                Timeline: {action.get('timeline', 'N/A')} |
                Impact: {action.get('impact', 'N/A')} |
                Cost: {action.get('estimated_cost', 'N/A')} |
                Expected ROI: {action.get('expected_roi', 'N/A')}
                """
            elements.append(Paragraph(action_text, self.styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_footer(self) -> List:
        """Create report footer"""
        elements = []

        elements.append(Spacer(1, 0.4 * inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 0.1 * inch))

        footer_text = f"""
        <i>Generated by Skill DNA - Organizational Genome Intelligence Platform</i><br/>
        Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        For more information: https://skill-dna.com
        """
        elements.append(Paragraph(footer_text, self.styles['Normal']))

        return elements


def generate_executive_pdf_report(insights: Dict[str, Any]) -> BytesIO:
    """
    Generate PDF executive report from insights data

    Args:
        insights: Comprehensive insights data from AdvancedInsights

    Returns:
        BytesIO buffer containing PDF data
    """
    # Defensive type checking
    if not isinstance(insights, dict):
        raise TypeError(f"insights must be a dict, got {type(insights).__name__}")

    # Ensure all required keys exist with defaults
    required_keys = [
        'executive_summary', 'mutation_risk_analysis', 'roi_analysis',
        'forecast_accuracy', 'workforce_readiness', 'mentorship_recommendations',
        'talent_redundancy_alerts', 'taxonomy_evolution', 'critical_actions'
    ]

    for key in required_keys:
        if key not in insights:
            print(f"[WARN] Missing key '{key}' in insights, using default empty value")
            insights[key] = {} if key not in ['critical_actions', 'mutation_risk_analysis', 'roi_analysis', 'forecast_accuracy', 'mentorship_recommendations', 'talent_redundancy_alerts'] else []

    generator = PDFExecutiveReport()
    return generator.generate_report(insights)
