// $(document).ready(function () {
//     const options = {
//         language: {
//             url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/ru.json'
//         },
//         paging: true,
//         searching: true,
//         ordering: true,
//         info: true,
//         dom: 'lfrtip'
//     };

//     var phoneTable = $('#phone-number-table').DataTable(options);
//     var employeeTable = $('#employee-phone-table').DataTable(options);

//     // Извлечение данных для фильтров и форм
//     const operators = [...new Set(
//         $('#phone-number-table tbody tr').map(function () {
//             return $(this).find('td').eq(1).text().trim();
//         }).get().filter(name => name !== '—')
//     )].sort();

//     const tariffs = [...new Set(
//         $('#phone-number-table tbody tr').map(function () {
//             return $(this).find('td').eq(4).text().trim();
//         }).get().filter(name => name !== '—')
//     )].sort();

//     const companies = [...new Set(
//         $('#employee-phone-table tbody tr').map(function () {
//             return $(this).find('td').eq(0).text().trim();
//         }).get().filter(name => name !== '—')
//     )].sort();

//     const employees = $('#employeeSelect option').map(function () {
//         return {
//             name: $(this).text().trim(),
//             id: $(this).val(),
//             personnel: $(this).data('personnel') || ''
//         };
//     }).get();

//     // Объект для соответствия отображаемого текста и ID для модальных окон
//     const operatorMap = {};
//     $('#newPhoneOperator option').each(function () {
//         operatorMap[$(this).text().trim()] = $(this).val();
//     });

//     const tariffMap = {};
//     $('#newPhoneTariff option').each(function () {
//         tariffMap[$(this).text().trim()] = $(this).val();
//     });

//     // Функция для отображения списка элементов в выпадающем меню
//     function showCustomList(inputElement, dropElement, items, filterType, selectElement, maxItems = 5) {
//         const filterValue = inputElement.val().toLowerCase().trim();
//         let filteredItems = filterValue
//             ? items.filter(item => item.toLowerCase().includes(filterValue))
//             : items;

//         filteredItems.sort();
//         const displayItems = filteredItems.slice(0, maxItems);

//         dropElement.empty();
//         displayItems.forEach(item => {
//             const listItem = $('<li></li>').text(item).appendTo(dropElement);
//             listItem.click(() => {
//                 inputElement.val(item);
//                 dropElement.css('height', '0');
//                 dropElement.empty();
//                 if (selectElement) {
//                     if (filterType === 'operator') {
//                         selectElement.val(operatorMap[item] || '');
//                     } else if (filterType === 'tariff') {
//                         selectElement.val(tariffMap[item] || '');
//                     } else if (filterType === 'employee') {
//                         const selectedEmployee = employees.find(emp => emp.name === item);
//                         selectElement.val(selectedEmployee ? selectedEmployee.id : '');
//                         $('#personnelNumber').text(selectedEmployee ? selectedEmployee.personnel : '');
//                     }
//                 } else {
//                     if ($('#phone-numbers-tab').hasClass('active')) {
//                         applyFilters();
//                     } else {
//                         applyEmployeeFilters();
//                     }
//                 }
//             });
//         });

//         dropElement.css('height', displayItems.length > 0 ? 'auto' : '0');
//     }

//     // Применение фильтров к таблице номеров телефонов
//     function applyFilters() {
//         const operatorFilter = $('#operatorFilter').val().trim();
//         const tariffFilter = $('#tariffFilter').val().trim();

//         phoneTable.columns(1).search(operatorFilter);
//         phoneTable.columns(4).search(tariffFilter);
//         phoneTable.draw();
//     }

//     // Применение фильтров к таблице номеров сотрудников
//     function applyEmployeeFilters() {
//         const companyFilter = $('#companyFilter').val().trim();
//         employeeTable.columns(0).search(companyFilter);
//         employeeTable.draw();
//     }

//     // Инициализация фильтров
//     applyFilters();
//     applyEmployeeFilters();

