import pandas as pd
import time
import datetime
import sqlite3


def checkData(class_code, otp, email):
    conn = sqlite3.connect("attendance.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT output_file FROM class__list__mapping WHERE class_code=(?)",
        (class_code,),
    )
    for name_of_file in cur.fetchall():
        filename = name_of_file[0]

    if filename != "":
        df = pd.read_csv(
            "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
            + filename
        )
        check_otp = (df.loc[df["Email ID"] == email]["OTP"]).iloc[0]
        check_time_str = (df.loc[df["Email ID"] == email]["End Time"]).iloc[0]
        check_time = datetime.datetime.strptime(check_time_str, "%Y-%m-%d %H:%M:%S.%f")
        entry_time = datetime.datetime.now()

        if int(check_otp) == int(otp):
            if entry_time <= check_time:
                df.loc[df["Email ID"] == email, "P/A"] = "P"
                df.to_csv(
                    "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List/"
                    + filename,
                    index=False,
                )
                return "Correct OTP"
            else:
                return "You're late"
        else:
            return "Incorrect OTP"
    else:
        return "No such class code exists"
