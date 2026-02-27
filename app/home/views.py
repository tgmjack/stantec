import os
import sys
from .data_handler import *
from stantec import settings as stg
from pathlib import Path

from dotenv import load_dotenv



env_path = Path(__file__).resolve().parent.parent / '.env'
if sys.platform.startswith("linux") and env_path.exists():
    load_dotenv(env_path)





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
