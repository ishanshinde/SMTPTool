import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

address_book = ['person1@company.com', 'person2@company.com', 'group3@company.com']
msg = MIMEMultipart()
sender = 'me@company.com'
subject = "My subject"
body = "This is my email body"

msg['From'] = sender
msg['To'] = ','.join(address_book)
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))
text=msg.as_string()
#print text
# Send the message via our SMTP server
s = smtplib.SMTP('usw80cavsmtp01')
s.sendmail(sender,address_book, text)
s.quit()