//     // Обработчики для фильтров на вкладке "Номера телефонов"
//     $('#phone-numbers-tab .custom-filter input').each(function () {
//         const input = $(this);
//         const drop = input.siblings('.custom-drop');
//         const filterType = drop.data('filter');
//         const items = filterType === 'operator' ? operators : tariffs;

//         input.on('click input', function () {
//             showCustomList(input, drop, items, filterType, null, Infinity);
//         });

//         input.on('change', function () {
//             applyFilters();
//         });
//     });

//     // Обработчик для фильтра на вкладке "Номера сотрудников"
//     $('#employee-phones-tab .custom-filter input').each(function () {
//         const input = $(this);
//         const drop = input.siblings('.custom-drop');
//         const filterType = drop.data('filter');
//         const items = companies;

//         input.on('click input', function () {
//             showCustomList(input, drop, items, filterType, null, Infinity);
//         });

//         input.on('change', function () {
//             applyEmployeeFilters();
//         });
//     });

//     // Обработчики для кастомных выпадающих списков в модальных окнах
//     $('.modal-content .custom-filter input').each(function () {
//         const input = $(this);
//         const drop = input.siblings('.custom-drop');
//         const selectElement = input.parent().find('select');
//         const filterType = drop.data('filter');

//         input.on('click input', function () {
//             showCustomList(input, drop,
//                 filterType === 'operator' ? operators :
//                     filterType === 'tariff' ? tariffs :
//                         employees.map(emp => emp.name),
//                 filterType, selectElement, Infinity);
//         });
//     });

//     // Закрытие выпадающего списка при клике вне
//     $(document).click(function (e) {
//         $('.custom-filter input').each(function () {
//             const input = $(this);
//             const drop = input.siblings('.custom-drop');
//             if (!input.is(e.target) && !drop.is(e.target) && drop.has(e.target).length === 0) {
//                 drop.css('height', '0');
//                 drop.empty();
//             }
//         });
//     });

//     // Переключение вкладок
//     $('.tab-menu li')
//         .not('.add-tab')
//         .click(function () {
//             var tabId = $(this).data('tab');
//             $('.tab-menu li').removeClass('active');
//             $(this).addClass('active');
//             $('.tab-content').removeClass('active').hide();
//             $('#' + tabId)
//                 .addClass('active')
//                 .show();
//         });

//     // Валидация полей
//     function validatePhoneNumber(value) {
//         return /^\d{10}$/.test(value);
//     }

//     function validateAccountNumber(value) {
//         return /^\d{12}$/.test(value);
//     }

//     function validateCustomSelect(inputField, errorElement) {
//         const value = inputField.val().trim();
//         const isValid = value !== '';
//         if (!isValid) {
//             inputField.addClass('invalid');
//             errorElement.text('Пожалуйста, выберите значение').show();
//         } else {
//             inputField.removeClass('invalid');
//             errorElement.hide();
//         }
//         return isValid;
//     }

//     // Открытие модального окна для добавления
//     $('#openAddModal').click(function () {
//         $('#addModal').fadeIn();
//         $('#addPhoneForm')[0].reset();
//         $('#addPhoneForm .error-message').hide();
//         $('#newPhoneOperatorDisplay').val('');
//         $('#newPhoneTariffDisplay').val('');
//         $('#addPhoneForm .input-field').removeClass('invalid');
//         $('#addPhoneForm .custom-filter input').removeClass('invalid');
//     });
//     $('#modalCloseAdd, #addModal').click(function (e) {
//         if (e.target !== this) return;
//         $('#addModal').fadeOut();
//     });

//     // Добавление номера с валидацией и проверкой уникальности
//     $('#addPhoneForm').on('submit', function (e) {
//         e.preventDefault();
//         var form = $(this);
//         var phoneNumber = $('#newPhoneNumber').val();
//         var accountNumber = $('#newPhoneAccountNumber').val();
//         var operatorInput = $('#newPhoneOperatorDisplay');
//         var tariffInput = $('#newPhoneTariffDisplay');

