import smtplib
import sys
import os
import io
import re
from optparse import OptionParser
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import COMMASPACE
from email import encoders
from datetime import datetime
import json
import RandomEmailGenerator
import email_object
import time
import math


def custom_join(list_of_strings, sep):
    strings = ''
    for string in list_of_strings:
        if (string is not None and string.strip() != ''):
            strings += string + sep

    # remove trailing char
    strings = strings.rstrip(sep)

    return strings


def replace_emaildomain(options, line):
    if (options.domain_name):
        if "@" in line:
            line = re.sub(r"(?<=@)[^.]+(?=\.)[^,]*", options.domain_name, line)
        else:
            line += "@" + options.domain_name
    return line


# mail_random_emails - mails randomized generated emails
def mail_random_emails(options):
    count = 0
    failed_count = 0
    server = None
    try:
        server = mail_connect(options)
    except smtplib.SMTPException:
        # retry
        server = mail_connect(options)

    if (server is None and not options.dryrun):
        print('Failed to connect to smtp server: ', options.serveraddr)
        return

    if (options.json_output_path is None):
        json_output_file = "emails_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".json"
    else:
        json_output_file = options.json_output_path

    random_emails_json = "["
    email_gtr = RandomEmailGenerator.EmailGenerator(
        addresses_file_path=options.addresses_file,
        attachments_dir_path=options.attachments_dir,
        text_model_file_path=options.text_model_file,
        domain_name=options.domain_name)

    attachmentLimit = 0

    if (options.attachment_percent < 0 or options.attachment_percent > 100):
        includeAttachments = 2
    elif (options.attachment_percent == 0):
        includeAttachments = 0
    else:
        includeAttachments = 1
        attachmentLimit = math.ceil(options.quanity * options.attachment_percent / 100)

    attachmentCount = 0

    for i in range(options.quanity):
        random_email = None
        random_email = email_gtr.get_email(include_attachments=includeAttachments)

        msg = MIMEMultipart()
        msg['From'] = replace_emaildomain(options, random_email.sender[0])
        msg['Date'] = random_email.sent_date
        msg['Subject'] = random_email.subject[0]

        if (random_email.to is None or len(random_email.to) == 0):
            msg['To'] = 'shouldnthappen@devtest-jb.com'
        elif len(random_email.to) > 1:
            msg['To'] = replace_emaildomain(options, custom_join(random_email.to, ', '))
        else:
            msg['To'] = random_email.to[0]

        if (random_email.cc is None or len(random_email.cc) == 0):
            msg['cc'] = ''
        elif len(random_email.cc) > 1:
            msg['cc'] = replace_emaildomain(options, custom_join(random_email.cc, ', '))
        else:
            msg['cc'] = random_email.cc[0]

        if (random_email.bcc is None or len(random_email.bcc) == 0):
            msg['bcc'] = ''
        elif len(random_email.bcc) > 1:
            msg['bcc'] = replace_emaildomain(options, custom_join(random_email.bcc, ', '))
        else:
            msg['bcc'] = random_email.bcc[0]

        if (random_email.body is None or len(random_email.body) == 0):
            msg.attach(MIMEText('This shouldn\'t happen but just in case.... \n'))
        elif len(random_email.body) > 1:
            msg.attach(MIMEText(custom_join(random_email.body, '\n'), 'plain', 'utf-8'))
        else:
            msg.attach(MIMEText(random_email.body[0].encode('utf-8'), 'plain', 'utf-8'))

        if (attachmentLimit <= attachmentCount and includeAttachments < 2):
            random_email.b_attachments = None
            random_email.attachments = list()

        if (random_email.b_attachments == 1):
            attachmentCount = attachmentCount + 1

            for attachment in random_email.attachments:
                file_name = options.attachments_dir + attachment
                part = MIMEBase('application', "octet-stream")

                with open(file_name, "rb") as f:
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    'attachment; filename="{0}"'.format(os.path.basename(file_name)))
                msg.attach(part)

        # output email obj json to later write to file
        if options.json_copy:
            random_emails_json += json.dumps(random_email, cls=email_object.ComplexEncoder, ensure_ascii=False) + ','

        try:
            mail(server, options, msg)
        except Exception:
            # output failed email
            failed_email_file = "failedemails_" + datetime.now().strftime("%Y%m%d") + ".json"
            failed_email_json = json.dumps(random_email, cls=email_object.ComplexEncoder, ensure_ascii=False) + ','
            # should put this in consumable json format...
            with io.open(failed_email_file, "a+", encoding="utf8") as f:
                f.write(failed_email_json)
            failed_count = failed_count + 1

        count = count + 1
        if (count % 1000 == 0):
            print(str(count) + ' emails generated')

        if (options.json_copy and count % 100000 == 0):
            # remove trailing comma and write json to file
            with io.open(json_output_file, "a+", encoding="utf8") as f:
                f.write(random_emails_json)
            random_emails_json = ''

    if options.json_copy:
        random_emails_json = random_emails_json.rstrip(',') + "]"
        with io.open(json_output_file, "a+", encoding="utf8") as f:
            f.write(random_emails_json)

    mail_disconnect(options, server)
    if options.verbose:
        print("Attachment count: " + str(attachmentCount))
        print("Attachment Limit: " + str(attachmentLimit))

    print(str(count - failed_count) + ' emails successfully sent.')
    print(str(failed_count) + ' failed emails.')

    if (options.verbose and options.json_copy):
        print("Emails copied to: " + json_output_file)
        if (failed_count > 0):
            print("Failed emails copied to: " + failed_email_file)


