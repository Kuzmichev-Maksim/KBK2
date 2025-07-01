from django.contrib import admin
from django.urls import path
from stats.views import *
from django.views.decorators.csrf import csrf_exempt
from django_prometheus import exports


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_view, name='login_page'),
    path('dashboard/', employee_view, name='employee'),
    path('employees/import/', employee_import, name='employee_import'),
    path('logout/', logout_view, name='logout_page'),
    path('history/', history, name='history'),
    path('expenses/', expenses, name='expenses'),
    path('expenses/ajax/', expenses_ajax, name='expenses_ajax'),
    path('expenses/import/', expenses_import, name='expenses_import'),
    path('data/', data_view, name='data'),
    path('numbers/', numbers_view, name="numbers"),
    path('numbers/import/', import_numbers, name='import_numbers'),
    path('issue_phone/', issue_phone_view, name='issue_phone'),
    path('return_phone/', return_phone_view, name="return_phone"),
    path('transfer/', transfer_phone_view, name='transfer_phone'),
    path('phone_history/<int:phone_id>/', phone_history_view, name='phone_history'),
    path('metrics/', csrf_exempt(exports.ExportToDjangoView), name='prometheus-django-metrics'),
    path('metrics', csrf_exempt(exports.ExportToDjangoView), name='prometheus-django-metrics-no-slash'),
    path('users/', users_view, name='users'),

    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('api/expense-stats/', ExpenseStatsAPIView.as_view(), name='expense-stats'),
    path('api/profile/', ProfileAPIView.as_view(), name='profile'),
    path('api/logout/', LogoutAPIView.as_view(), name='logout'),
]