//         var isValid = true;
//         if (!validatePhoneNumber(phoneNumber)) {
//             $('#errorNewPhoneNumber').text('Номер телефона должен содержать ровно 10 цифр без букв').show();
//             $('#newPhoneNumber').addClass('invalid');
//             isValid = false;
//         } else {
//             $('#errorNewPhoneNumber').hide();
//             $('#newPhoneNumber').removeClass('invalid');
//         }
//         if (!validateAccountNumber(accountNumber)) {
//             $('#errorNewAccountNumber').text('Лицевой номер должен содержать ровно 12 цифр без букв').show();
//             $('#newPhoneAccountNumber').addClass('invalid');
//             isValid = false;
//         } else {
//             $('#errorNewAccountNumber').hide();
//             $('#newPhoneAccountNumber').removeClass('invalid');
//         }
//         if (!validateCustomSelect(operatorInput, $('#errorNewOperator'))) {
//             isValid = false;
//         }
//         if (!validateCustomSelect(tariffInput, $('#errorNewTariff'))) {
//             isValid = false;
//         }

//         if (!isValid) return;

//         $.ajax({
//             url: '/numbers/',
//             type: 'POST',
//             data: {
//                 new_phone_number: phoneNumber,
//                 check_unique: true,
//                 csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
//             },
//             success: function (response) {
//                 if (response.exists) {
//                     $('#errorNewPhoneNumber').text('Такой номер уже существует').show();
//                     $('#newPhoneNumber').addClass('invalid');
//                 } else {
//                     $.ajax({
//                         url: '/numbers/',
//                         type: 'POST',
//                         data: form.serialize() + '&add_phone=true',
//                         success: function (response) {
//                             if (response.success) {
//                                 $('#addModal').fadeOut();
//                                 location.reload();
//                             } else {
//                                 $('#errorNewPhoneNumber').text(response.error).show();
//                                 $('#newPhoneNumber').addClass('invalid');
//                             }
//                         }
//                     });
//                 }
//             }
//         });
//     });

//     // Открытие модального окна для обновления номера
//     $('.update-phone-btn').click(function () {
//         var phoneId = $(this).data('id');
//         var number = $(this).data('number');
//         var operatorId = $(this).data('operator');
//         var accountNumber = $(this).data('account-number');
//         var tariffId = $(this).data('tariff');
//         var operatorName = $(this).closest('tr').find('td').eq(1).text().trim();
//         var tariffName = $(this).closest('tr').find('td').eq(4).text().trim();

//         $('#modalPhoneId').val(phoneId);
//         $('#modalPhoneNumber').val(number);
//         $('#modalPhoneOperator').val(operatorId);
//         $('#modalPhoneOperatorDisplay').val(operatorName !== '—' ? operatorName : '');
//         $('#modalPhoneAccountNumber').val(accountNumber);
//         $('#modalPhoneTariff').val(tariffId);
//         $('#modalPhoneTariffDisplay').val(tariffName !== '—' ? tariffName : '');
//         $('#updatePhoneModal').fadeIn();
//         $('#modalUpdatePhoneForm .error-message').hide();
//         $('#modalUpdatePhoneForm .input-field').removeClass('invalid');
//         $('#modalUpdatePhoneForm .custom-filter input').removeClass('invalid');
//     });
//     $('#modalCloseUpdate, #updatePhoneModal').click(function (e) {
//         if (e.target !== this) return;
//         $('#updatePhoneModal').fadeOut();
//     });

//     // Обновление номера с валидацией
//     $('#modalUpdatePhoneForm').on('submit', function (e) {
//         e.preventDefault();
//         var form = $(this);
//         var phoneNumber = $('#modalPhoneNumber').val();
//         var accountNumber = $('#modalPhoneAccountNumber').val();
//         var operatorInput = $('#modalPhoneOperatorDisplay');
//         var tariffInput = $('#modalPhoneTariffDisplay');

