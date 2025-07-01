from django.db import models
import hashlib


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class User(models.Model):
    login_hash = models.CharField(
        max_length=64, unique=True)
    password_hash = models.CharField(max_length=64)
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name='users')

    def set_login(self, login):
        """Устанавливает хеш логина."""
        self.login_hash = hashlib.sha256(login.encode('utf-8')).hexdigest()

    def set_password(self, password):
        """Устанавливает хеш пароля."""
        self.password_hash = hashlib.sha256(
            password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        """Проверяет пароль."""
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

    def __str__(self):
        return f"User (Role: {self.role.name})"


class Company(models.Model):
    name = models.CharField(max_length=255)
    kpp = models.CharField(max_length=9, null=True, blank=True)
    inn = models.CharField(max_length=12, null=True, blank=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=255)
    salary_limit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Employee(models.Model):
    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(default=True)
    personnel_number = models.CharField(max_length=50)
    city = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='employees')
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, related_name='employees')
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='employees')
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name='employee',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Operator(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Tariff(models.Model):
    name = models.CharField(max_length=255)
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)


class PhoneNumber(models.Model):
    number = models.CharField(max_length=15, unique=True)
    status = models.CharField(max_length=50, choices=[(
        'занят', 'Занят'), ('свободен', 'Свободен'), ('отдан', 'Отдан')])
    account_number = models.CharField(max_length=50)
    tariff = models.ForeignKey(
        Tariff, on_delete=models.CASCADE, related_name='phone_numbers')

    def __str__(self):
        return self.number


class EmployeePhoneNumber(models.Model):
    phone_number = models.OneToOneField(
        PhoneNumber, on_delete=models.CASCADE, related_name='employee_number')
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='phone_numbers')


class PhoneNumberHistory(models.Model):
    phone_number = models.ForeignKey(
        PhoneNumber, on_delete=models.CASCADE, related_name='history')
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='phone_number_history')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)


class EmployeeHistory(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='history')
    deletion_date = models.DateField()
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee} - {self.deletion_date}"


class Expense(models.Model):
    phone_number = models.ForeignKey(
        PhoneNumber, on_delete=models.CASCADE, related_name='expenses')
    minute_usage = models.PositiveIntegerField()
    gb_usage = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    usage_period = models.DateField()
    status = models.CharField(max_length=50, choices=[(
        'превышен', 'Превышен'), ('не превышен', 'Не превышен')])


class CompanyPhoneNumber(models.Model):
    phone_number = models.OneToOneField(
        PhoneNumber, on_delete=models.CASCADE, related_name='company_number')
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='phone_numbers')

    def __str__(self):
        return f"{self.company.name} - {self.phone_number.number}"