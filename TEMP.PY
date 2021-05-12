from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import numpy as np
import config
import csv
import random
import string
import smtplib
import time
import datetime
import sqlite3


def generateString():
    S = 10
    random_string = "".join(random.choices(string.ascii_uppercase + string.digits, k=S))
    return random_string


def updating_sql_file(filename, email):
    conn = sqlite3.connect("attendance.db")
    cur = conn.cursor()
    while True:
        try:
            random_code = generateString()
            cur.execute(
                "INSERT INTO class__list__mapping (input_file, class_code, output_file, instructor_email, date_added) "
                "values (?, ?, ?, ?, ?)",
                (
                    filename,
                    random_code,
                    random_code + "-" + filename,
                    email,
                    (datetime.datetime.now()).strftime("%d %b, %Y at %H:%M:%S"),
                ),
            )
            break
        except:
            pass
    conn.commit()
    conn.close()

    return random_code


def generateOTP():
    otp = str(random.randint(1, 999999)).zfill(6)
    return otp


def add_otp_to_file(filename, decided_random_code):
    with open(
        "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
        + filename,
        "r",
    ) as csvinput:
        with open(
            "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
            + decided_random_code
            + "-"
            + filename,
            "w",
        ) as csvoutput:
            writer = csv.writer(csvoutput, lineterminator="\n")
            reader = csv.reader(csvinput)

            all = []
            row = next(reader)
            row.append("OTP")
            row.append("Start Time")
            row.append("End Time")
            row.append("P/A")
            all.append(row)

            for row in reader:
                row.append(generateOTP())
                row.append("0")
                row.append("0")
                row.append("A")
                all.append(row)

            writer.writerows(all)


def add_time_to_file(filename, decided_random_code, row, start_time, end_time):
    df = pd.read_csv(
        "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
        + decided_random_code
        + "-"
        + filename
    )
    df.at[row, "Start Time"] = start_time
    df.at[row, "End Time"] = end_time
    df.to_csv(
        "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
        + decided_random_code
        + "-"
        + filename,
        index=False,
    )


def contact_data(filename, decided_random_code):
    names = []
    emails = []
    otps = []
    with open(
        "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
        + decided_random_code
        + "-"
        + filename,
        mode="r",
    ) as contacts_file:
        next(contacts_file)
        for a_contact in contacts_file:
            names.append(a_contact.split(",")[1])
            emails.append(a_contact.split(",")[2])
            otps.append(a_contact.split(",")[3])

    return names, emails, otps


def message_content(filename):
    with open(filename, "r") as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def host_email_login():
    s = smtplib.SMTP(host="smtp.gmail.com", port=587)
    s.starttls()
    MY_ADDRESS = config.MY_ADDRESS
    PASSWORD = config.PASSWORD
    s.login(MY_ADDRESS, PASSWORD)
    return s


def send_email(filename, decided_random_code):
    names, emails, otps = contact_data(filename, decided_random_code)
    email_message_content = message_content("email_template.txt")
    row = 0

    for name, email, otp in zip(names, emails, otps):
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(minutes=10)
        msg = MIMEMultipart()
        message = email_message_content.substitute(PERSON_NAME=name.title())
        otp = otp.replace("\n", "")
        message = message.replace("PERSON_OTP", otp)
        message = message.replace(
            "PERSON_START_TIME", start_time.time().strftime("%H:%M:%S")
        )
        message = message.replace(
            "PERSON_END_TIME", end_time.time().strftime("%H:%M:%S")
        )
        message = message.replace("CLASS_CODE", decided_random_code)

        msg["From"] = config.MY_ADDRESS
        msg["To"] = email
        msg["Subject"] = "Mark your attendance"
        msg.attach(MIMEText(message, "plain"))

        host_email_login().send_message(msg)
        add_time_to_file(filename, decided_random_code, row, start_time, end_time)
        del msg
        time.sleep(120)
        row += 1