//         var isValid = true;
//         if (!validatePhoneNumber(phoneNumber)) {
//             $('#errorModalPhoneNumber').text('Номер телефона должен содержать ровно 10 цифр без букв').show();
//             $('#modalPhoneNumber').addClass('invalid');
//             isValid = false;
//         } else {
//             $('#errorModalPhoneNumber').hide();
//             $('#modalPhoneNumber').removeClass('invalid');
//         }
//         if (!validateAccountNumber(accountNumber)) {
//             $('#errorModalAccountNumber').text('Лицевой номер должен содержать ровно 12 цифр без букв').show();
//             $('#modalPhoneAccountNumber').addClass('invalid');
//             isValid = false;
//         } else {
//             $('#errorModalAccountNumber').hide();
//             $('#modalPhoneAccountNumber').removeClass('invalid');
//         }
//         if (!validateCustomSelect(operatorInput, $('#errorModalOperator'))) {
//             isValid = false;
//         }
//         if (!validateCustomSelect(tariffInput, $('#errorModalTariff'))) {
//             isValid = false;
//         }

//         if (!isValid) return;

//         $.ajax({
//             url: '/numbers/',
//             type: 'POST',
//             data: form.serialize(),
//             success: function (response) {
//                 if (response.success) {
//                     $('#updatePhoneModal').fadeOut();
//                     location.reload();
//                 } else {
//                     $('#errorModalPhoneNumber').text(response.error).show();
//                     $('#modalPhoneNumber').addClass('invalid');
//                 }
//             }
//         });
//     });

//     // Открытие модального окна для подтверждения удаления
//     $('.delete-phone-btn').click(function () {
//         var phoneId = $(this).data('id');
//         var phoneNumber = $(this).data('number');
//         $('#deletePhoneId').val(phoneId);
//         $('#deleteConfirmText').text('Вы уверены, что хотите удалить номер ' + phoneNumber + '?');
//         $('#deleteConfirmModal').fadeIn();
//     });
//     $('#modalCloseDelete, #cancelDelete, #deleteConfirmModal').click(function (e) {
//         if (e.target !== this && e.target.id !== 'cancelDelete') return;
//         $('#deleteConfirmModal').fadeOut();
//     });

//     // Удаление номера
//     $('#deletePhoneForm').on('submit', function (e) {
//         e.preventDefault();
//         $.ajax({
//             url: '/numbers/',
//             type: 'POST',
//             data: $(this).serialize(),
//             success: function (response) {
//                 if (response.success) {
//                     $('#deleteConfirmModal').fadeOut();
//                     location.reload();
//                 }
//             }
//         });
//     });

//     // Открытие модального окна для выдачи номера
//     $('.issue-phone-btn').click(function () {
//         var phoneId = $(this).data('phone-id');
//         var phoneNumber = $(this).data('phone-number');
//         $('#phoneId').val(phoneId);
//         $('#modalPhoneNumber').text(phoneNumber);
//         $('#employeeSelectDisplay').val('');
//         $('#personnelNumber').text('');
//         $('#issuePhoneModal').fadeIn();
//         $('#issuePhoneForm .error-message').hide();
//         $('#issuePhoneForm .input-field').removeClass('invalid');
//         $('#issuePhoneForm .custom-filter input').removeClass('invalid');
//     });
//     $('#modalCloseIssue, #issuePhoneModal').click(function (e) {
//         if (e.target !== this) return;
//         $('#issuePhoneModal').fadeOut();
//     });

//     // Выдача номера
//     $('#issuePhoneForm').on('submit', function (e) {
//         e.preventDefault();
//         var formData = new FormData(this);
//         if (!validateCustomSelect($('#employeeSelectDisplay'), $('#errorEmployee'))) {
//             return;
//         }
//         $.ajax({
//             url: '/issue_phone/',
//             type: 'POST',
//             data: formData,
//             processData: false,
//             contentType: false,
//             success: function (data) {
//                 if (data.success) {
//                     $('#issuePhoneModal').fadeOut();
//                     location.reload();
//                 } else {
//                     $('#errorEmployee').text(data.error).show();
//                     $('#employeeSelectDisplay').addClass('invalid');
//                 }
//             }
//         });
//     });