# mail_input_emails - mails emails from an given json file
def mail_input_emails(options):
    count = 0
    failed_count = 0
    server = None

    with io.open(options.json_input, "r", encoding="utf8") as f:
        emails_json = f.read()

    try:
        server = mail_connect(options)
    except smtplib.SMTPException:
        # retry
        server = mail_connect(options)

    if (server is None and not options.dryrun):
        print('Failed to connect to smtp server: ', options.serveraddr)
        return

    emails_input = json.loads(emails_json, encoding="utf8")
    for em in emails_input:
        try:
            msg = MIMEMultipart()
            msg['From'] = replace_emaildomain(options, em['sender'])
            msg['Date'] = em['sentdate']
            msg['Subject'] = em['subject']

            if (em['to'] is None or len(em['to']) == 0):
                msg['To'] = 'shouldnthappen@devtest-jb.com'
            elif len(em['to']) > 1:
                msg['To'] = replace_emaildomain(options, custom_join(em['to'], ', '))
            else:
                msg['To'] = replace_emaildomain(options, em['to'][0])

            if (em['cc'] is None or len(em['cc']) == 0):
                msg['cc'] = ''
            elif len(em['cc']) > 1:
                msg['cc'] = replace_emaildomain(options, custom_join(em['cc'], ', '))
            elif len(em['cc']) == 1:
                msg['cc'] = replace_emaildomain(options, em['cc'][0])

            if (em['bcc'] is None or len(em['bcc']) == 0):
                msg['bcc'] = ''
            elif len(em['bcc']) > 1:
                msg['bcc'] = replace_emaildomain(options, custom_join(em['bcc'], ', '))
            elif len(em['bcc']) == 1:
                msg['bcc'] = replace_emaildomain(options, em['bcc'][0])

            if (em['body'] is None or len(em['body']) == 0):
                msg.attach(MIMEText('This shouldnt happen, but just in case...'))
            elif len(em['body']) > 1:
                msg.attach(MIMEText(custom_join(em['body'], '\n').encode('utf-8'), 'plain', 'utf-8'))
            else:
                msg.attach(MIMEText(em['body'][0].encode('utf-8'), 'plain', 'utf-8'))

            if em['attachments'] is not None:
                for attachment in em['attachments']:
                    file_name = options.attachments_dir + attachment
                    part = MIMEBase('application', "octet-stream")

                    with open(file_name, "rb") as f:
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment; filename="{0}"'
                                        .format(os.path.basename(file_name).encode('utf-8')))
                    msg.attach(part)

            # if options.verbose:
            #    print(msg)

            mail(server, options, msg)
        except Exception as e:
            print(e)
            # output failed email
            failed_email_file = "failedemails_" + datetime.now().strftime("%Y%m%d") + ".json"
            failed_email_json = json.dumps(em, cls=email_object.ComplexEncoder) + ','
            # should put this in consumable json format...
            with io.open(failed_email_file, "a+", encoding="utf8") as f:
                f.write(failed_email_json)
            failed_count = failed_count + 1

        count = count + 1
        time.sleep(0.01)
        if (count % 1000 == 0):
            # sleep for 3 secs, don't want to overload smtp server
            time.sleep(3)
            print(str(count) + ' emails sent...')

    mail_disconnect(options, server)
    print(str(count - failed_count) + ' emails successfully sent.')
    print(str(failed_count) + ' failed emails.')


def mail_connect(options):
    server = None
    if options.usessl:
        server = smtplib.SMTP_SSL()
    else:
        server = smtplib.SMTP()

    if not options.dryrun:
        server.set_debuglevel(options.debuglevel)
        server.connect(options.serveraddr, options.serverport)
        if options.usetls: server.starttls()
        if options.SMTP_USER != "": server.login(options.SMTP_USER, options.SMTP_PASS)

    return server


def mail_disconnect(options, server):
    if not options.dryrun:
        server.quit()


def mail(server, options, msg):
    if not options.dryrun:
        try:
            server.sendmail(options.fromaddr, options.toaddr, msg.as_string())
        except smtplib.SMTPException:
            # try again
            try:
                server.sendmail(options.fromaddr, options.toaddr, msg.as_string())
            except smtplib.SMTPException:
                raise Exception('Failed to send email!')

    return server


