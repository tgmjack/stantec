
from .data_handler import *
from stantec import settings as stg




############# registering user functions #############
def registration_code_entered(request):
    registration_code_entered = request.POST.get("registration_code_entered")
    existing_users = get_user_data()
    user = existing_users.filter(registration_code=registration_code_entered).first()
    if user is None:
        return redirect('/enter_registration_code_page?alert=invalid+registration+code')
    email_address = user.email_address
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


############### log in / log out functions ###############
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



##############  main pages  ################
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
        'cell_data': cell_data,
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
    logs = get_logs()

    logs_columns = ["log_id", "time", "user_email", "log_type", "log_message"]
    logs_cell_data = []
    for log in logs:
        logs_cell_data.append(
            {
                "log_id": log.log_id,
                "time": log.time,
                "user_email": log.user_email,
                "log_type": log.log_type,
                "log_message": log.log_message,
            }
        )

    context = {
        'user_email': user_email,
        'logs_columns': logs_columns,
        'logs_data': logs_cell_data,
    }

    if "tgmjackcroc@gmail.com" != user_email:
        return display_page(request, alert = "You must be logged in as an admin to access the admin page.")

    return render(request, 'home/admin_stuff.html' , context)
