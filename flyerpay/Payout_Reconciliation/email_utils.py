import imaplib
import email
from email.header import decode_header
import datetime
import re
from django.conf import settings

from .models import SentEmailLog


def clean_subject(raw_subject):
    """
    Removes common reply/forward prefixes like 'Re:', 'Fwd:' etc. and trims spaces.
    """
    if not raw_subject:
        return ""
    # Keep removing prefixes like Re:, Fwd: from the start
    while True:
        new_subject = re.sub(r"^(re:|fwd:)\s*", "", raw_subject, flags=re.IGNORECASE)
        if new_subject == raw_subject:
            break
        raw_subject = new_subject

    # Collapse multiple spaces/newlines to a single space
    cleaned = re.sub(r"\s+", " ", raw_subject)
    print(cleaned)
    return cleaned.strip().lower()


def fetch_replies_from_gmail(username, password, subject_filter=None, sender_filter=None, since_days=None):
    try:
        print("Fetching......")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")

        cleaned_subject_filter = clean_subject(subject_filter)
        since_date = (datetime.date.today() - datetime.timedelta(days=since_days)).strftime("%d-%b-%Y")

        result, data = mail.search(None, f'(SINCE "{since_date}")')
        if result != 'OK':
            print("No messages found!")
            return []

        reply_emails = []

        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != 'OK':
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_ = msg.get("From")
            print(from_.lower(),"from.lower")
            if sender_filter and sender_filter.lower() not in from_.lower():
                continue  # Skip if sender doesn't match

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                try:
                    subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                except:
                    subject = subject.decode("utf-8", errors="ignore")

            cleaned_subject = clean_subject(subject)
            if cleaned_subject.strip().lower() != cleaned_subject_filter.strip().lower():
                continue

            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        charset = part.get_content_charset()
                        try:
                            body = part.get_payload(decode=True).decode(charset if charset else "utf-8", errors="ignore")
                        except:
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                charset = msg.get_content_charset()
                try:
                    body = msg.get_payload(decode=True).decode(charset if charset else "utf-8", errors="ignore")
                except:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            reply_emails.append({
                "subject": subject.strip(),
                "from": from_,
                "body": body.strip(),
                "date": msg.get("Date"),
            })

        mail.logout()
        return reply_emails

    except Exception as e:
        print("Error fetching replies:", str(e))
        return []



# def fetch_replies_from_gmail(username, password, subject_filter=None, since_days=30):
#     try:
#         # Connect to Gmail IMAP
#         print("Fetching......")
#         mail = imaplib.IMAP4_SSL("imap.gmail.com")
#         mail.login(username, password)
#         mail.select("inbox")
#         cleaned_subject_filter = clean_subject(subject_filter)
#         print(cleaned_subject_filter.strip().lower(),"subject_filter")
#         # Search emails since X days ago
#         since_date = (datetime.date.today() - datetime.timedelta(days=since_days)).strftime("%d-%b-%Y")
#         result, data = mail.search(None, f'(SINCE "{since_date}")')
#         print(result,"result")
#         print(data,"data")
#         if result != 'OK':
#             print("No messages found!")
#             return []

#         reply_emails = []

#         for num in data[0].split():
#             result, msg_data = mail.fetch(num, "(RFC822)")
#             # print(result,"result2")
#             if result != 'OK':
#                 # print("Fetching 1")
#                 continue

#             raw_email = msg_data[0][1]
#             msg = email.message_from_bytes(raw_email)

#             # Decode subject
#             subject, encoding = decode_header(msg["Subject"])[0]
#             # print(subject.strip(),"Subject11 ")
#             if isinstance(subject, bytes):
#                 try:
#                     subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
#                     # print(subject.strip(),"Subject.strip()")
#                     # cleaned_subject = clean_subject(subject)
#                 except:
#                     subject = subject.decode("utf-8", errors="ignore")
            
#             cleaned_subject = clean_subject(subject)
#             # print(cleaned_subject.strip().lower(),"Subject.strip()")
#             if  cleaned_subject.strip().lower() != cleaned_subject_filter.strip().lower():
#                 continue  # exact subject match

#             from_ = msg.get("From")

#             print(from_,"from_")

#             # Get email body
#             body = ""
#             if msg.is_multipart():
#                 for part in msg.walk():
#                     content_type = part.get_content_type()
#                     content_disposition = str(part.get("Content-Disposition"))
#                     if content_type == "text/plain" and "attachment" not in content_disposition:
#                         charset = part.get_content_charset()
#                         try:
#                             body = part.get_payload(decode=True).decode(charset if charset else "utf-8", errors="ignore")
#                         except:
#                             body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
#                         break
#             else:
#                 charset = msg.get_content_charset()
#                 try:
#                     body = msg.get_payload(decode=True).decode(charset if charset else "utf-8", errors="ignore")
#                 except:
#                     body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

#             reply_emails.append({
#                 "subject": subject.strip(),
#                 "from": from_,
#                 "body": body.strip(),
#                 "date": msg.get("Date"),
#             })

#         mail.logout()
#         return reply_emails

#     except Exception as e:
#         print("Error fetching replies:", str(e))
#         return []

# def fetch_replies_from_gmail(username, password, subject_filter=None, since_days=30):
#     try:
#         # Connect to Gmail IMAP
#         mail = imaplib.IMAP4_SSL("imap.gmail.com")
#         mail.login(username, password)
#         mail.select("inbox")



#         print(subject_filter,"subject_filetr_fetch")
#         # Calculate since date
#         since_date = (datetime.date.today() - datetime.timedelta(days=since_days)).strftime("%d-%b-%Y")

#         # Search emails with subject or all if not given
#         search_criteria = f'(SINCE "{since_date}")'
#         if subject_filter:
#             search_criteria = f'(SUBJECT "{subject_filter}" SINCE "{since_date}")'
#             print(search_criteria,"search_criteria")

#         result, data = mail.search(None, search_criteria)
#         print(data,"search_criteria_data")
#         reply_emails = []

#         for num in data[0].split():
#             result, msg_data = mail.fetch(num, "(RFC822)")
#             raw_email = msg_data[0][1]
#             msg = email.message_from_bytes(raw_email)

#             # Decode subject
#             subject, encoding = decode_header(msg["Subject"])[0]
#             if isinstance(subject, bytes):
#                 subject = subject.decode(encoding if encoding else "utf-8")
#                 print(subject,"search_criteria_subject")

#             # Decode sender
#             from_ = msg.get("From")

#             # Get email body
#             body = ""
#             if msg.is_multipart():
#                 for part in msg.walk():
#                     if part.get_content_type() == "text/plain":
#                         charset = part.get_content_charset()
#                         body = part.get_payload(decode=True).decode(charset if charset else "utf-8")
#                         break
#             else:
#                 body = msg.get_payload(decode=True).decode()

#             reply_emails.append({
#                 "subject": subject,
#                 "from": from_,
#                 "body": body,
#                 "date": msg.get("Date"),
#             })

#         mail.logout()
#         return reply_emails
#     except Exception as e:
#         print("Error fetching replies:", str(e))
#         return []
