import os
import sys
from django.shortcuts import render , redirect
from stantec import settings as stg
from pathlib import Path
import ssl
import bcrypt
from email.message import EmailMessage
from dotenv import load_dotenv



env_path = Path(__file__).resolve().parent.parent / '.env'
if sys.platform.startswith("linux") and env_path.exists():
    load_dotenv(env_path)
# Create your views here.


def get_db_connection():
    import psycopg2

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
    import os
    import pandas as pd
    import psycopg2

    connection = get_db_connection()

    print(" qwertyu")
    print(email_address, password , registered, registration_code)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                insert into users (email_address, password, registered, registration_code) values (%s, %s, %s, %s)
                """,
                (email_address, password, registered, registration_code)
            )



def get_data_from_postgres():
    import os
    import pandas as pd
    import psycopg2

    connection = get_db_connection()

    with connection:
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
                cursor.execute(
                    """
                    SELECT rf.time, rf.rainfall AS \"Rainfall\", rg.location, rg.latitude, rg.longitude
                    FROM rainfall rf
                    JOIN rainguage rg ON rg.id = rf.rainguage_id
                    ORDER BY rf.id
                    """
                )
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=["time", "Rainfall", "location", "latitude", "longitude"])
            else:
                cursor.execute(
                    """
                    SELECT rf.rainfall AS \"Rainfall\", rg.location, rg.latitude, rg.longitude
                    FROM rainfall rf
                    JOIN rainguage rg ON rg.id = rf.rainguage_id
                    ORDER BY rf.id
                    """
                )
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=["Rainfall", "location", "latitude", "longitude"])

    latitude_and_longitude, data_to_display = seperate_latitude_and_logitude_from_rest_of_df(df)
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

    columns = list(data_to_display.columns)
    normalized_rows = []
    cell_data = []

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

    import os
    import pandas as pd
    import psycopg2

    connection = get_db_connection()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM users
                """
            )
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=["user_id", "email_address", "password", "registered", "registration_code"])

    return df


