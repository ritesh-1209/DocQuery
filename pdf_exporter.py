import os
import tempfile
from datetime import datetime
from typing import List, Dict
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import inch

class PDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Question style
        self.styles.add(ParagraphStyle(
            name='Question',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor='#2E86AB',
            spaceBefore=15,
            spaceAfter=5,
            leftIndent=0
        ))
        
        # Answer style
        self.styles.add(ParagraphStyle(
            name='Answer',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=5,
            spaceAfter=10,
            leftIndent=20
        ))
        
        # Source style
        self.styles.add(ParagraphStyle(
            name='Source',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor='#666666',
            spaceBefore=5,
            spaceAfter=5,
            leftIndent=40
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='#888888',
            spaceAfter=20,
            alignment=TA_CENTER
        ))
    
    def export_chat(self, messages: List[Dict], document_name: str) -> str:
        """Export chat messages to PDF"""
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_path = os.path.join(temp_dir, f"chat_export_{timestamp}.pdf")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            title = f"Chat Export: {document_name}"
            story.append(Paragraph(title, self.styles['CustomTitle']))
            
            # Metadata
            export_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata = f"Exported on {export_time}"
            story.append(Paragraph(metadata, self.styles['Metadata']))
            
            # Add separator
            story.append(Spacer(1, 20))
            
            # Process messages
            qa_pairs = self._group_messages_into_qa_pairs(messages)
            
            for i, (question, answer) in enumerate(qa_pairs, 1):
                # Question
                question_text = f"<b>Q{i}:</b> {self._escape_html(question['content'])}"
                story.append(Paragraph(question_text, self.styles['Question']))
                
                # Answer
                answer_text = f"<b>A{i}:</b> {self._escape_html(answer['content'])}"
                story.append(Paragraph(answer_text, self.styles['Answer']))
                
                # Sources (if available)
                if 'sources' in answer and answer['sources']:
                    story.append(Paragraph("<b>Sources:</b>", self.styles['Source']))
                    for source in answer['sources']:
                        source_text = f"• {self._escape_html(source)}"
                        story.append(Paragraph(source_text, self.styles['Source']))
                
                # Add space between Q&A pairs
                if i < len(qa_pairs):
                    story.append(Spacer(1, 15))
            
            # Build PDF
            doc.build(story)
            
            return pdf_path
            
        except Exception as e:
            raise Exception(f"Error exporting chat to PDF: {str(e)}")
    
    def _group_messages_into_qa_pairs(self, messages: List[Dict]) -> List[tuple]:
        """Group messages into question-answer pairs"""
        pairs = []
        current_question = None
        
        for message in messages:
            if message['role'] == 'user':
                current_question = message
            elif message['role'] == 'assistant' and current_question:
                pairs.append((current_question, message))
                current_question = None
        
        return pairs
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters for ReportLab"""
        if not text:
            return ""
        
        # Replace HTML entities
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        # Handle line breaks
        text = text.replace('\n', '<br/>')
        
        return text
    
    def export_document_summary(self, document_info: Dict, chunks_sample: List[str] = None) -> str:
        """Export document summary to PDF"""
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_path = os.path.join(temp_dir, f"document_summary_{timestamp}.pdf")
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []
            
            # Title
            title = f"Document Summary: {document_info['filename']}"
            story.append(Paragraph(title, self.styles['CustomTitle']))
            
            # Document metadata
            story.append(Paragraph("<b>File Information:</b>", self.styles['Heading2']))
            story.append(Paragraph(f"Filename: {document_info['filename']}", self.styles['Normal']))
            story.append(Paragraph(f"Type: {document_info['file_type']}", self.styles['Normal']))
            story.append(Paragraph(f"Upload Date: {document_info['upload_date']}", self.styles['Normal']))
            story.append(Paragraph(f"Size: {document_info['size']}", self.styles['Normal']))
            story.append(Paragraph(f"Total Chunks: {document_info['chunks_count']}", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Sample chunks if provided
            if chunks_sample:
                story.append(Paragraph("<b>Content Sample:</b>", self.styles['Heading2']))
                for i, chunk in enumerate(chunks_sample[:3], 1):
                    story.append(Paragraph(f"<b>Chunk {i}:</b>", self.styles['Normal']))
                    story.append(Paragraph(self._escape_html(chunk[:500] + "..." if len(chunk) > 500 else chunk), self.styles['Normal']))
                    story.append(Spacer(1, 10))
            
            # Build PDF
            doc.build(story)
            
            return pdf_path
            
        except Exception as e:
            raise Exception(f"Error exporting document summary to PDF: {str(e)}")
