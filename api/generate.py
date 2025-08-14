import io
import json
from http.server import BaseHTTPRequestHandler
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# This is the Vercel Serverless Function Handler
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Read and parse incoming data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            # 2. Basic variables
            file_format = data.get('format', 'docx') # Default to docx
            user_name = data.get('name', 'resume')
            
            content_type = ""
            download_name = ""
            file_bytes = None

            # --- Helper function for safe string conversion ---
            def s(text): return str(text) if text is not None else ""

            # --- GENERATE PDF ---
            if file_format == 'pdf':
                content_type = 'application/pdf'
                download_name = f"Resume - {s(user_name)}.pdf"
                
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer)
                styles = getSampleStyleSheet()
                story = []

                # Add content to PDF story
                story.append(Paragraph(s(data.get('name')), styles['h1']))
                contact_info = f"{s(data.get('email'))} | {s(data.get('phone'))} | {s(data.get('linkedin'))}"
                story.append(Paragraph(contact_info, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

                if data.get('summary'):
                    story.append(Paragraph("Summary", styles['h2']))
                    story.append(Paragraph(s(data.get('summary')), styles['BodyText']))
                    story.append(Spacer(1, 0.2*inch))

                if data.get('workExperiences'):
                    story.append(Paragraph("Work Experience", styles['h2']))
                    for job in data.get('workExperiences', []):
                        story.append(Paragraph(f"<b>{s(job.get('jobTitle'))}</b> at {s(job.get('company'))}", styles['h3']))
                        date_to = 'Present' if job.get('isPresent') else s(job.get('dateTo'))
                        story.append(Paragraph(f"<i>{s(job.get('dateFrom'))} - {date_to}</i>", styles['Normal']))
                        for line in s(job.get('jobDescription')).split('\n'):
                            if line.strip(): story.append(Paragraph(f"• {line.strip()}", styles['BodyText']))
                        story.append(Spacer(1, 0.1*inch))
                
                # (You can add similar blocks for Education and Skills here)
                doc.build(story)
                file_bytes = buffer.getvalue()

            # --- GENERATE DOCX ---
            else: # Default to docx
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                download_name = f"Resume - {s(user_name)}.docx"
                
                doc = Document()
                doc.add_heading(s(data.get('name')), 0)
                doc.add_paragraph(f"{s(data.get('email'))} | {s(data.get('phone'))} | {s(data.get('linkedin'))}")
                if data.get('summary'):
                    doc.add_heading('Professional Summary', level=1)
                    doc.add_paragraph(s(data.get('summary')))
                if data.get('workExperiences'):
                    doc.add_heading('Work Experience', level=1)
                    for job in data.get('workExperiences', []):
                        if job.get('jobTitle'):
                            doc.add_paragraph(f"{s(job.get('jobTitle'))} at {s(job.get('company'))}", style='Intense Quote')
                            date_to = 'Present' if job.get('isPresent') else s(job.get('dateTo'))
                            doc.add_paragraph(f"{s(job.get('dateFrom'))} - {date_to}")
                            for line in s(job.get('jobDescription')).split('\n'):
                                if line.strip(): doc.add_paragraph(line.strip(), style='List Bullet')
                # (Add similar blocks for Education and Skills here)
                
                file_stream = io.BytesIO()
                doc.save(file_stream)
                file_stream.seek(0)
                file_bytes = file_stream.read()

            # --- 5. Send the file back to the user ---
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{download_name}"')
            self.end_headers()
            self.wfile.write(file_bytes)

        except Exception as e:
            print(f"MAIN ERROR: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': 'An internal server error occurred while generating the file.'})
            self.wfile.write(error_response.encode('utf-8'))
        
        return