//     // Открытие модального окна для истории номера
//     $('.history-phone-btn').click(function () {
//         var phoneId = $(this).data('phone-id');
//         var phoneNumber = $(this).data('phone-number');

//         $('#historyPhoneNumber').text(phoneNumber);
//         $('#historyContent').empty().append('<p>Загрузка истории...</p>');
//         $('#historyPhoneModal').fadeIn();

//         $.ajax({
//             url: '/phone_history/' + phoneId + '/',
//             type: 'GET',
//             success: function (response) {
//                 $('#historyContent').empty();
//                 var history = response.history;

//                 if (history && history.length > 0) {
//                     var historyList = $('<ul></ul>');
//                     history.forEach(function (entry) {
//                         if (entry.message) {
//                             historyList.append('<li>' + entry.message + '</li>');
//                         } else {
//                             var text = `${entry.employee_name}<br>С ${entry.start_date} по ${entry.end_date || 'настоящее время'}<br>Комментарий: ${entry.comment || 'нет'}`;
//                             historyList.append('<li>' + text + '</li>');
//                         }
//                     });
//                     $('#historyContent').append(historyList);
//                 } else {
//                     $('#historyContent').append('<p>История для этого номера отсутствует</p>');
//                 }
//             },
//             error: function () {
//                 $('#historyContent').empty().append('<p>Ошибка загрузки истории</p>');
//             }
//         });
//     });
//     $('#modalCloseHistory, #historyPhoneModal').click(function (e) {
//         if (e.target === this) {
//             $('#historyPhoneModal').fadeOut();
//         }
//     });

//     // Открытие модального окна для возврата номера
//     $('.return-phone-btn').click(function () {
//         var phoneId = $(this).data('phone-id');
//         var phoneNumber = $(this).data('phone-number');
//         $('#returnPhoneId').val(phoneId);
//         $('#returnModalPhoneNumber').text(phoneNumber);
//         $('#returnPhoneModal').fadeIn();
//     });
//     $('#modalCloseReturn, #returnPhoneModal').click(function (e) {
//         if (e.target !== this) return;
//         $('#returnPhoneModal').fadeOut();
//     });

//     // Возврат номера
//     $('#returnPhoneForm').on('submit', function (e) {
//         e.preventDefault();
//         var formData = new FormData(this);
//         $.ajax({
//             url: '/return_phone/',
//             type: 'POST',
//             data: formData,
//             processData: false,
//             contentType: false,
//             success: function (data) {
//                 if (data.success) {
//                     $('#returnPhoneModal').fadeOut();
//                     location.reload();
//                 } else {
//                     $('#returnComment').after('<span class="error-message">' + data.error + '</span>');
//                 }
//             }
//         });
//     });

//     // Открытие модального окна для передачи номера
//     $('.transfer-phone-btn').click(function () {
//         var phoneId = $(this).data('phone-id');
//         var phoneNumber = $(this).data('phone-number');
//         $('#transferPhoneId').val(phoneId);
//         $('#transferModalPhoneNumber').text(phoneNumber);
//         $('#transferPhoneModal').fadeIn();
//     });
//     $('#modalCloseTransfer, #cancelTransfer, #transferPhoneModal').click(function (e) {
//         if (e.target !== this && e.target.id !== 'cancelTransfer') return;
//         $('#transferPhoneModal').fadeOut();
//     });

//     // Передача номера
//     $('#transferPhoneForm').on('submit', function (e) {
//         e.preventDefault();
//         var formData = new FormData(this);
//         $.ajax({
//             url: '/transfer/',
//             type: 'POST',
//             data: formData,
//             processData: false,
//             contentType: false,
//             success: function (data) {
//                 if (data.success) {
//                     $('#transferPhoneModal').fadeOut();
//                     location.reload();
//                 } else {
//                     $('#transferPhoneForm p').after('<span class="error-message">' + data.error + '</span>');
//                 }
//             }
//         });
//     });
// });