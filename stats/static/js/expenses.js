const { jsPDF } = window.jspdf;

$(document).ready(function () {
  let cachedAccounts = [];
  let cachedEmployees = [];
  let companyChart = null;
  let employeeChart = null;

  const options = {
    language: {
      url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/ru.json'
    },
    paging: true,
    searching: true,
    ordering: true,
    info: true,
    dom: 'lfrtip'
  };

  var expensesTable = $('#expenses-table').DataTable(options);

  let startDateInput = document.getElementById("start_date");
  if (startDateInput) {
    let today = new Date();
    let year = today.getFullYear();
    let month = (today.getMonth() + 1).toString().padStart(2, '0');
    startDateInput.value = `${year}-${month}`;
    $('#download-pdf').prop('disabled', false);
  }

  let usagePeriodInput = document.getElementById("usage_period");
  if (usagePeriodInput) {
    let today = new Date();
    let year = today.getFullYear();
    let month = (today.getMonth() + 1).toString().padStart(2, '0');
    usagePeriodInput.value = `${year}-${month}`;
  }

  $('#start_date').on('change', function () {
    const startDate = $(this).val();
    $('#download-pdf').prop('disabled', !startDate);
  });

  loadExpenses(true);

  $('#filter-form').on('submit', function (e) {
    e.preventDefault();
    loadExpenses(true);
  });

  $('#account, #employee').on('change', function () {
    loadExpenses(false);
  });

  $('.tab-menu li').click(function () {
    $('.tab-menu li').removeClass('active');
    $(this).addClass('active');

    $('.tab-content').removeClass('active');
    $('#' + $(this).data('tab')).addClass('active');
  });

  $('#import-form').on('submit', function (e) {
    e.preventDefault();
    let formData = new FormData(this);

    $.ajax({
      url: '/expenses/import/',
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        $('#import-result').html(response.message);
        if (response.success) {
          $('#import-result').css('color', 'green');
        } else {
          $('#import-result').css('color', 'red');
        }
      },
      error: function (xhr) {
        $('#import-result').html('Произошла ошибка при импорте').css('color', 'red');
      }
    });
  });

  function formatDateToMonthYear(dateString) {
    if (!dateString) return "Не выбран";

    const months = [
      "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ];

    const date = new Date(dateString);
    const month = months[date.getMonth()];
    const year = date.getFullYear();

    return `${month} ${year}`;
  }

  $('#download-pdf').click(function () {
    if ($(this).prop('disabled')) return;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.addFileToVFS('Journalsans.ttf', JournalsansFont);
    doc.addFont('Journalsans.ttf', 'Journalsans', 'normal');
    doc.setFont('Journalsans');

    const company = $('#company option:selected').text();
    const startDate = formatDateToMonthYear($('#start_date').val());
    const account = $('#account option:selected').text();
    const employee = $('#employee option:selected').text();
    const totalExpenses = $('#total-expenses').text();

    doc.setFontSize(16);
    doc.text('Статистика расходов', 10, 10);
    doc.setFontSize(12);
    doc.text(`Компания: ${company || 'Все компании'}`, 10, 20);
    doc.text(`Период: ${startDate}`, 10, 30);
    doc.text(`Лицевой счет: ${account || 'Все'}`, 10, 40);
    doc.text(`Сотрудник: ${employee || 'Все'}`, 10, 50);
    doc.text(`Общая сумма расходов: ${totalExpenses} руб.`, 10, 60);

    Promise.all([
      html2canvas(document.getElementById('companyChart'), { scale: 2 }),
      html2canvas(document.getElementById('employeeChart'), { scale: 2 })
    ]).then(([companyCanvas, employeeCanvas]) => {
      const companyImg = companyCanvas.toDataURL('image/png');
      const employeeImg = employeeCanvas.toDataURL('image/png');

      doc.addImage(companyImg, 'PNG', 10, 70, 90, 90);
      doc.addImage(employeeImg, 'PNG', 110, 70, 90, 90);

      doc.addPage();
      doc.setFontSize(16);
      doc.text('Таблица расходов', 10, 10);
      doc.setFontSize(12);

      const tableData = expensesTable.rows().data().toArray();
      const tableBody = tableData.map(row => [row[0], row[1], row[2], row[3], row[4]]);

      doc.autoTable({
        startY: 20,
        head: [['ФИО', 'Номер', 'Лицевой счет', 'Период', 'Сумма']],
        body: tableBody,
        styles: { font: 'Journalsans', fontSize: 10 },
        headStyles: { fillColor: [35, 136, 159] },
        theme: 'grid'
      });

      doc.save('expenses_report.pdf');
    }).catch(err => {
      console.error('Ошибка при генерации PDF:', err);
    });
  });

  function loadExpenses(fullReload) {
    let company = $('#company').val();
    let start_date = $('#start_date').val();
    let account = $('#account').val();
    let employee = $('#employee').val();

    $.ajax({
      url: '/expenses/ajax/',
      data: { company, start_date, account, employee },
      success: function (data) {
        $('#total-expenses').text(data.total_expenses);

        if (fullReload) {
          cachedAccounts = data.accounts;
          cachedEmployees = data.employees;
        }

        let accountsHtml = '<option value="">Все</option>';
        cachedAccounts.forEach(acc => {
          accountsHtml += `<option value="${acc}" ${acc == account ? "selected" : ""}>${acc}</option>`;
        });
        $('#account').html(accountsHtml);

        let employeesHtml = '<option value="">Все</option>';
        cachedEmployees.forEach(emp => {
          employeesHtml += `<option value="${emp.id}" ${emp.id == employee ? "selected" : ""}>${emp.name}</option>`;
        });
        $('#employee').html(employeesHtml);

        const months = [
          "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
          "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ];

        expensesTable.clear();
        data.expenses.forEach(exp => {
          let formattedDate = "Неизвестно";
          if (exp.date) {
            let dateParts = exp.date.split('.');
            if (dateParts.length === 3) {
              let day = dateParts[0];
              let monthIndex = parseInt(dateParts[1]) - 1;
              let year = dateParts[2];
              if (monthIndex >= 0 && monthIndex < 12 && year) {
                formattedDate = `${months[monthIndex]} ${year}`;
              }
            }
          }

          expensesTable.row.add([
            exp.employee,
            exp.phone_number,
            exp.account,
            formattedDate,
            exp.amount
          ]);
        });
        expensesTable.draw();

        updateCompanyChart(data.expenses, company);
        updateEmployeeChart(data.expenses, employee);
      }
    });
  }

  function updateCompanyChart(expenses, company) {
    let labels = [];
    let values = [];

    if (!company) {
      let companyTotals = {};
      expenses.forEach(exp => {
        let companyName = exp.company || "Неизвестно";
        companyTotals[companyName] = (companyTotals[companyName] || 0) + parseFloat(exp.amount);
      });
      labels = Object.keys(companyTotals);
      values = Object.values(companyTotals);
    } else {
      let accountTotals = {};
      expenses.forEach(exp => {
        let accountNumber = exp.account || "Неизвестно";
        accountTotals[accountNumber] = (accountTotals[accountNumber] || 0) + parseFloat(exp.amount);
      });
      labels = Object.keys(accountTotals);
      values = Object.values(accountTotals);
    }

    let ctx = document.getElementById('companyChart').getContext('2d');
    if (companyChart) companyChart.destroy();

    companyChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4CAF50', '#9C27B0'],
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top' },
          title: { display: true, text: company ? 'Расходы по лицевым счетам' : 'Статистика по компаниям' }
        }
      }
    });
  }

  function updateEmployeeChart(expenses, employee) {
    let labels = [];
    let values = [];

    if (employee) {
      let phoneTotals = {};
      expenses.forEach(exp => {
        let phoneNumber = exp.phone_number || "Неизвестно";
        phoneTotals[phoneNumber] = (phoneTotals[phoneNumber] || 0) + parseFloat(exp.amount);
      });
      labels = Object.keys(phoneTotals);
      values = Object.values(phoneTotals);
    } else {
      let employeeTotals = {};
      expenses.forEach(exp => {
        let employeeName = exp.employee || "Неизвестно";
        employeeTotals[employeeName] = (employeeTotals[employeeName] || 0) + parseFloat(exp.amount);
      });
      labels = Object.keys(employeeTotals);
      values = Object.values(employeeTotals);
    }

    let ctx = document.getElementById('employeeChart').getContext('2d');
    if (employeeChart) employeeChart.destroy();

    employeeChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ['#FF9800', '#9E9E9E', '#4CAF50', '#FF6384', '#36A2EB'],
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top' },
          title: { display: true, text: employee ? 'Расходы по номерам сотрудника' : 'Статистика по сотрудникам' }
        }
      }
    });
  }
});