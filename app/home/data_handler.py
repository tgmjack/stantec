import os
import pandas as pd
import psycopg2
import os
import pandas as pd
import psycopg2
import random
import string
import smtplib
from email.mime.text import MIMEText
import os
import pandas as pd
import psycopg2
from pathlib import Path
from django.shortcuts import render , redirect
from django.utils import timezone
from django.db import connection
import ssl
import bcrypt
from email.message import EmailMessage
from stantec import settings as stg
from .models import User, Log, Rainfall


def get_db_connection():


    host = os.getenv("DB_HOST") or getattr(stg, "DB_HOST", None) or "postgres"
    port = getattr(stg, "DB_PORT", None) or os.getenv("DB_PORT") or "5432"
    dbname = getattr(stg, "DB_NAME", None) or os.getenv("DB_NAME") or "stantec_db"
    user = getattr(stg, "DB_USER", None) or os.getenv("DB_USER") or "stantec_user"
    password = getattr(stg, "DB_PASSWORD", None) or os.getenv("DB_PASSWORD") or "stantec_password"

    if os.path.exists("/.dockerenv") and str(host).strip().lower() in {"localhost", "127.0.0.1", "::1"}:
        host = "postgres"

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )


def seperate_latitude_and_logitude_from_rest_of_df(df):
    
    latitude_and_longitude = {}
    for unique_value in df["location"].unique():
        latitude = df[df["location"] == unique_value]["latitude"].iloc[0]
        longitude = df[df["location"] == unique_value]["longitude"].iloc[0]
        latitude_and_longitude[unique_value] =[latitude, longitude]
    data_to_display = df.drop(columns=["latitude", "longitude"])

    return latitude_and_longitude, data_to_display
    

def use_local_data():
    import pandas as pd
    data_file = Path(stg.BASE_DIR) / 'home' / 'static' / 'Data2.csv'
    df = pd.read_csv(data_file)
    latitude_and_longitude, data_to_display = seperate_latitude_and_logitude_from_rest_of_df(df)
    return latitude_and_longitude, data_to_display

def get_data_from_local_sqlite_db():
    import sqlite3
    sqlite_file = Path(stg.BASE_DIR) / 'home' / 'data.db'
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data')
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    return columns, rows

def create_new_user(email_address, password , registered, registration_code):
    print(" qwertyu")
    print(email_address, password , registered, registration_code)

    User.objects.create(
        email_address=email_address,
        password=password,
        registered=registered,
        registration_code=registration_code,
    )



