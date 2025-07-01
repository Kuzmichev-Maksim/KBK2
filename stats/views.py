import datetime
import csv
import io
import logging
import traceback
import hashlib
from io import TextIOWrapper
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import *
from django.db.models import Sum
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.permissions import AllowAny


logger = logging.getLogger(__name__)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        login_str = request.data.get('login')
        password = request.data.get('password')

        if not login_str or not password:
            return Response({'success': False, 'message': 'Логин и пароль обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        login_hash = hashlib.sha256(login_str.encode('utf-8')).hexdigest()
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        try:
            user = User.objects.get(login_hash=login_hash)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({'success': False, 'message': 'Неверный пароль'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.role.name != "Пользователь":
            logger.warning(
                f"Роль пользователя {user.id} не соответствует: {user.role.name}")
            return Response({'success': False, 'message': 'Доступ запрещён: только для пользователей с ролью "Пользователь"'}, status=status.HTTP_403_FORBIDDEN)

        try:
            employee = user.employee
        except Employee.DoesNotExist:
            return Response({'success': False, 'message': 'Сотрудник не найден для данного пользователя'}, status=status.HTTP_404_NOT_FOUND)

        request.session['user_id'] = user.id
        request.session.modified = True
        logger.info(f"Пользователь {user.id} вошёл в систему через сессию")

        profile_data = {
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'middle_name': employee.middle_name or '',
            'role': user.role.name,
            'company': employee.company.name,
            'department': employee.department.name,
            'position': employee.position.name,
            'city': employee.city,
            'personnel_number': employee.personnel_number,
            'status': 'Активен' if employee.status else 'Неактивен',
            'phone_numbers': [epn.phone_number.number for epn in employee.phone_numbers.all()]
        }

        employee_phone_numbers = employee.phone_numbers.all()
        phone_numbers = PhoneNumber.objects.filter(
            employee_number__in=employee_phone_numbers)

        expenses = Expense.objects.filter(phone_number__in=phone_numbers)
        expense_data = [
            {
                'phone_number': expense.phone_number.number,
                'usage_period': expense.usage_period.strftime('%Y-%m-%d'),
                'amount': float(expense.amount),
                'status': expense.status,
                'tariff': expense.phone_number.tariff.name,
                'operator': expense.phone_number.tariff.operator.name if expense.phone_number.tariff.operator else '',
                'limit': float(expense.phone_number.employee_number.employee.position.salary_limit) if expense.phone_number.employee_number else 0.0,
            }
            for expense in expenses
        ]

        return Response({
            'success': True,
            'user_id': user.id,
            'role': user.role.name,
            'profile': profile_data,
            'expenses': expense_data
        }, status=status.HTTP_200_OK)


class ExpenseStatsAPIView(APIView):
    def get(self, request):
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                return Response({
                    'success': False,
                    'message': 'Необходимо авторизоваться'
                }, status=status.HTTP_401_UNAUTHORIZED)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Пользователь не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            try:
                employee = user.employee
            except Employee.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Сотрудник не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            logger.info(
                f"Запрос статистики расходов для пользователя {user.id}")

            employee_phone_numbers = employee.phone_numbers.all()
            phone_numbers = PhoneNumber.objects.filter(
                employee_number__in=employee_phone_numbers)
            expenses = Expense.objects.filter(phone_number__in=phone_numbers)

            expense_data = [
                {
                    'phone_number': expense.phone_number.number,
                    'usage_period': expense.usage_period.strftime('%Y-%m-%d'),
                    'amount': float(expense.amount),
                    'status': expense.status,
                    'tariff': expense.phone_number.tariff.name,
                    'operator': expense.phone_number.tariff.operator.name if expense.phone_number.tariff.operator else '',
                    'limit': float(expense.phone_number.employee_number.employee.position.salary_limit) if expense.phone_number.employee_number else 0.0,
                }
                for expense in expenses
            ]

            return Response({
                'success': True,
                'data': expense_data,
                'message': 'Статистика расходов успешно получена'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Ошибка при получении статистики расходов: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка при получении статистики: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileAPIView(APIView):
    def get(self, request):
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                return Response({
                    'success': False,
                    'message': 'Необходимо авторизоваться'
                }, status=status.HTTP_401_UNAUTHORIZED)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Пользователь не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            try:
                employee = user.employee
            except Employee.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Сотрудник не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            logger.info(f"Запрос данных профиля для пользователя {user.id}")

            profile_data = {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'middle_name': employee.middle_name or '',
                'role': user.role.name,
                'company': employee.company.name,
                'department': employee.department.name,
                'position': employee.position.name,
                'city': employee.city,
                'personnel_number': employee.personnel_number,
                'status': 'Активен' if employee.status else 'Неактивен',
                'phone_numbers': [epn.phone_number.number for epn in employee.phone_numbers.all()]
            }

            return Response({
                'success': True,
                'data': profile_data,
                'message': 'Данные профиля успешно получены'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Ошибка при получении данных профиля: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка при получении профиля: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            if 'user_id' in request.session:
                user_id = request.session['user_id']
                del request.session['user_id']
                request.session.modified = True
                logger.info(f"Пользователь {user_id} вышел из системы")
            return Response({
                'success': True,
                'message': 'Выход из системы выполнен успешно'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Ошибка при выходе из системы: {str(e)}")
            return Response({
                'success': False,
                'message': f'Ошибка при выходе: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, "Необходимо авторизоваться")
            return redirect('login')

        user_role = request.session.get('role')
        if user_role != "Администратор":
            messages.error(request, "Доступ разрешён только администраторам")
            request.session.flush()
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.method == "POST":
        login = request.POST.get("login")
        password = request.POST.get("password")

        if not login or not password:
            messages.error(request, "Введите логин и пароль")
            return render(request, "login.html")

        login = login.strip()
        password = password.strip()

        logger.info(f"Попытка авторизации с логином: {login}")

        login_hash = hashlib.sha256(login.encode('utf-8')).hexdigest()
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        logger.info(f"Сгенерированный login_hash: {login_hash}")
        logger.info(f"Сгенерированный password_hash: {password_hash}")

        try:
            user = User.objects.get(login_hash=login_hash)
            logger.info(
                f"Пользователь найден: ID={user.id}, Role={user.role.name}")
        except User.DoesNotExist:
            logger.error("Пользователь с таким логином не найден")
            messages.error(request, "Неверный логин или пароль")
            return render(request, "login.html")

        if user.check_password(password):
            if user.role.name != "Администратор":
                messages.error(
                    request, "Доступ разрешён только администраторам")
                return render(request, "login.html")

            request.session['user_id'] = user.id
            request.session['role'] = user.role.name
            logger.info(f"Пользователь с ID {user.id} успешно авторизован")
            return redirect('employee')
        else:
            logger.error("Неверный пароль")
            messages.error(request, "Неверный логин или пароль")
            return render(request, "login.html")

    if request.session.get('user_id'):
        return redirect('employee')
    return render(request, "login.html")


def logout_view(request):
    request.session.flush()
    logger.info("Пользователь вышел из системы")
    return render(request, "login.html")


@login_required_custom
def history(request):
    if request.method == "POST":
        history_id = request.POST.get("history_id")
        if history_id:
            comment = request.POST.get(f"comment_{history_id}")
            if comment is not None:
                history = get_object_or_404(PhoneNumberHistory, id=history_id)
                history.comment = comment
                history.save()
                logger.info(
                    f"Комментарий для истории номера ID {history_id} обновлён: {comment}")
                return HttpResponseRedirect(reverse("history") + "?tab=phone-numbers-tab")

        employee_history_id = request.POST.get("employee_history_id")
        if employee_history_id:
            comment = request.POST.get(
                f"employee_comment_{employee_history_id}")
            if comment is not None:
                history = get_object_or_404(
                    EmployeeHistory, id=employee_history_id)
                history.comment = comment
                history.save()
                logger.info(
                    f"Комментарий для истории сотрудника ID {employee_history_id} обновлён: {comment}")
                return HttpResponseRedirect(reverse("history") + "?tab=employee-history-tab")

        active_tab = request.POST.get("active_tab", "phone-numbers-tab")
        return HttpResponseRedirect(reverse("history") + f"?tab={active_tab}")

    histories = PhoneNumberHistory.objects.select_related(
        'phone_number', 'employee', 'employee__company'
    ).order_by('phone_number__number', 'start_date')
    grouped_histories = {}
    for history in histories:
        phone_number = history.phone_number.number
        employee = history.employee
        employee_info = f"{employee.last_name} {employee.first_name} {employee.middle_name or ''} (Таб. № {employee.personnel_number})"
        company_name = employee.company.name if employee.company else '-'

        if phone_number not in grouped_histories:
            grouped_histories[phone_number] = []
        grouped_histories[phone_number].append({
            "id": history.id,
            "employee_info": employee_info,
            "start_date": history.start_date,
            "end_date": history.end_date,
            "comment": history.comment or '-',
            "company": company_name
        })

    employee_histories = EmployeeHistory.objects.filter(employee__status=False).select_related(
        'employee', 'employee__company', 'employee__position', 'employee__department'
    ).order_by('employee__last_name', 'deletion_date')
    grouped_employee_histories = {}
    for history in employee_histories:
        employee = history.employee
        employee_info = f"{employee.last_name} {employee.first_name} {employee.middle_name or ''} (Таб. № {employee.personnel_number})"

        if employee_info not in grouped_employee_histories:
            grouped_employee_histories[employee_info] = []
        grouped_employee_histories[employee_info].append({
            "id": history.id,
            "deletion_date": history.deletion_date,
            "comment": history.comment or '-',
            "company": history.company if hasattr(history, 'company') else employee.company.name,
            "city": history.city if hasattr(history, 'city') else employee.city,
            "position": history.position if hasattr(history, 'position') else employee.position.name,
            "department": history.department if hasattr(history, 'department') else employee.department.name
        })

    companies = Company.objects.all().order_by('name')

    return render(request, 'history.html', {
        'grouped_histories': grouped_histories,
        'grouped_employee_histories': grouped_employee_histories,
        'companies': companies
    })


@login_required_custom
def employee_view(request):
    if request.method == "POST":
        logger.info("Получен POST-запрос: %s", request.POST)

        if 'check_unique' in request.POST:
            last_name = request.POST.get('new_employee_last_name')
            first_name = request.POST.get('new_employee_first_name')
            middle_name = request.POST.get('new_employee_middle_name', '')
            personnel_number = request.POST.get(
                'new_employee_personnel_number')
            city = request.POST.get('new_employee_city')
            company_id = request.POST.get('new_employee_company')
            position_id = request.POST.get('new_employee_position')
            department_id = request.POST.get('new_employee_department')

            exists = Employee.objects.filter(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                personnel_number=personnel_number,
                city=city,
                company_id=company_id,
                position_id=position_id,
                department_id=department_id,
                status=True
            ).exists()
            logger.info("Проверка уникальности: %s", exists)
            return JsonResponse({'exists': exists})

        elif 'add_employee' in request.POST:
            last_name = request.POST.get("new_employee_last_name")
            first_name = request.POST.get("new_employee_first_name")
            middle_name = request.POST.get("new_employee_middle_name", '')
            personnel_number = request.POST.get(
                "new_employee_personnel_number")
            city = request.POST.get("new_employee_city")
            company_id = request.POST.get("new_employee_company")
            position_id = request.POST.get("new_employee_position")
            department_id = request.POST.get("new_employee_department")

            logger.info("Добавление сотрудника: %s %s %s",
                        last_name, first_name, personnel_number)

            if all([last_name, first_name, personnel_number, city, company_id, position_id, department_id]):
                try:
                    if Employee.objects.filter(personnel_number=personnel_number, status=True).exists():
                        logger.warning(
                            "Табельный номер %s уже используется другим активным сотрудником", personnel_number)
                        return JsonResponse({'error': 'Табельный номер уже используется другим активным сотрудником'})

                    company = get_object_or_404(Company, id=company_id)
                    position = get_object_or_404(Position, id=position_id)
                    department = get_object_or_404(
                        Department, id=department_id)
                    employee = Employee.objects.create(
                        last_name=last_name,
                        first_name=first_name,
                        middle_name=middle_name,
                        personnel_number=personnel_number,
                        city=city,
                        company=company,
                        position=position,
                        department=department,
                    )
                    logger.info(
                        "Сотрудник успешно добавлен с ID: %s", employee.id)
                    return JsonResponse({'success': True})
                except Exception as e:
                    logger.error("Ошибка при добавлении: %s", str(e))
                    return JsonResponse({'error': f'Ошибка: {str(e)}'})
            else:
                return JsonResponse({'error': 'Все поля должны быть заполнены'})

        elif "update_employee" in request.POST:
            employee_id = request.POST.get("update_employee")
            employee = get_object_or_404(Employee, id=employee_id)
            new_personnel_number = request.POST.get(
                "employee_personnel_number")

            if Employee.objects.filter(personnel_number=new_personnel_number, status=True).exclude(id=employee_id).exists():
                logger.warning(
                    "Табельный номер %s уже используется другим сотрудником", new_personnel_number)
                return JsonResponse({'error': 'Табельный номер уже используется другим сотрудником'})

            try:
                employee.last_name = request.POST.get("employee_last_name")
                employee.first_name = request.POST.get("employee_first_name")
                employee.middle_name = request.POST.get(
                    "employee_middle_name", '')
                employee.personnel_number = new_personnel_number
                employee.city = request.POST.get("employee_city")
                employee.company = get_object_or_404(
                    Company, id=request.POST.get("employee_company"))
                employee.position = get_object_or_404(
                    Position, id=request.POST.get("employee_position"))
                employee.department = get_object_or_404(
                    Department, id=request.POST.get("employee_department"))
                employee.save()
                logger.info("Сотрудник обновлен: %s", employee_id)
                return JsonResponse({'success': True})
            except IntegrityError as e:
                logger.error("Ошибка целостности при обновлении: %s", str(e))
                return JsonResponse({'error': 'Табельный номер уже используется другим сотрудником'})
            except Exception as e:
                logger.error("Ошибка при обновлении: %s", str(e))
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

        elif "delete_employee" in request.POST:
            employee_id = request.POST.get("delete_employee")
            comment = request.POST.get("comment", "Сотрудник удален")
            employee = get_object_or_404(Employee, id=employee_id)
            logger.info(
                "Попытка изменения статуса сотрудника ID: %s с комментарием: %s", employee_id, comment)
            try:
                with transaction.atomic():
                    employee_phones = EmployeePhoneNumber.objects.filter(
                        employee=employee)
                    logger.info("Найдено %d номеров для освобождения",
                                employee_phones.count())
                    for emp_phone in employee_phones:
                        phone = emp_phone.phone_number
                        phone.status = "свободен"
                        phone.save()

                        history_entry = PhoneNumberHistory.objects.filter(
                            phone_number=phone,
                            employee=employee,
                            end_date__isnull=True
                        ).last()
                        if history_entry:
                            history_entry.end_date = timezone.now().date()
                            history_entry.comment = comment
                            history_entry.save()
                            logger.info(
                                "Обновлена история номера %s", phone.number)

                        emp_phone.delete()

                    history_entry = EmployeeHistory.objects.create(
                        employee=employee,
                        deletion_date=timezone.now().date(),
                        comment=comment
                    )
                    logger.info(
                        "Создана запись в EmployeeHistory с ID: %s", history_entry.id)

                    employee.status = False
                    employee.save()
                    logger.info(
                        "Статус сотрудника изменен на False: %s", employee_id)
                    return JsonResponse({'success': True})
            except Exception as e:
                logger.error(
                    "Ошибка при изменении статуса сотрудника: %s", str(e), exc_info=True)
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

    employees = Employee.objects.filter(status=True)
    companies = Company.objects.all()
    positions = Position.objects.all()
    departments = Department.objects.all()

    return render(request, "home.html", {
        "employees": employees,
        "companies": companies,
        "positions": positions,
        "departments": departments,
    })


@csrf_exempt
def employee_import(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return JsonResponse({'success': False, 'message': 'Файл CSV не предоставлен'})

        try:
            # Читаем CSV файл
            csv_data = csv_file.read().decode('utf-8')
            csv_io = io.StringIO(csv_data)
            reader = csv.DictReader(csv_io)

            # Проверяем наличие необходимых столбцов
            required_columns = ['ФИО', 'Таб. номер',
                                'Город', 'Компания', 'Должность', 'Отдел']
            if not all(col in reader.fieldnames for col in required_columns):
                return JsonResponse({'success': False, 'message': 'Некорректный формат CSV. Требуются столбцы: ФИО, Таб. номер, Город, Компания, Должность, Отдел'})

            errors = []
            # start=2 для учета заголовка
            for row_num, row in enumerate(reader, start=2):
                # Разделяем ФИО
                fio = row['ФИО'].strip().split()
                if len(fio) < 2 or len(fio) > 3:
                    errors.append(
                        f"Строка {row_num}: Неверный формат ФИО. Ожидается 'Фамилия Имя' или 'Фамилия Имя Отчество'")
                    continue

                last_name = fio[0]
                first_name = fio[1]
                middle_name = fio[2] if len(fio) == 3 else ''

                personnel_number = row['Таб. номер'].strip()
                city = row['Город'].strip()
                company_name = row['Компания'].strip()
                position_name = row['Должность'].strip()
                department_name = row['Отдел'].strip()

                # Валидация данных
                if not all([last_name, first_name, personnel_number, city, company_name, position_name, department_name]):
                    errors.append(
                        f"Строка {row_num}: Все поля, кроме отчества, должны быть заполнены")
                    continue

                if not (last_name.isalpha() and first_name.isalpha() and (not middle_name or middle_name.isalpha())):
                    errors.append(
                        f"Строка {row_num}: ФИО должно содержать только буквы")
                    continue

                if not personnel_number.isdigit():
                    errors.append(
                        f"Строка {row_num}: Табельный номер должен содержать только цифры")
                    continue

                # Проверка уникальности по personnel_number
                if Employee.objects.filter(personnel_number=personnel_number, status=True).exists():
                    errors.append(
                        f"Строка {row_num}: Сотрудник с таб. номером {personnel_number} уже существует")
                    continue

                # Обработка компании
                company, created = Company.objects.get_or_create(
                    name=company_name,
                    # Значения по умолчанию
                    defaults={'kpp': None, 'inn': None}
                )

                # Обработка должности
                position, created = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'salary_limit': 0.00}  # Значение по умолчанию
                )

                # Обработка отдела
                department, created = Department.objects.get_or_create(
                    name=department_name
                )

                # Создание сотрудника
                Employee.objects.create(
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    personnel_number=personnel_number,
                    city=city,
                    company=company,
                    position=position,
                    department=department,
                    status=True
                )

            if errors:
                return JsonResponse({'success': False, 'message': '<br>'.join(errors)})
            return JsonResponse({'success': True, 'message': 'Сотрудники успешно импортированы'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка при импорте: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Недопустимый метод запроса'})


@login_required_custom
def data_view(request):
    if request.method == "POST":
        active_tab = request.POST.get("active_tab", "companies-tab")

        if "add_company" in request.POST:
            name = request.POST.get("new_company_name")
            kpp = request.POST.get("new_company_kpp")
            inn = request.POST.get("new_company_inn")
            if name and kpp and inn:
                if not Company.objects.filter(kpp=kpp).exists() and not Company.objects.filter(inn=inn).exists():
                    Company.objects.create(name=name, kpp=kpp, inn=inn)
        elif "update_company" in request.POST:
            company_id = request.POST.get("update_company")
            company = get_object_or_404(Company, id=company_id)
            company.name = request.POST.get("company_name")
            company.kpp = request.POST.get("company_kpp")
            company.inn = request.POST.get("company_inn")
            company.save()
        elif "delete_company" in request.POST:
            company_id = request.POST.get("delete_id")
            company = get_object_or_404(Company, id=company_id)
            company.delete()

        elif "add_department" in request.POST:
            name = request.POST.get("new_department_name")
            if name:
                Department.objects.create(name=name)
        elif "update_department" in request.POST:
            department_id = request.POST.get("update_department")
            department = get_object_or_404(Department, id=department_id)
            department.name = request.POST.get("department_name")
            department.save()
        elif "delete_department" in request.POST:
            department_id = request.POST.get("delete_id")
            department = get_object_or_404(Department, id=department_id)
            department.delete()

        elif "add_position" in request.POST:
            name = request.POST.get("new_position_name")
            salary_limit = request.POST.get("new_position_salary_limit")
            if name and salary_limit:
                Position.objects.create(name=name, salary_limit=salary_limit)
        elif "update_position" in request.POST:
            position_id = request.POST.get("update_position")
            position = get_object_or_404(Position, id=position_id)
            position.name = request.POST.get("position_name")
            position.salary_limit = request.POST.get("position_salary_limit")
            position.save()
        elif "delete_position" in request.POST:
            position_id = request.POST.get("delete_id")
            position = get_object_or_404(Position, id=position_id)
            position.delete()

        elif "add_tariff" in request.POST:
            name = request.POST.get("new_tariff_name")
            operator_id = request.POST.get("new_tariff_operator")
            if name:
                operator = Operator.objects.get(
                    id=operator_id) if operator_id else None
                Tariff.objects.create(name=name, operator=operator)
        elif "update_tariff" in request.POST:
            tariff_id = request.POST.get("update_tariff")
            tariff = get_object_or_404(Tariff, id=tariff_id)
            tariff.name = request.POST.get("tariff_name")
            operator_id = request.POST.get("tariff_operator")
            tariff.operator = Operator.objects.get(
                id=operator_id) if operator_id else None
            tariff.save()
        elif "delete_tariff" in request.POST:
            tariff_id = request.POST.get("delete_id")
            tariff = get_object_or_404(Tariff, id=tariff_id)
            tariff.delete()

        elif "add_operator" in request.POST:
            name = request.POST.get("new_operator_name")
            if name:
                Operator.objects.create(name=name)
        elif "update_operator" in request.POST:
            operator_id = request.POST.get("update_operator")
            operator = get_object_or_404(Operator, id=operator_id)
            operator.name = request.POST.get("operator_name")
            operator.save()
        elif "delete_operator" in request.POST:
            operator_id = request.POST.get("delete_id")
            operator = get_object_or_404(Operator, id=operator_id)
            operator.delete()

        return HttpResponseRedirect(reverse("data") + f"?tab={active_tab}")

    companies = Company.objects.all()
    departments = Department.objects.all()
    positions = Position.objects.all()
    tariffs = Tariff.objects.all()
    operators = Operator.objects.all()

    return render(request, "data.html", {
        "companies": companies,
        "departments": departments,
        "positions": positions,
        "tariffs": tariffs,
        "operators": operators,
    })


@login_required_custom
def numbers_view(request):
    if request.method == "POST":
        if "check_unique" in request.POST:
            phone_number = request.POST.get("new_phone_number")
            exists = PhoneNumber.objects.filter(number=phone_number).exists()
            return JsonResponse({'exists': exists})

        elif "add_phone" in request.POST:
            phone_number = request.POST.get("new_phone_number")
            account_number = request.POST.get("new_phone_account_number")
            tariff_id = request.POST.get("new_phone_tariff")
            company_id = request.POST.get("new_phone_company")

            if not all([phone_number, account_number, tariff_id]):
                return JsonResponse({'error': 'Все поля должны быть заполнены'})

            if not (phone_number.isdigit() and len(phone_number) == 10):
                return JsonResponse({'error': 'Номер телефона должен содержать ровно 10 цифр без букв'})

            if not (account_number.isdigit() and len(account_number) == 12):
                return JsonResponse({'error': 'Лицевой номер счета должен содержать ровно 12 цифр без букв'})

            tariff = get_object_or_404(Tariff, id=tariff_id)

            try:
                phone = PhoneNumber.objects.create(
                    number=phone_number,
                    status="свободен",
                    account_number=account_number,
                    tariff=tariff
                )
                if company_id:
                    company = get_object_or_404(Company, id=company_id)
                    CompanyPhoneNumber.objects.create(
                        phone_number=phone, company=company)
                return JsonResponse({'success': True})
            except IntegrityError:
                return JsonResponse({'error': 'Такой номер уже существует'})
            except Exception as e:
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

        elif "update_phone" in request.POST:
            phone_id = request.POST.get("update_phone")
            phone = get_object_or_404(PhoneNumber, id=phone_id)
            new_account_number = request.POST.get(
                "phone_number_account_number")
            new_tariff_id = request.POST.get("phone_number_tariff")
            new_company_id = request.POST.get("phone_number_company")

            if not (new_account_number.isdigit() and len(new_account_number) == 12):
                return JsonResponse({'error': 'Лицевой номер счета должен содержать ровно 12 цифр без букв'})

            try:
                phone.account_number = new_account_number
                phone.tariff = get_object_or_404(Tariff, id=new_tariff_id)
                phone.save()

                CompanyPhoneNumber.objects.filter(phone_number=phone).delete()
                if new_company_id:
                    company = get_object_or_404(Company, id=new_company_id)
                    CompanyPhoneNumber.objects.create(
                        phone_number=phone, company=company)

                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

        elif "delete_phone" in request.POST:
            phone_id = request.POST.get("delete_phone")
            phone = get_object_or_404(PhoneNumber, id=phone_id)
            phone.delete()
            return JsonResponse({'success': True})

    phone_numbers = PhoneNumber.objects.filter(status='свободен').select_related(
        'tariff__operator', 'company_number__company'
    )
    tariffs = Tariff.objects.select_related('operator')
    operators = Operator.objects.all()
    employees = Employee.objects.filter(status=True).select_related('company')
    companies = Company.objects.all()

    phone_history_data = []
    for phone in phone_numbers:
        history = PhoneNumberHistory.objects.filter(
            phone_number=phone).order_by('-start_date')
        usage_info = [
            {
                'employee_name': f"{record.employee.last_name} {record.employee.first_name} {record.employee.middle_name or ''}",
                'start_date': record.start_date,
                'end_date': record.end_date,
                'comment': record.comment
            }
            for record in history
        ] if history.exists() else [{'message': 'История использования отсутствует.'}]
        phone_history_data.append((phone, usage_info))

    return render(request, "numbers.html", {
        "phone_numbers": phone_numbers,
        "tariffs": tariffs,
        "operators": operators,
        "phone_history_data": phone_history_data,
        "employees": employees,
        "companies": companies,
    })


@login_required_custom
@csrf_exempt
def import_numbers(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            logger.warning("Импорт CSV: Файл не предоставлен")
            return JsonResponse({'success': False, 'errors': ['Файл не предоставлен']})

        if not csv_file.name.endswith('.csv'):
            logger.warning("Импорт CSV: Неверный формат файла")
            return JsonResponse({'success': False, 'errors': ['Файл должен быть в формате CSV']})

        errors = []
        added = 0
        try:
            csv_reader = csv.DictReader(TextIOWrapper(csv_file, encoding='utf-8'))
            required_headers = ['Оператор', 'Номер', 'Лиц. счёт', 'Тариф', 'Компания']
            if not all(header in csv_reader.fieldnames for header in required_headers):
                logger.warning("Импорт CSV: Неверные заголовки")
                return JsonResponse({'success': False, 'errors': ['Неверный формат CSV. Требуемые столбцы: Оператор, Номер, Лиц. счёт, Тариф, Компания']})

            for row_idx, row in enumerate(csv_reader, start=1):
                try:
                    # Валидация
                    number = row['Номер'].strip()
                    account_number = row['Лиц. счёт'].strip()
                    operator_name = row['Оператор'].strip()
                    tariff_name = row['Тариф'].strip()
                    company_name = row['Компания'].strip()

                    if not number.isdigit() or len(number) != 10:
                        errors.append(f"Строка {row_idx}: Номер {number} должен содержать ровно 10 цифр")
                        continue
                    if not operator_name or not tariff_name or not company_name:
                        errors.append(f"Строка {row_idx}: Поля Оператор, Тариф и Компания не могут быть пустыми для номера {number}")
                        continue

                    # Проверка уникальности номера
                    if PhoneNumber.objects.filter(number=number).exists():
                        errors.append(f"Строка {row_idx}: Номер {number} уже существует")
                        continue

                    with transaction.atomic():
                        # Оператор
                        operator, created = Operator.objects.get_or_create(
                            name=operator_name,
                            defaults={'name': operator_name}
                        )
                        if created:
                            logger.info(f"Создан новый оператор: {operator_name}")
                        else:
                            logger.info(f"Использован существующий оператор: {operator_name}")

                        # Тариф
                        tariff, created = Tariff.objects.get_or_create(
                            name=tariff_name,
                            operator=operator
                        )
                        if created:
                            logger.info(f"Создан новый тариф: {tariff_name}")
                        else:
                            logger.info(f"Использован существующий тариф: {tariff_name}")

                        # Компания
                        company, created = Company.objects.get_or_create(
                            name=company_name,
                            defaults={
                                'name': company_name,
                                'kpp': None,  # Значение по умолчанию
                                'inn': None  # Значение по умолчанию
                            }
                        )
                        if created:
                            logger.info(f"Создана новая компания: {company_name} с KPP={company.kpp}, INN={company.inn}")
                        else:
                            logger.info(f"Использована существующая компания: {company_name}")

                        # Создание PhoneNumber
                        phone_number = PhoneNumber.objects.create(
                            number=number,
                            account_number=account_number,
                            tariff=tariff,
                            status='свободен'  # Значение по умолчанию
                        )
                        logger.info(f"Создан номер: {number}, статус по умолчанию: свободен")

                        # Создание CompanyPhoneNumber
                        CompanyPhoneNumber.objects.create(
                            phone_number=phone_number,
                            company=company
                        )
                        logger.info(f"Создана связь: {company_name} - {number}")

                        added += 1

                except Exception as e:
                    logger.error(f"Ошибка обработки строки {row_idx}: {str(e)}")
                    errors.append(f"Строка {row_idx}: Ошибка для номера {row.get('Номер', 'неизвестно')}: {str(e)}")
                    continue

            logger.info(f"Импорт CSV: Добавлено {added} записей, ошибок: {len(errors)}")
            return JsonResponse({
                'success': len(errors) == 0,
                'added': added,
                'errors': errors
            })

        except Exception as e:
            logger.error(f"Ошибка обработки CSV: {str(e)}")
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })

    logger.warning("Импорт CSV: Метод не поддерживается")
    return JsonResponse({
        'success': False,
        'errors': ['Метод не поддерживается']
    })


@login_required_custom
def issue_phone_view(request):
    if request.method == "POST":
        phone_id = request.POST.get("phone_id")
        employee_id = request.POST.get("employee_id")
        comment = request.POST.get("comment", "")

        try:
            phone = get_object_or_404(
                PhoneNumber, id=phone_id, status='свободен')
            employee = get_object_or_404(Employee, id=employee_id, status=True)

            company_number = CompanyPhoneNumber.objects.filter(
                phone_number=phone).first()
            if company_number and employee.company != company_number.company:
                return JsonResponse({"success": False, "error": "Сотрудник не принадлежит компании номера"}, status=400)

            existing_record = EmployeePhoneNumber.objects.filter(
                phone_number=phone).first()
            if existing_record:
                return JsonResponse({"success": False, "error": "Этот номер уже выдан другому сотруднику"}, status=400)

            phone.status = "занят"
            phone.save()

            EmployeePhoneNumber.objects.create(
                phone_number=phone, employee=employee)

            PhoneNumberHistory.objects.create(
                phone_number=phone,
                employee=employee,
                start_date=timezone.now().date(),
                comment=comment or "Номер выдан сотруднику",
            )
            logger.info(
                f"Номер {phone.number} выдан сотруднику {employee.id} с комментарием: {comment}")

            return JsonResponse({"success": True})

        except Exception as e:
            logger.error(f"Ошибка при выдаче номера {phone_id}: {str(e)}")
            return JsonResponse({"success": False, "error": f"Ошибка сервера: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "error": "Неверный запрос"}, status=400)


@login_required_custom
def return_phone_view(request):
    if request.method == "POST":
        phone_id = request.POST.get("phone_id")
        comment = request.POST.get("comment", "Номер возвращён в пул")

        try:
            phone = get_object_or_404(PhoneNumber, id=phone_id, status="занят")
            employee_phone = get_object_or_404(
                EmployeePhoneNumber, phone_number=phone)

            phone.status = "свободен"
            phone.save()

            history_entry = PhoneNumberHistory.objects.filter(
                phone_number=phone, end_date__isnull=True
            ).last()
            if history_entry:
                history_entry.end_date = timezone.now().date()
                history_entry.comment = comment
                history_entry.save()
                logger.info(
                    f"История номера {phone.number} обновлена: end_date={history_entry.end_date}, comment={comment}")
            else:
                logger.warning(
                    f"Не найдена незакрытая запись в истории для номера {phone.number}")

            employee_phone.delete()
            logger.info(
                f"Номер {phone.number} возвращён в пул, связь с сотрудником удалена")

            return JsonResponse({"success": True})

        except Exception as e:
            logger.error(f"Ошибка при возврате номера {phone_id}: {str(e)}")
            return JsonResponse({"success": False, "error": f"Ошибка сервера: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "error": "Неверный запрос"}, status=400)


@login_required_custom
def transfer_phone_view(request):
    if request.method == "POST":
        try:
            phone_id = request.POST.get("phone_id")
            comment = request.POST.get("comment", "Номер отдан сотруднику")

            if not phone_id:
                return JsonResponse({"success": False, "error": "Отсутствует phone_id"}, status=400)

            phone = get_object_or_404(PhoneNumber, id=phone_id, status="занят")
            employee_phone = get_object_or_404(
                EmployeePhoneNumber, phone_number=phone)

            phone.status = "отдан"
            phone.save()

            history_entry = PhoneNumberHistory.objects.filter(
                phone_number=phone, end_date__isnull=True
            ).last()
            if history_entry:
                history_entry.end_date = timezone.now().date()
                history_entry.comment = comment
                history_entry.save()
                logger.info(
                    f"История номера {phone.number} обновлена: end_date={history_entry.end_date}, comment={comment}")
            else:
                logger.warning(
                    f"Не найдена незакрытая запись в истории для номера {phone.number}")

            employee_phone.delete()
            logger.info(
                f"Номер {phone.number} отдан, связь с сотрудником удалена")

            return JsonResponse({"success": True})

        except Exception as e:
            logger.error(f"Ошибка при передаче номера {phone_id}: {str(e)}")
            return JsonResponse({"success": False, "error": f"Ошибка сервера: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "error": "Неверный запрос"}, status=400)


@login_required_custom
def phone_history_view(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id)
    history = PhoneNumberHistory.objects.filter(
        phone_number=phone).order_by('-start_date')

    usage_info = [
        {
            'employee_name': f"{record.employee.last_name} {record.employee.first_name} {record.employee.middle_name or ''}",
            'start_date': record.start_date.strftime('%d.%m.%Y'),
            'end_date': record.end_date.strftime('%d.%m.%Y') if record.end_date else None,
            'comment': record.comment or ''
        }
        for record in history
    ] if history.exists() else [{'message': 'История использования отсутствует.'}]

    return JsonResponse({'history': usage_info})


@login_required_custom
def expenses(request):
    companies = Company.objects.all()
    return render(request, "expenses.html", {"companies": companies})


@login_required_custom
def expenses_ajax(request):
    try:
        company_id = request.GET.get("company")
        start_date = request.GET.get("start_date")
        account = request.GET.get("account")
        employee_id = request.GET.get("employee")

        logger.debug(
            f"Параметры запроса: company_id={company_id}, start_date={start_date}, account={account}, employee_id={employee_id}")

        if not start_date:
            return JsonResponse({"error": "Дата не выбрана"}, status=400)

        year = int(start_date[:4])
        month = int(start_date[5:])

        expenses_qs = Expense.objects.filter(
            usage_period__year=year,
            usage_period__month=month
        )

        if company_id:
            expenses_qs = expenses_qs.filter(
                phone_number__employee_number__employee__company_id=company_id)

        if account:
            expenses_qs = expenses_qs.filter(
                phone_number__account_number=account)

        if employee_id:
            expenses_qs = expenses_qs.filter(
                phone_number__employee_number__employee_id=employee_id)

        total_expenses = expenses_qs.aggregate(
            total=Sum("amount"))["total"] or 0

        expenses_data = [
            {
                "employee": f"{exp.phone_number.employee_number.employee.last_name} {exp.phone_number.employee_number.employee.first_name} {exp.phone_number.employee_number.employee.middle_name or ''}".strip()
                if exp.phone_number.employee_number else "Неизвестно",
                "company": exp.phone_number.employee_number.employee.company.name if exp.phone_number.employee_number else "Неизвестно",
                "personnel_number": exp.phone_number.employee_number.employee.personnel_number if exp.phone_number.employee_number else "Неизвестно",
                "phone_number": exp.phone_number.number if exp.phone_number else "Неизвестно",
                "account": exp.phone_number.account_number if exp.phone_number else "Неизвестно",
                "date": exp.usage_period.strftime("%d.%m.%Y"),
                "amount": float(exp.amount),
                "limit": float(exp.phone_number.employee_number.employee.position.salary_limit) if exp.phone_number.employee_number else 0,
            }
            for exp in expenses_qs
        ]

        accounts = expenses_qs.values_list(
            "phone_number__account_number", flat=True).distinct()
        employees = expenses_qs.values_list(
            "phone_number__employee_number__employee_id",
            "phone_number__employee_number__employee__last_name",
            "phone_number__employee_number__employee__first_name",
            "phone_number__employee_number__employee__middle_name"
        ).distinct()
        employees_data = [
            {"id": emp[0], "name": f"{emp[1]} {emp[2]} {emp[3] or ''}".strip()} for emp in employees]

        return JsonResponse({
            "total_expenses": total_expenses,
            "expenses": expenses_data,
            "accounts": list(accounts),
            "employees": employees_data
        })

    except Exception as e:
        error_message = traceback.format_exc()
        logger.error("Ошибка в expenses_ajax: %s", error_message)
        return JsonResponse({"error": str(e), "traceback": error_message}, status=500)


@csrf_exempt
@login_required_custom
def expenses_import(request):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})

    try:
        usage_period = request.POST.get('usage_period')
        csv_file = request.FILES.get('csv_file')

        if not usage_period or not csv_file:
            return JsonResponse({
                'success': False,
                'message': 'Необходимо выбрать период и загрузить файл'
            })

        try:
            year, month = map(int, usage_period.split('-'))
            usage_date = datetime.date(year, month, 1)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Неверный формат периода (ожидается YYYY-MM)'
            })

        csv_file.seek(0)
        csv_file = TextIOWrapper(
            csv_file.file, encoding='utf-8', errors='ignore')
        reader = csv.reader(csv_file)

        next(reader)

        created_count = 0
        duplicate_errors = []
        format_errors = []

        for row in reader:
            try:
                if len(row) < 3:
                    format_errors.append(
                        f"Недостаточно данных: строка {reader.line_num}")
                    continue

                account_number_str = row[0].strip()
                phone_number_str = row[1].strip()
                amount_str = row[2].strip()

                try:
                    account_number = int(account_number_str)
                except ValueError:
                    format_errors.append(
                        f"Неверный формат лицевого счета: {account_number_str} в строке {reader.line_num}")
                    continue

                try:
                    phone_number = int(phone_number_str)
                except ValueError:
                    format_errors.append(
                        f"Неверный формат номера телефона: {phone_number_str} в строке {reader.line_num}")
                    continue

                amount_str = amount_str.replace(',', '.').strip()
                try:
                    amount = round(float(amount_str), 2)
                except ValueError:
                    format_errors.append(
                        f"Неверный формат суммы: {amount_str} в строке {reader.line_num}")
                    continue

                phone = PhoneNumber.objects.filter(number=str(
                    phone_number), account_number=str(account_number)).first()

                if not phone:
                    format_errors.append(
                        f"Не найден номер {phone_number} с лицевым счетом {account_number} в строке {reader.line_num}")
                    continue

                if Expense.objects.filter(phone_number=phone, usage_period=usage_date).exists():
                    duplicate_errors.append(
                        f"Расходы для {phone_number} за {usage_period} уже существуют в строке {reader.line_num}")
                    continue

                employee_phone = EmployeePhoneNumber.objects.filter(
                    phone_number=phone).first()
                limit = 0
                if employee_phone and employee_phone.employee:
                    limit = float(
                        employee_phone.employee.position.salary_limit)

                status = "превышен" if amount > limit else "не превышен"

                expense = Expense(
                    phone_number=phone,
                    minute_usage=0,
                    gb_usage=0,
                    amount=amount,
                    usage_period=usage_date,
                    status=status
                )
                expense.save()
                created_count += 1

            except Exception as e:
                format_errors.append(
                    f"Ошибка в строке {reader.line_num}: {str(e)}")
                logger.error(f"Ошибка на строке {reader.line_num}: {str(e)}")

        message = f"Успешно импортировано {created_count} записей."

        if created_count > 0:
            if duplicate_errors:
                message += "\nОшибки:\n" + "\n".join(duplicate_errors)
        else:
            all_errors = duplicate_errors + format_errors
            if all_errors:
                message += "\nОшибки:\n" + "\n".join(all_errors)

        return JsonResponse({
            'success': True if created_count > 0 else False,
            'message': message
        })

    except Exception as e:
        logger.error(f"Ошибка при импорте: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при импорте: {str(e)}'
        })


@login_required_custom
def users_view(request):
    if request.method == "POST":
        logger.info("Получен POST-запрос: %s", request.POST)

        if 'check_unique' in request.POST:
            login = request.POST.get('new_user_login')
            login_hash = hashlib.sha256(login.encode('utf-8')).hexdigest()
            exists = User.objects.filter(login_hash=login_hash).exists()
            logger.info("Проверка уникальности пользователя: %s", exists)
            return JsonResponse({'exists': exists})

        elif 'check_unique_role' in request.POST:
            name = request.POST.get('new_role_name')
            exists = Role.objects.filter(name=name).exists()
            logger.info("Проверка уникальности роли: %s", exists)
            return JsonResponse({'exists': exists})

        elif 'add_user' in request.POST:
            login = request.POST.get("new_user_login")
            password = request.POST.get("new_user_password")
            role_id = request.POST.get("new_user_role")
            employee_id = request.POST.get("new_user_employee")

            logger.info("Добавление пользователя: %s", login)

            if all([login, password, role_id]):
                try:
                    login_hash = hashlib.sha256(
                        login.encode('utf-8')).hexdigest()
                    if User.objects.filter(login_hash=login_hash).exists():
                        logger.warning("Логин %s уже используется", login)
                        return JsonResponse({'error': 'Пользователь с таким логином уже существует'})

                    role = get_object_or_404(Role, id=role_id)
                    user = User.objects.create(
                        login_hash=login_hash,
                        password_hash=hashlib.sha256(
                            password.encode('utf-8')).hexdigest(),
                        role=role,
                    )

                    if employee_id:
                        employee = get_object_or_404(Employee, id=employee_id)
                        if employee.user and employee.user != user:
                            logger.warning(
                                "Сотрудник %s уже привязан к другому пользователю", employee_id)
                            user.delete()
                            return JsonResponse({'error': 'Этот сотрудник уже привязан к другому пользователю'})
                        employee.user = user
                        employee.save()

                    logger.info(
                        "Пользователь успешно добавлен с ID: %s", user.id)
                    return JsonResponse({'success': True})
                except Exception as e:
                    logger.error(
                        "Ошибка при добавлении пользователя: %s", str(e))
                    return JsonResponse({'error': f'Ошибка: {str(e)}'})
            else:
                return JsonResponse({'error': 'Все поля должны быть заполнены'})

        elif 'add_role' in request.POST:
            name = request.POST.get("new_role_name")

            logger.info("Добавление роли: %s", name)

            if name:
                try:
                    if Role.objects.filter(name=name).exists():
                        logger.warning("Роль %s уже существует", name)
                        return JsonResponse({'error': 'Роль с таким названием уже существует'})

                    role = Role.objects.create(name=name)
                    logger.info("Роль успешно добавлена с ID: %s", role.id)
                    return JsonResponse({'success': True})
                except Exception as e:
                    logger.error("Ошибка при добавлении роли: %s", str(e))
                    return JsonResponse({'error': f'Ошибка: {str(e)}'})
            else:
                return JsonResponse({'error': 'Поле названия должно быть заполнено'})

        elif "update_user" in request.POST:
            user_id = request.POST.get("update_user")
            user = get_object_or_404(User, id=user_id)
            new_login = request.POST.get("user_login")
            new_password = request.POST.get("user_password")
            role_id = request.POST.get("user_role")
            employee_id = request.POST.get("user_employee")

            new_login_hash = hashlib.sha256(
                new_login.encode('utf-8')).hexdigest()

            if User.objects.filter(login_hash=new_login_hash).exclude(id=user_id).exists():
                logger.warning(
                    "Логин %s уже используется другим пользователем", new_login)
                return JsonResponse({'error': 'Пользователь с таким логином уже существует'})

            try:
                user.login_hash = new_login_hash
                if new_password:
                    user.password_hash = hashlib.sha256(
                        new_password.encode('utf-8')).hexdigest()
                user.role = get_object_or_404(Role, id=role_id)
                user.save()

                Employee.objects.filter(user=user).update(user=None)
                if employee_id:
                    employee = get_object_or_404(Employee, id=employee_id)
                    if employee.user and employee.user != user:
                        logger.warning(
                            "Сотрудник %s уже привязан к другому пользователю", employee_id)
                        return JsonResponse({'error': 'Этот сотрудник уже привязан к другому пользователю'})
                    employee.user = user
                    employee.save()

                logger.info("Пользователь обновлен: %s", user_id)
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error("Ошибка при обновлении пользователя: %s", str(e))
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

        elif "update_role" in request.POST:
            role_id = request.POST.get("update_role")
            role = get_object_or_404(Role, id=role_id)
            new_name = request.POST.get("role_name")

            if Role.objects.filter(name=new_name).exclude(id=role_id).exists():
                logger.warning("Роль %s уже существует", new_name)
                return JsonResponse({'error': 'Роль с таким названием уже существует'})

            try:
                role.name = new_name
                role.save()
                logger.info("Роль обновлена: %s", role_id)
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error("Ошибка при обновлении роли: %s", str(e))
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

        elif "delete_user" in request.POST:
            user_id = request.POST.get("delete_user")
            user = get_object_or_404(User, id=user_id)
            logger.info("Попытка удаления пользователя ID: %s", user_id)
            try:
                Employee.objects.filter(user=user).update(user=None)
                user.delete()
                logger.info("Пользователь удалён: %s", user_id)
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error("Ошибка при удалении пользователя: %s", str(e))
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

        elif "delete_role" in request.POST:
            role_id = request.POST.get("delete_role")
            role = get_object_or_404(Role, id=role_id)
            logger.info("Попытка удаления роли ID: %s", role_id)
            try:
                if User.objects.filter(role=role).exists():
                    logger.warning(
                        "Роль %s используется пользователями и не может быть удалена", role.name)
                    return JsonResponse({'error': 'Эта роль используется пользователями и не может быть удалена'})
                role.delete()
                logger.info("Роль удалена: %s", role_id)
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error("Ошибка при удалении роли: %s", str(e))
                return JsonResponse({'error': f'Ошибка: {str(e)}'})

    users = User.objects.select_related('role').prefetch_related(
        'employee__company').all()
    roles = Role.objects.all()
    employees = Employee.objects.filter(status=True)

    return render(request, "users.html", {
        "users": users,
        "roles": roles,
        "employees": employees,
    })