def get_logs():
            

    import os
    import pandas as pd
    import psycopg2


    connection = get_db_connection()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM logs
                """
            )
            rows = cursor.fetchall()
            print(rows)
            df = pd.DataFrame(rows, columns=["log_id", "time"  , "user_email", "log_type", "log_message"])

    return df


def check_if_password_is_correct_for_user(email, password, user_data):
    query = """
    SELECT * FROM "z-users"
    """
    print("###################################")
    print(user_data)
    for index, row in user_data.iterrows():
        print("checking row:", row["email_address"])
        print("against email:", email)
        if email == row["email_address"]:  # Use equality for safety
            raw_hashed = row["password"]  # This is a hex string like '\\x243262...'

            # Convert PostgreSQL bytea hex string to actual bytes
            if raw_hashed.startswith("\\x"):  # Python string representation of bytea
                raw_hashed = raw_hashed[2:]  # Strip '\\x'
            hashed_password_on_db = bytes.fromhex(raw_hashed)

            # Make sure the password is bytes
            if isinstance(password, str):
                password = password.encode("utf-8")

            if bcrypt.checkpw(password, hashed_password_on_db):
                print("It Matches!")
                create_new_log(email, "login", "user logged in successfully")
                return True
            else:
                print("It Does not Match :(")
    create_new_log(email, "login", "user failed to log in with incorrect password")
    return False

def create_new_log(user, log_type, log_message):
    # Ensure `user` is never None when inserted into a NOT NULL column.
    # Use an empty string or a placeholder for anonymous access.
    if user is None:
        user = "not logged in"  # could also be "anonymous" or similar

    import os
    import pandas as pd
    import psycopg2

    query = """ insert into logs (time, user_email, log_type, log_message) values (CURRENT_TIMESTAMP, %s, %s, %s) """
    connection = get_db_connection()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (user, log_type, log_message))



def hash_password(email, password):
    salt = bcrypt.gensalt()
    print("password   hhhhhhhhhhhhhhhhhh")
    print(password)
    hashed_password = bcrypt.hashpw(password.encode(), salt)
#    save_hash_key(email, salt)  # Save the salt (not the full hash)
    return hashed_password

def password_is_acceptable(password):
    if len(password) < 8:
        return False
    return True

def generte_registration_code():
    import random
    import string

    code_length = 20
    characters = string.ascii_letters + string.digits
    registration_code = ''.join(random.choice(characters) for _ in range(code_length))
    return registration_code

def attempt_to_register_new_user(request):
    print(request)
    email_entered = request.GET.get("email")
    password_entered = request.GET.get("Password")

    if not email_entered or not password_entered:
        return redirect('/registration_page?alert=email+and+password+are+required')

    existing_users = get_user_data()

    if email_entered in existing_users["email_address"].values:
        return redirect('/registration_page?alert=email+already+exists')
    
    if password_is_acceptable(password_entered) == False:
        return redirect('/registration_page?alert=password+must+be+at+least+8+characters+long')

    hashed_password = hash_password(email_entered, password_entered)

    registration_code = generte_registration_code()

    create_new_user(email_entered, hashed_password, False, registration_code)

    email_new_user_registration_code(email_entered, registration_code)


    return redirect('/enter_registration_code_page?alert=you+have+been+sent+a+registration+code+to+your+email')


def email_new_user_registration_code(email_entered, registration_code):
    import smtplib
    from email.mime.text import MIMEText

    EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM = os.getenv("EMAIL_ADDRESS_TO_SEND_REGISTRATION_CODES_FROM", "Jack@encircle-marketing.com")
    EMAIL_PASSWORD_TO_SEND_REGISTRATION_CODES_FROM = os.getenv("EMAIL_PASSWORD_TO_SEND_REGISTRATION_CODES_FROM", "Crocodile1in*")

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
    import os
    import pandas as pd
    import psycopg2

    connection = get_db_connection()

    cursor = connection.cursor()

    update_query = """
        UPDATE users 
        SET registered = TRUE 
        WHERE email_address = %s
    """
    cursor.execute(update_query, (email_address,))
    connection.commit()









































            



















def registration_code_entered(request):

    registration_code_entered = request.POST.get("registration_code_entered")

    existing_users = get_user_data()

    print(request)
    print(" ############################################################################## ")
    print("registration_code_entered:", registration_code_entered)
    print('existing_users["registration_code"]      ' , existing_users["registration_code"])

    user_row = existing_users[existing_users["registration_code"] == registration_code_entered]

    if user_row.empty:
        return redirect('/enter_registration_code_page?alert=invalid+registration+code')

    email_address = user_row["email_address"].iloc[0]

    set_registered_to_true_for_this_user(email_address)

    return redirect('/login_page?alert=registration+complete+please+log+in')


def enter_registration_code_page(request):
    alert = request.GET.get('alert', '')
    context = {'alert': alert}
    return render(request, 'home/enter_registration_code_page.html' , context)


def registration_page(request):
    alert = request.GET.get('alert', '')
    context = {'alert': alert}
    return render(request, 'home/registration_page.html' , context)

def logout(request):
    request.session.flush()
    return redirect('/')


def login_page(request):
    alert = request.GET.get('alert', '')
    context = {'alert': alert}
    return render(request, 'home/login_page.html' , context)

def login_button_clicked(request):
    print("request login clicked ")
    print(request)
    existing_users = get_user_data()

    password_entered = request.POST.get("password")
    email_entered = request.POST.get("email")

    if check_if_password_is_correct_for_user(email_entered, password_entered, existing_users):
        request.session['user_email'] = email_entered
        return redirect('/')
    else:
        return redirect('/login_page?alert=email+or+password+are+wrong')

    pass


def display_page(request , alert = None):

    user_email = request.session.get('user_email')
    create_new_log(user_email, "display_page", "accessed displayed page")
    columns, rows, cell_data , latitude_and_longitude = get_data()
    
    title = 'think of a clever title'
   
    default_latitude = latitude_and_longitude["central Birmingham"][0] 
    default_longitude = latitude_and_longitude["central Birmingham"][1]

    print("user_email:", user_email)
    context = {

        'user_email': user_email,
        'title': title,
        'columns': columns,
#        'rows': rows,
        'cell_data': cell_data,
#        'type_of_table_to_display': type_of_table_to_display,
        'latitude_and_longitude': latitude_and_longitude,
        'default_latitude': default_latitude,
        'default_longitude': default_longitude,
        'ag_grid_enterprise_key': getattr(stg, 'AG_GRID_ENTERPRISE_KEY', '')
    }
    if alert is not None:
        context['alert'] = alert

    return render(request, 'home/index.html' , context)


def about_us(request):
    user_email = request.session.get('user_email')
    create_new_log(user_email, "about_us", "accessed about us page")
    context = {
        'user_email': user_email,
    }

    return render(request, 'home/about_us.html' , context)

def admin_stuff(request):
    user_email = request.session.get('user_email')
    create_new_log(user_email, "admin access", "accessed admin page")
    logs_df = get_logs()

    # Format logs data like cell_data for the table
    logs_columns = list(logs_df.columns)
    logs_cell_data = []
    for index, row in logs_df.iterrows():
        row_object = {col: row[col] for col in logs_columns}
        logs_cell_data.append(row_object)

    context = {
        'user_email': user_email,
        'logs_columns': logs_columns,
        'logs_data': logs_cell_data,
    }

    if "tgmjackcroc@gmail.com" != user_email:
        return display_page(request, alert = "You must be logged in as an admin to access the admin page.")

    return render(request, 'home/admin_stuff.html' , context)