def get_data_from_postgres():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'rainfall'
                  AND column_name = 'time'
            )
            """
        )
        has_time_column = cursor.fetchone()[0]

    if has_time_column:
        queryset = Rainfall.objects.select_related("rainguage").order_by("id").values(
            "time",
            "rainfall",
            "rainguage__location",
            "rainguage__latitude",
            "rainguage__longitude",
        )
        rows = [
            {
                "time": row["time"],
                "Rainfall": row["rainfall"],
                "location": row["rainguage__location"],
                "latitude": row["rainguage__latitude"],
                "longitude": row["rainguage__longitude"],
            }
            for row in queryset
        ]
    else:
        queryset = Rainfall.objects.select_related("rainguage").order_by("id").values(
            "rainfall",
            "rainguage__location",
            "rainguage__latitude",
            "rainguage__longitude",
        )
        rows = [
            {
                "Rainfall": row["rainfall"],
                "location": row["rainguage__location"],
                "latitude": row["rainguage__latitude"],
                "longitude": row["rainguage__longitude"],
            }
            for row in queryset
        ]

    latitude_and_longitude = {}
    data_to_display = []
    for row in rows:
        location = row.get("location")
        if location not in latitude_and_longitude:
            latitude_and_longitude[location] = [row.get("latitude"), row.get("longitude")]

        data_to_display.append({k: v for k, v in row.items() if k not in {"latitude", "longitude"}})

    return latitude_and_longitude, data_to_display



def get_data():
    if stg.TESTING:
        latitude_and_longitude, data_to_display = use_local_data()
    elif stg.USE_LOCAL_SQLITE_DB:
        latitude_and_longitude, data_to_display = get_data_from_local_sqlite_db()
    elif stg.USE_POSTGRES_DB:
        latitude_and_longitude, data_to_display = get_data_from_postgres()
    else:
        raise Exception("no data chosen")

    if isinstance(data_to_display, list):
        columns = list(data_to_display[0].keys()) if data_to_display else []
    else:
        columns = list(data_to_display.columns)
    normalized_rows = []
    cell_data = []

    if isinstance(data_to_display, list):
        for row_object in data_to_display:
            ordered_row = [row_object.get(column) for column in columns]
            normalized_rows.append(ordered_row)
            cell_data.append({column: row_object.get(column) for column in columns})
    else:
        for row in data_to_display.itertuples(index=False):
            if isinstance(row, dict):
                ordered_row = [row.get(column) for column in columns]
                row_object = {column: row.get(column) for column in columns}
            else:
                ordered_row = list(row)
                row_object = {
                    column: ordered_row[index] if index < len(ordered_row) else None
                    for index, column in enumerate(columns)
                }

            normalized_rows.append(ordered_row)
            cell_data.append(row_object)


    return columns, normalized_rows, cell_data , latitude_and_longitude



def get_user_data():
    return User.objects.all()


def get_logs():
    return Log.objects.all().order_by("-time")


def check_if_password_is_correct_for_user(email, password, user_data):
    query = """
    SELECT * FROM "z-users"
    """

    user = user_data.filter(email_address=email).first()
    if user is None:
        create_new_log(email, "login", "user failed to log in with incorrect password")
        return False

    raw_hashed = user.password

    hashed_password_on_db = bytes.fromhex(raw_hashed[2:])
    
    if isinstance(password, str):
        password = password.encode("utf-8")

    if bcrypt.checkpw(password, hashed_password_on_db):
        print("it matches")
        create_new_log(email, "login", "user logged in successfully")
        return True
    else:
        print("It Does not Match :(")
    create_new_log(email, "login", "user failed to log in with incorrect password")
    return False

def create_new_log(user, log_type, log_message):

    if user is None:
        user = "not logged in"  

    Log.objects.create(
        time=timezone.now(),
        user_email=user,
        log_type=log_type,
        log_message=log_message,
    )



def hash_password(email, password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password

def password_is_acceptable(password):
    if len(password) < 8:
        return False
    return True

def generte_registration_code():
    code_length = 20
    characters = string.ascii_letters + string.digits
    registration_code = ''.join(random.choice(characters) for _ in range(code_length))
    return registration_code

def attempt_to_register_new_user(request):

    email_entered = request.GET.get("email")
    password_entered = request.GET.get("Password")
    if not email_entered or not password_entered:
        return redirect('/registration_page?alert=email+and+password+are+required')
    existing_users = get_user_data()
    if existing_users.filter(email_address=email_entered).exists():
        return redirect('/registration_page?alert=email+already+exists')
    if password_is_acceptable(password_entered) == False:
        return redirect('/registration_page?alert=password+must+be+at+least+8+characters+long')
    hashed_password = hash_password(email_entered, password_entered)
    registration_code = generte_registration_code()
    create_new_user(email_entered, hashed_password, False, registration_code)
    email_new_user_registration_code(email_entered, registration_code)
    return redirect('/enter_registration_code_page?alert=you+have+been+sent+a+registration+code+to+your+email')


def email_new_user_registration_code(email_entered, registration_code):
    
    EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM = os.getenv("EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM", "xxxx@encircle-marketing.com")
    EMAIL_PASSWORD_TO_SEND_REGISTRATION_CODES_FROM = os.getenv("EMAIL_PASSWORD_TO_SEND_REGISTRATION_CODES_FROM", "xxxxxxx")

    subject = "rainfall report registration"
    body = f"""
    Hello,
    Thank you for registering.
    Your registration code is: {registration_code}
    Please use it to complete your signup.
    Best regards,
    Jack Flavell 

    ps, hire me
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM
    msg["To"] = email_entered
    msg.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.office365.com", 587) as smtp:
        smtp.starttls(context=context)
        smtp.login(EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM, EMAIL_PASSWORD_TO_SEND_REGISTRATION_CODES_FROM)
        smtp.send_message(msg)
    print(f"Registration email sent to {email_entered} with code: {registration_code}")
    create_new_log(email_entered, "registration", "sent a registration email to "+email_entered+" with registration code "+registration_code+" from "+EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM)

def set_registered_to_true_for_this_user(email_address):
    User.objects.filter(email_address=email_address).update(registered=True)