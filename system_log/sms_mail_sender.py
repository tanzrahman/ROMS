import datetime
import requests
from django.conf import settings
from manpower.models import User, Profile
from system_log.models import MailAndSMSLog
import smtplib, ssl

def mail_and_send_sms(msg_body, user=None, subject=None):
    print("Send Mail, SMS to ",user.email)

   # user = User.objects.get(username='omar.faruk384')
    if(settings.DEBUG==True):
        print("Successfully called SMS/Mailer ",msg_body)
        return

    receiver_phone = user.profile.phone
    receiver_email = user.email

    api_url = "https://api.greenweb.com.bd/api.php"

    token = settings.SMS_TOKEN

    data = {"token": token,
            "to": receiver_phone,
            "message": msg_body
            }

    response = requests.post(url=api_url, data=data)

    sms_success = False
    sms_error = ""
    email_error = ""
    email_success = False
    if (response.status_code == 200):
        if ('Successfully' in response.text):
            sms_success = True
        else:
            sms_error = response.text

    current_time = datetime.datetime.now()

    smtp_server = settings.EMAIL_HOST
    port = settings.SMTP_PORT  # For starttls
    sender_email = settings.EMAIL_SENDER
    password = settings.EMAIL_PASS

    # Create a secure SSL context
    context = ssl.create_default_context()


    message_details = 'Subject: Task Assignment \n\n' + msg_body
    if(subject):
        message_details = 'Subject: ' + subject + '\n\n' + msg_body

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        resp = server.sendmail(from_addr=sender_email, to_addrs=user.email, msg=message_details)

    except Exception as e:
        # Print any error messages to stdout
        print(e)
        email_error = e.__str__()
    finally:
        server.quit()

    if(email_error == ""):
        email_success = True

    new_log = MailAndSMSLog(receiver=user, message_body=msg_body, send_time=current_time,
                            email=receiver_email, phone_no=receiver_phone,
                            sms_success=sms_success, email_success=email_success,
                            sms_error_reason=sms_error, email_error_reason=email_error)
    new_log.save()


def doc_review_mail_and_send_sms(msg_body, user=None, task_id=None, subject=None):
    print("Send Mail, SMS to ", user.email)

   # user = User.objects.get(username='omar.faruk384')
    if(settings.DEBUG==True):
        print("Successfully called SMS/Mailer ", msg_body)
        return

    receiver_phone = user.profile.phone
    receiver_email = user.email

    api_url = "https://api.greenweb.com.bd/api.php"

    token = settings.SMS_TOKEN

    data = {"token": token,
            "to": receiver_phone,
            "message": msg_body
            }

    response = requests.post(url=api_url, data=data)

    sms_success = False
    sms_error = ""
    email_error = ""
    email_success = False
    if (response.status_code == 200):
        if ('Successfully' in response.text):
            sms_success = True
        else:
            sms_error = response.text

    current_time = datetime.datetime.now()

    smtp_server = settings.EMAIL_HOST
    port = settings.SMTP_PORT  # For starttls
    sender_email = settings.EMAIL_SENDER
    password = settings.EMAIL_PASS

    # Create a secure SSL context
    context = ssl.create_default_context()


    message_details = f'Subject: Document ({task_id}) Review Comment from MD\n\n{str(msg_body)}'
    if(subject):
        message_details = f'Subject: Document ({task_id}) Review Comment from MD\n\n{str(msg_body)}'

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        resp = server.sendmail(from_addr=sender_email, to_addrs=user.email, msg=message_details)

    except Exception as e:
        # Print any error messages to stdout
        print(e)
        email_error = e.__str__()
    finally:
        server.quit()

    if(email_error == ""):
        email_success = True

    new_log = MailAndSMSLog(receiver=user, message_body=msg_body, send_time=current_time,
                            email=receiver_email, phone_no=receiver_phone,
                            sms_success=sms_success, email_success=email_success,
                            sms_error_reason=sms_error, email_error_reason=email_error)
    new_log.save()


def send_email_only(msg_body, subject=None, receiver_email=None):
    print("Send Mail to ", receiver_email)

   # user = User.objects.get(username='tanziar.rahman523')
    if(settings.DEBUG==True):
        print("Successfully called SMS/Mailer")
        return


    current_time = datetime.datetime.now()

    smtp_server = settings.EMAIL_HOST
    port = settings.SMTP_PORT  # For starttls
    sender_email = settings.EMAIL_SENDER
    password = settings.EMAIL_PASS

    # Create a secure SSL context
    context = ssl.create_default_context()

    message_details = 'Subject: Task Assignment \n\n' + msg_body
    if(subject):
        message_details = "Subject: {} \n\n {}".format(subject,msg_body)

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        resp = server.sendmail(from_addr=sender_email, to_addrs=receiver_email, msg=message_details)

        if(receiver_email):
            if(User.objects.filter(email=receiver_email).count()>0):
                receiver = User.objects.get(email=receiver_email)
                new_log = MailAndSMSLog(receiver=receiver, message_body=msg_body, send_time=current_time,sms_success=False,
                                        sms_error_reason="Not Send", email=receiver_email, email_success=True, email_error_reason="")
                new_log.save()

    except Exception as e:
        # Print any error messages to stdout
        email_error = e.__str__()
        print("EMAIL_SEND_FAIL: ", e.__str__())
    finally:
        server.quit()



def send_email_with_cc(msg_body, subject=None, receiver_email=None,CC=None):
    print("Send Mail to ", receiver_email)

   # user = User.objects.get(username='omar.faruk384')
    if(settings.DEBUG==True):
        print("Successfully called SMS/Mailer")
        return

    all_receivers = CC
    all_receivers.append(receiver_email)

    current_time = datetime.datetime.now()

    smtp_server = settings.EMAIL_HOST
    port = settings.SMTP_PORT  # For starttls
    sender_email = settings.EMAIL_SENDER
    password = settings.EMAIL_PASS

    # Create a secure SSL context
    context = ssl.create_default_context()
    info = [f"From: {sender_email}\r\n", f"To: {receiver_email}\r\n", f"CC: {', '.join(CC)}\r\n", ""]

    message_details = "".join(info) + "Subject: Task Assignment \n\n" + msg_body
    if(subject):
        message_details = "".join(info) + "Subject: {} \n\n {}".format(subject, msg_body)

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        resp = server.sendmail(from_addr=sender_email, to_addrs=all_receivers, msg=message_details)

    except Exception as e:
        # Print any error messages to stdout
        email_error = e.__str__()
        print("EMAIL_SEND_FAIL: ", e.__str__())
    finally:
        server.quit()

    print("DOC_REQ_EMAIL_SENT")
