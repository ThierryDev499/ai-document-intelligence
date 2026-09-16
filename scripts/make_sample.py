from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

root = Path(__file__).resolve().parent.parent
folder = root / 'examples'
folder.mkdir(exist_ok=True)
styles = getSampleStyleSheet()
styles['Title'].textColor = colors.HexColor('#086b62')
story = [Paragraph('Atlas Operations Handbook', styles['Title']),
         Paragraph('Fictional demonstration data / Revision 1.0', styles['Normal']), Spacer(1, 28)]
for title, body in [
    ('Support response times', 'Critical incidents receive an initial response within 30 minutes. Standard requests receive an initial response within 8 business hours. Support hours are Monday to Friday, 09:00 to 18:00 Brasilia time.'),
    ('Escalation policy', 'An incident affecting all users is classified as critical. The operations coordinator assigns an incident owner and records an update every 60 minutes until service recovery.'),
    ('Data retention', 'Operational execution logs are retained for 90 days. Customer uploads are deleted after 30 days. Access is restricted to the assigned operations team.'),
    ('Change management', 'Production changes require peer review, a rollback plan and approval by the service owner. Scheduled deployments take place on Tuesdays at 20:00 Brasilia time.'),
    ('Billing', 'Invoices are issued on the first business day of each month. Payment terms are 15 calendar days. Billing disputes must include the invoice number and be sent to billing@example.test.'),
]:
    story.extend([Paragraph(title, styles['Heading2']), Paragraph(body, styles['BodyText']), Spacer(1, 12)])
SimpleDocTemplate(str(folder / 'operations-handbook.pdf')).build(story)
print('Generated fictional sample PDF.')
