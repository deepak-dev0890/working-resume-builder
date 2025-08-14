# Serverless function for Vercel (Python) that returns DOCX or PDF
import io
import json
from http.server import BaseHTTPRequestHandler
from docx import Document

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # --- Read JSON body ---
            content_length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(raw.decode('utf-8') or "{}")

            # --- Helpers ---
            def s(val): return str(val) if val is not None else ""
            def split_skills(val):
                if isinstance(val, list):
                    return [s(x).strip() for x in val if s(x).strip()]
                return [x.strip() for x in s(val).split(',') if x.strip()]

            file_format = (data.get('format') or 'docx').lower()  # 'docx' | 'pdf'
            user_name   = s(data.get('name') or "resume").strip() or "resume"

            # --- Build file bytes ---
            if file_format == 'pdf':
                # ---------- PDF ----------
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer)
                styles = getSampleStyleSheet()

                story = []
                # Header
                story.append(Paragraph(s(data.get('name')), styles['Title']))
                contact = " | ".join(
                    [x for x in [s(data.get('email')), s(data.get('phone')), s(data.get('linkedin'))] if x]
                )
                if contact:
                    story.append(Paragraph(contact, styles['Normal']))
                    story.append(Spacer(1, 0.2 * inch))

                # Summary
                if s(data.get('summary')):
                    story.append(Paragraph("Professional Summary", styles['Heading2']))
                    story.append(Paragraph(s(data.get('summary')), styles['BodyText']))
                    story.append(Spacer(1, 0.2 * inch))

                # Work Experience
                work_list = data.get('workExperiences') or []
                if any((job or {}).get('jobTitle') for job in work_list):
                    story.append(Paragraph("Work Experience", styles['Heading2']))
                    for job in work_list:
                        job = job or {}
                        if not job.get('jobTitle'):
                            continue
                        title_line = f"<b>{s(job.get('jobTitle'))}</b> at {s(job.get('company'))}"
                        story.append(Paragraph(title_line, styles['Heading3']))
                        date_to = 'Present' if job.get('isPresent') else s(job.get('dateTo'))
                        when = f"{s(job.get('dateFrom'))} - {date_to}"
                        loc = s(job.get('location'))
                        info_line = " | ".join([x for x in [when, loc] if x])
                        if info_line:
                            story.append(Paragraph(info_line, styles['Italic']))
                        # bullet points
                        bullets = []
                        for line in s(job.get('jobDescription')).split('\n'):
                            line = line.strip().lstrip('-•').strip()
                            if line:
                                bullets.append(Paragraph(line, styles['BodyText']))
                        if bullets:
                            story.append(ListFlowable([ListItem(b) for b in bullets], bulletType='bullet'))
                        story.append(Spacer(1, 0.12 * inch))

                # Education
                edu_list = data.get('educations') or []
                if any((edu or {}).get('degree') for edu in edu_list):
                    story.append(Paragraph("Education", styles['Heading2']))
                    for edu in edu_list:
                        edu = edu or {}
                        if not edu.get('degree'):
                            continue
                        heading = f"<b>{s(edu.get('degree'))}</b> at {s(edu.get('school'))}"
                        story.append(Paragraph(heading, styles['Heading3']))
                        date_to = 'Present' if edu.get('isPresent') else s(edu.get('dateTo'))
                        when = f"{s(edu.get('dateFrom'))} - {date_to}"
                        if when.strip() != " - ":
                            story.append(Paragraph(when, styles['Italic']))
                        story.append(Spacer(1, 0.06 * inch))

                # Skills
                skills = split_skills(data.get('skills'))
                if skills:
                    story.append(Paragraph("Skills", styles['Heading2']))
                    story.append(ListFlowable(
                        [ListItem(Paragraph(skil, styles['BodyText'])) for skil in skills],
                        bulletType='bullet'
                    ))

                doc.build(story)
                file_bytes = buffer.getvalue()
                content_type = 'application/pdf'
                download_name = f'Resume - {user_name}.pdf'

            else:
                # ---------- DOCX ----------
                doc = Document()
                doc.add_heading(s(data.get('name')), 0)
                contact = " | ".join(
                    [x for x in [s(data.get('email')), s(data.get('phone')), s(data.get('linkedin'))] if x]
                )
                if contact:
                    doc.add_paragraph(contact)

                if s(data.get('summary')):
                    doc.add_heading('Professional Summary', level=1)
                    doc.add_paragraph(s(data.get('summary')))

                work_list = data.get('workExperiences') or []
                if any((job or {}).get('jobTitle') for job in work_list):
                    doc.add_heading('Work Experience', level=1)
                    for job in work_list:
                        job = job or {}
                        if not job.get('jobTitle'):
                            continue
                        doc.add_paragraph(f"{s(job.get('jobTitle'))} at {s(job.get('company'))}", style='Intense Quote')
                        date_to = 'Present' if job.get('isPresent') else s(job.get('dateTo'))
                        when = f"{s(job.get('dateFrom'))} - {date_to}"
                        loc = s(job.get('location'))
                        info_line = " | ".join([x for x in [when, loc] if x])
                        if info_line:
                            doc.add_paragraph(info_line)
                        for line in s(job.get('jobDescription')).split('\n'):
                            line = line.strip().lstrip('-•').strip()
                            if line:
                                doc.add_paragraph(line, style='List Bullet')

                edu_list = data.get('educations') or []
                if any((edu or {}).get('degree') for edu in edu_list):
                    doc.add_heading('Education', level=1)
                    for edu in edu_list:
                        edu = edu or {}
                        if not edu.get('degree'):
                            continue
                        doc.add_paragraph(f"{s(edu.get('degree'))} at {s(edu.get('school'))}", style='Intense Quote')
                        date_to = 'Present' if edu.get('isPresent') else s(edu.get('dateTo'))
                        when = f"{s(edu.get('dateFrom'))} - {date_to}"
                        if when.strip() != " - ":
                            doc.add_paragraph(when)

                skills = split_skills(data.get('skills'))
                if skills:
                    doc.add_heading('Skills', level=1)
                    for skil in skills:
                        doc.add_paragraph(skil, style='List Bullet')

                stream = io.BytesIO()
                doc.save(stream)
                stream.seek(0)
                file_bytes   = stream.read()
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                download_name = f'Resume - {user_name}.docx'

            # --- Response ---
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{download_name}"')
            self.end_headers()
            self.wfile.write(file_bytes)

        except Exception as e:
            try:
                print("ERROR in /api/generate:", repr(e))
            except Exception:
                pass
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'An internal server error occurred while generating the file.'
            }).encode('utf-8'))