def main():
    usage = "Usage: %prog [options] fromaddr toaddr serveraddress"
    parser = OptionParser(usage=usage)

    parser.set_defaults(usetls=False)
    parser.set_defaults(usessl=False)
    parser.set_defaults(serverport=25)
    parser.set_defaults(SMTP_USER="")
    parser.set_defaults(SMTP_PASS="")
    parser.set_defaults(debuglevel=0)
    parser.set_defaults(verbose=False)
    parser.set_defaults(quanity=1)
    parser.set_defaults(dryrun=False)
    parser.set_defaults(json_copy=False)
    parser.set_defaults(json_input="")
    parser.set_defaults(json_output_path=None)
    parser.set_defaults(attachment_percent=-1)
    parser.set_defaults(addresses_file="./Content/emailaddresses.txt")
    parser.set_defaults(attachments_dir=u"./Content/Attachments/")
    parser.set_defaults(text_model_file="./Content/news_articles.txt")
    parser.set_defaults(domain_name=None)
    parser.set_defaults(fromaddr="")
    parser.set_defaults(toaddr="")
    parser.set_defaults(serveraddr="")

    parser.add_option("-t", "--usetls", action="store_true", dest="usetls", default=False,
                      help="Connect using TLS, default is false")
    parser.add_option("-s", "--usessl", action="store_true", dest="usessl", default=False,
                      help="Connect using SSL, default is false")
    parser.add_option("-n", "--port", action="store", type="int", dest="serverport", help="SMTP server port",
                      metavar="nnn")
    parser.add_option("-u", "--username", action="store", type="string", dest="SMTP_USER",
                      help="SMTP server auth username", metavar="username")
    parser.add_option("-p", "--password", action="store", type="string", dest="SMTP_PASS",
                      help="SMTP server auth password", metavar="password")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose message printing")
    parser.add_option("-l", "--debuglevel", type="int", dest="debuglevel",
                      help="Set to 1 to print smtplib.send messages", metavar="n")
    parser.add_option("-q", "--quanity", type="int", dest="quanity", help="Number of emails to be generated",
                      metavar="n")
    parser.add_option("-r", "--dryrun", action="store_true", dest="dryrun", help="Execute script without sending email")
    parser.add_option("-i", "--jsoninput", action="store", type="string", dest="json_input",
                      help="Sends emails from json file", metavar="filepath")
    parser.add_option("-j", "--jsonoutput", action="store_true", dest="json_copy",
                      help="Copies emails to json file for email data ingestion")
    parser.add_option("-o", "--jsonoutputfile", action="store", type="string", dest="json_output_path",
                      help="File path for emails copies to json file for email data ingestion", metavar="filepath")
    parser.add_option("-c", "--attachmentpercent", type="int", dest="attachment_percent",
                      help="Int value for percentage of emails to include attachments", metavar="n")
    parser.add_option("-f", "--addressesfile", action="store", type="string", dest="addresses_file",
                      help="Email addresses to use for generated emails", metavar="filepath")
    parser.add_option("-a", "--attachmentsdir", action="store", type="string", dest="attachments_dir",
                      help="Attachments to use for generated emails", metavar="filepath")
    parser.add_option("-x", "--textmodelfile", action="store", type="string", dest="text_model_file",
                      help="Input text to use for generated subject and body of emails", metavar="filepath")
    parser.add_option("-d", "--domainname", action="store", type="string", dest="domain_name",
                      help="Adds/replaces domains of provided email addresses", metavar="domainname")

    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.print_help()
        parser.error("incorrect number of arguments")
        sys.exit(-1)

    options.fromaddr = args[0]
    options.toaddr = args[1]
    options.serveraddr = args[2]

    if options.verbose:
        print('usetls             : ', options.usetls)
        print('usessl             : ', options.usessl)
        print('server address     : ', options.serveraddr)
        print('server port        : ', options.serverport)
        print('envelope sender    : ', options.fromaddr)
        print('envelope recipient : ', options.toaddr)
        print('smtp username      : ', options.SMTP_USER)
        print('smtplib debuglevel : ', options.debuglevel)
        print('dryrun             : ', options.dryrun)
        print('json copy          : ', options.json_copy)
        print('json input         : ', options.json_input)
        print('json output        : ', options.json_output_path)
        if not options.json_input:
            print('# of emails        : ', str(options.quanity))
        if options.attachment_percent > 0:
            print('   w/ attachments  : ', str(math.ceil(options.quanity * options.attachment_percent / 100)))
        print('addresses filepath   : ', options.addresses_file)
        print('attachments dirpath  : ', options.attachments_dir)
        print('text model filepath  : ', options.text_model_file)
        print('domain name        : ', options.domain_name)

        if (options.json_input == ""):
            print('Generating ' + str(options.quanity) + ' emails...')
            mail_random_emails(options)
        else:
            print('Sending emails from', options.json_input)
            mail_input_emails(options)


def interf(options):
    if (options.json_input == ""):
        print('Generating ' + str(options.quanity) + ' emails...')
        mail_random_emails(options)
    else:
        print('Sending emails from', options.json_input)
        mail_input_emails(options)


if __name__ == "__main__":
    main()
