"""
URL configuration for stantec project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from home import views

urlpatterns = [

        path('' , views.display_page , name = 'display_page'),
        path('about_us' , views.about_us , name = 'about_us'),
        path('admin_stuff' , views.admin_stuff , name = 'admin_stuff'),
        path('login_page' , views.login_page , name = 'login_page'),
        path('login_button_clicked' , views.login_button_clicked , name = 'login_button_clicked'),
        path('logout' , views.logout , name = 'logout'),
        path('registration_page' , views.registration_page , name = 'registration_page'),
        path('attempt_to_register_new_user' , views.attempt_to_register_new_user , name = 'attempt_to_register_new_user'),
        path('enter_registration_code_page' , views.enter_registration_code_page , name = 'enter_registration_code_page'),
        path('registration_code_entered' , views.registration_code_entered , name = 'registration_code_entered'),
]
