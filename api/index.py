import os
import io
import json
import uuid
from http.server import BaseHTTPRequestHandler
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# This is the Vercel Serverless Function Handler
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # --- Read and parse incoming data ---
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # --- Basic variables ---
        file_format = data.get('format', 'docx') # Default to docx
        user_name = data.get('name', 'resume')
        unique_id = uuid.uuid4()
        
        file_path = ""
        content_type = ""
        download_name = ""

        try:
            # --- GENERATE PDF ---
            if file_format == 'pdf':
                content_type = 'application/pdf'
                download_name = f"Resume - {user_name}.pdf"
                file_path = f"/tmp/{unique_id}.pdf"

                doc = SimpleDocTemplate(file_path)
                styles = getSampleStyleSheet()
                story = []

                # Add content to PDF story
                story.append(Paragraph(data.get('name', ''), styles['h1']))
                contact_info = f"{data.get('email', '')} | {data.get('phone', '')} | {data.get('linkedin', '')}"
                story.append(Paragraph(contact_info, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

                if data.get('summary'):
                    story.append(Paragraph("Summary", styles['h2']))
                    story.append(Paragraph(data.get('summary'), styles['BodyText']))
                    story.append(Spacer(1, 0.2*inch))

                if data.get('workExperiences'):
                    story.append(Paragraph("Work Experience", styles['h2']))
                    for job in data.get('workExperiences', []):
                        story.append(Paragraph(f"<b>{job.get('jobTitle', '')}</b> at {job.get('company', '')}", styles['h3']))
                        date_to = 'Present' if job.get('isPresent') else job.get('dateTo', '')
                        story.append(Paragraph(f"<i>{job.get('dateFrom', '')} - {date_to}</i>", styles['Normal']))
                        for line in job.get('jobDescription', '').split('\n'):
                            story.append(Paragraph(f"• {line.strip()}", styles['BodyText']))
                        story.append(Spacer(1, 0.1*inch))
                # (Add similar blocks for Education and Skills)
                doc.build(story)

            # --- GENERATE DOCX ---
            else: # Default to docx
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                download_name = f"Resume - {user_name}.docx"
                file_path = f"/tmp/{unique_id}.docx"
                
                doc = Document()
                doc.add_heading(data.get('name', ''), 0)
                doc.add_paragraph(f"{data.get('email', '')} | {data.get('phone', '')} | {data.get('linkedin', '')}")

                if data.get('summary'):
                    doc.add_heading('Professional Summary', level=1)
                    doc.add_paragraph(data.get('summary'))
                
                if data.get('workExperiences'):
                    doc.add_heading('Work Experience', level=1)
                    for job in data.get('workExperiences', []):
                        if job.get('jobTitle'):
                            doc.add_paragraph(f"{job.get('jobTitle', '')} at {job.get('company', '')}", style='Intense Quote')
                            date_to = 'Present' if job.get('isPresent') else job.get('dateTo', '')
                            doc.add_paragraph(f"{job.get('dateFrom', '')} - {date_to}")
                            for line in job.get('jobDescription', '').split('\n'):
                                if line.strip():
                                    doc.add_paragraph(line.strip(), style='List Bullet')

                # (Add similar blocks for Education and Skills)
                doc.save(file_path)

            # --- Read the generated file from /tmp ---
            with open(file_path, 'rb') as f:
                file_bytes = f.read()

            # --- Send the file back to the user ---
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
        
        finally:
            # --- Clean up the temporary file ---
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return