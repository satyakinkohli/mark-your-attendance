import sqlite3


def show_records(instructor_email):
    records = []
    conn = sqlite3.connect("attendance.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM class__list__mapping WHERE instructor_email=(?)",
        (instructor_email,),
    )
    for itemset in cur.fetchall():
        records.append(itemset)

    return records