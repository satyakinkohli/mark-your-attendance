from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import os
import config

from booking_class import duplicate_file, send_email, updating_sql_file
from marking_attendance import checkData
from instructor_records import show_records
from auth_decorator import login_required


UPLOAD_FOLDER = (
    "/Users/satyakinkohli/PycharmProjects/Online-Attendance-Project/Class_List"
)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["UPLOAD_EXTENSIONS"] = [".csv", ".txt"]
app.secret_key = config.APP_SECRET_KEY
app.config["SESSION_COOKIE_NAME"] = "google-login-session"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)


oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    client_kwargs={"scope": "openid email profile"},
)


db_name = "attendance.db"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_name
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)


class Class_List_Mapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input_file = db.Column(db.String(120), unique=False, nullable=False)
    class_code = db.Column(db.String(120), unique=True, nullable=False)
    output_file = db.Column(db.String(120), unique=True, nullable=False)
    instructor_email = db.Column(db.String(120), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@app.route("/login")
def login():
    google = oauth.create_client("google")
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    google = oauth.create_client("google")
    token = (
        google.authorize_access_token()
    )  # Access token from google (needed to get user info)
    resp = google.get(
        "userinfo", token=token
    )  # userinfo contains stuff you specificed in the scope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set your own data in the session not the profile from google
    session["profile"] = user_info
    session["email"] = user_info["email"]
    session["name"] = user_info["name"]
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    return redirect("/")


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")


@app.route("/")
def homepage():
    name = dict(session).get("name", None)
    return render_template("homepage.html", name=name)


@app.route("/bookClass", methods=["GET", "POST"])
@login_required
def book_class():
    name = dict(session).get("name", None)
    email = dict(session).get("email", None)
    if request.method == "POST":
        f = request.files["file"]
        file_ext = os.path.splitext(f.filename)[1]
        if f.filename != "":
            if file_ext not in app.config["UPLOAD_EXTENSIONS"]:
                return "Extension not accepted", 400
            else:
                f.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"], secure_filename(f.filename)
                    )
                )

        decided_random_code = updating_sql_file(f.filename, email)
        duplicate_file(f.filename, decided_random_code)
        send_email(f.filename, decided_random_code)

        return render_template("booking.html", name=name)
    else:
        return render_template("booking.html", name=name)


@app.route("/markAttendance", methods=["GET", "POST"])
def mark_attendance():
    name = dict(session).get("name", None)
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        otp = request.form.get("otp")
        class_code = request.form.get("class_code")
        attendance_verdict = checkData(class_code, otp, email)
        if attendance_verdict == "Correct OTP":
            return render_template("attendance.html", name=name)
        elif attendance_verdict == "Incorrect OTP":
            return "Incorrect OTP", 400
        elif attendance_verdict == "No such class code exists":
            return "No such class code exists", 400
        else:
            return "You're late!", 400
    else:
        return render_template("attendance.html", name=name)


@app.route("/myRecords", methods=["GET", "POST"])
def my_records():
    name = dict(session).get("name", None)
    instructor_email = dict(session).get("email", None)
    if request.method == "POST":
        return render_template("records.html", name=name)
    if request.method == "GET":
        record_rows = show_records(instructor_email)
        return render_template("records.html", name=name, record_rows=record_rows)


if __name__ == "__main__":
    app.run(debug=True)