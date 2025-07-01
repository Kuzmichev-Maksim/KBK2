$(document).ready(function () {
  const options = {
    language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/ru.json' },
    paging: true,
    searching: true,
    ordering: true,
    info: true,
    dom: 'lfrtip'
  };
  $('#company-table, #department-table, #position-table, #tariff-table, #operator-table').DataTable(options);

  $('.tab-menu li')
    .not('.add-tab')
    .click(function () {
      var tabId = $(this).data('tab');
      $('.tab-menu li').removeClass('active');
      $(this).addClass('active');
      $('.tab-content').removeClass('active').hide();
      $('#' + tabId)
        .addClass('active')
        .show();
    });

  var urlParams = new URLSearchParams(window.location.search);
  var activeTab = urlParams.get('tab');
  if (activeTab) {
    $('.tab-menu li').removeClass('active');
    $('.tab-content').removeClass('active').hide();
    $('.tab-menu li[data-tab="' + activeTab + '"]').addClass('active');
    $('#' + activeTab)
      .addClass('active')
      .show();
  }

  $('#openAddModal').click(function () {
    $('#addChoiceList').show();
    $('#addTypeSelect').hide().val('');
    $('.add-form-section').hide();
    $('#addModal').fadeIn();
  });
  $('#modalCloseAdd, #addModal').click(function (e) {
    if (e.target !== this) return;
    $('#addModal').fadeOut();
  });

  $('#addChoiceList li').click(function () {
    var choice = $(this).data('choice');
    $('#addChoiceList').hide();
    $('#addTypeSelect').show();
    $('#addTypeSelect').val(choice);
    showAddForm(choice);
  });

  $('#addTypeSelect').change(function () {
    var choice = $(this).val();
    showAddForm(choice);
  });

  function showAddForm(choice) {
    $('.add-form-section').hide();
    if (choice === 'company') $('#addCompanyForm').show();
    else if (choice === 'department') $('#addDepartmentForm').show();
    else if (choice === 'position') $('#addPositionForm').show();
    else if (choice === 'tariff') $('#addTariffForm').show();
    else if (choice === 'operator') $('#addOperatorForm').show();
  }

  $('.update-company-btn').click(function () {
    var companyId = $(this).data('id');
    var companyName = $(this).data('name');
    var companyInn = $(this).data('inn');
    var companyKpp = $(this).data('kpp');
    $('#modalCompanyId').val(companyId);
    $('#modalCompanyName').val(companyName);
    $('#modalCompanyInn').val(companyInn);
    $('#modalCompanyKpp').val(companyKpp);
    $('#updateCompanyModal').fadeIn();
  });
  $('#modalCloseCompany, #updateCompanyModal').click(function (e) {
    if (e.target !== this) return;
    $('#updateCompanyModal').fadeOut();
  });

  $('.update-department-btn').click(function () {
    var deptId = $(this).data('id');
    var deptName = $(this).data('name');
    $('#modalDepartmentId').val(deptId);
    $('#modalDepartmentName').val(deptName);
    $('#updateDepartmentModal').fadeIn();
  });
  $('#modalCloseDepartment, #updateDepartmentModal').click(function (e) {
    if (e.target !== this) return;
    $('#updateDepartmentModal').fadeOut();
  });

  $('.update-position-btn').click(function () {
    var posId = $(this).data('id');
    var posName = $(this).data('name');
    var posSalary = $(this).data('salary');
    $('#modalPositionId').val(posId);
    $('#modalPositionName').val(posName);
    $('#modalPositionSalary').val(posSalary);
    $('#updatePositionModal').fadeIn();
  });
  $('#modalClosePosition, #updatePositionModal').click(function (e) {
    if (e.target !== this) return;
    $('#updatePositionModal').fadeOut();
  });

  $('.update-tariff-btn').click(function () {
    var tariffId = $(this).data('id');
    var tariffName = $(this).data('name');
    var operatorId = $(this).data('operator');
    $('#modalTariffId').val(tariffId);
    $('#modalTariffName').val(tariffName);
    $('#modalTariffOperator').val(operatorId);
    $('#updateTariffModal').fadeIn();
  });
  $('#modalCloseTariff, #updateTariffModal').click(function (e) {
    if (e.target !== this) return;
    $('#updateTariffModal').fadeOut();
  });

  $('.update-operator-btn').click(function () {
    var operatorId = $(this).data('id');
    var operatorName = $(this).data('name');
    $('#modalOperatorId').val(operatorId);
    $('#modalOperatorName').val(operatorName);
    $('#updateOperatorModal').fadeIn();
  });
  $('#modalCloseOperator, #updateOperatorModal').click(function (e) {
    if (e.target !== this) return;
    $('#updateOperatorModal').fadeOut();
  });

  $('.delete-company-btn, .delete-department-btn, .delete-position-btn, .delete-tariff-btn, .delete-operator-btn').click(function () {
    var id = $(this).data('id');
    var name = $(this).data('name');
    var type = $(this).hasClass('delete-company-btn') ? 'company' :
               $(this).hasClass('delete-department-btn') ? 'department' :
               $(this).hasClass('delete-position-btn') ? 'position' :
               $(this).hasClass('delete-tariff-btn') ? 'tariff' : 'operator';
    var activeTab = $('.tab-menu li.active').data('tab');
    var entityType = type === 'company' ? 'компанию' :
                     type === 'department' ? 'отдел' :
                     type === 'position' ? 'должность' :
                     type === 'tariff' ? 'тариф' : 'оператора';

    $('#deleteId').val(id);
    $('#deleteType').val('delete_' + type);
    $('#deleteActiveTab').val(activeTab);
    $('#deleteConfirmText').text('Вы уверены, что хотите удалить ' + entityType + ' "' + name + '"?');
    $('#confirmDeleteBtn').attr('name', 'delete_' + type);
    $('#deleteConfirmModal').fadeIn();
  });

  $('#modalCloseDelete, #cancelDelete, #deleteConfirmModal').click(function (e) {
    if (e.target !== this && e.target.id !== 'cancelDelete') return;
    $('#deleteConfirmModal').fadeOut();
  });
});