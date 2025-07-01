document.addEventListener('DOMContentLoaded', function () {
    if ($.fn.DataTable.isDataTable('#employeeTable')) {
        $('#employeeTable').DataTable().destroy();
    }

    const employeeTable = new DataTable('#employeeTable', {
        language: {
            lengthMenu: "Показать _MENU_ записей",
            zeroRecords: "Ничего не найдено",
            info: "Показано с _START_ по _END_ из _TOTAL_ записей",
            info: "Показано с _START_ по _END_ из _TOTAL_ записей",
            infoEmpty: "Показано с 0 по 0 из 0 записей",
            infoFiltered: "(отфильтровано из _MAX_ записей)",
            search: "Поиск:",
            paginate: {
                first: "Первая",
                last: "Последняя",
                next: "Следующая",
                previous: "Предыдущая"
            }
        },
        pagingType: 'full_numbers',
        lengthMenu: [10, 25, 50, 100],
        dom: '<"top"lf>rt<"bottom"ip><"clear">'
    });

    // // Обработка кнопки "Вернуть номер"
    // document.querySelectorAll('.btn-return').forEach(button => {
    //     button.addEventListener('click', function () {
    //         const employeeId = this.getAttribute('data-employee-id');
    //         alert(`Вернуть номер для сотрудника с ID: ${employeeId}`);
    //     });
    // });

    // // Обработка кнопки "Отдать номер"
    // document.querySelectorAll('.btn-assign').forEach(button => {
    //     button.addEventListener('click', function () {
    //         const employeeId = this.getAttribute('data-employee-id');
    //         alert(`Отдать номер сотруднику с ID: ${employeeId}`);
    //     });
    // });
});