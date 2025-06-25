// Arabic  translations for DataTables
const dataTableArabic = { 
        "emptyTable": "لا يوجد بيانات متاحة في الجدول", 
        "info": "عرض _START_ إلى _END_ من _TOTAL_ مدخل",
        "infoEmpty": "عرض 0 إلى 0 من 0 مدخل",
        "infoFiltered": "(تمت التصفية من _MAX_ مجموع مدخلات)",
        "lengthMenu": "عرض _MENU_ مدخل",
        "loadingRecords": "جاري التحميل...",
        "processing": "جاري المعالجة...",
        "search": "بحث:",
        "zeroRecords": "لم يتم العثور على سجلات مطابقة",
        "paginate": {
            "first": "الأول",
            "last": "الأخير",
            "next": "التالي",
            "previous": "السابق"
        }
    }; 

    let assignmentsTable;
    let submissionsTable;
    const adminToken = localStorage.getItem('adminToken'); // Get token from localStorage
    
    $(document).ready(function() {
        let apiUrl; 
        // Check if we are on a specific course's assignment page
        if (window.courseId) {
            // Construct the URL for fetching assignments for this specific course
            apiUrl = `/admin/api/courses/${window.courseId}/assignments`; // Use the new JSON API endpoint
        } else {
            // Default URL for fetching all assignments (e.g., on a dashboard)
            // Assuming this endpoint exists under the admin blueprint
            apiUrl = '/admin/api/assignments'; // Keep this if it's the correct dashboard/all assignments URL
        } 
        
        if (!adminToken) {
            console.error("Admin token not found in localStorage.");
            $('#assignmentsTable tbody').html('<tr><td colspan="6" class="text-center text-danger">خطأ: رمز المصادقة غير موجود. يرجى تسجيل الدخول مرة أخرى.</td></tr>');
            // Optionally redirect to login: window.location.href = '/admin/login';
            return;
        }

        // Initialize DataTable
        assignmentsTable = $('#assignmentsTable').DataTable({
            ajax: {
                url: apiUrl, // Use the determined API URL
                dataSrc: '',
                // Add Authorization header
                headers: {
                    'Authorization': 'Bearer ' + adminToken
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.error("Error loading assignments:", jqXHR.status, jqXHR.statusText, jqXHR.responseJSON);
                    let errorMsg = 'خطأ في تحميل الواجبات.';
                    if (jqXHR.status === 401) {
                        // The error message sent by the server might not always be in the 'error' property.
                        if (typeof jqXHR.responseJSON === 'string' && jqXHR.responseJSON.includes("Unauthorized")) {
                            errorMsg = 'خطأ في المصادقة. يرجى تسجيل الدخول مرة أخرى.';
                        } else if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                            errorMsg = jqXHR.responseJSON.error;
                        } else {
                            errorMsg = 'خطأ في المصادقة. يرجى تسجيل الدخول مرة أخرى.';
                        }
                        // Add code to redirect to login:
                        // window.location.href = '/admin/login';
                    } else if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                        errorMsg = jqXHR.responseJSON.error;
                    } else if (jqXHR.statusText){
                        // Display the statusText provided by the server.
                        errorMsg = `Error: ${jqXHR.statusText}`;
                    }
                     $('#assignmentsTable tbody').html(`<tr><td colspan="6" class="text-center text-danger">${errorMsg}</td></tr>`);
                }
            },
            columns: [
                { data: 'title' },
                {
                    data: 'assignment_type',
                    render: function(data) {
                        return data === 'assignment' ? 'واجب' : (data === 'quiz' ? 'اختبار' : data);
                    }
                },
                {
                    data: 'due_date',
                    render: function(data) {
                        return data ? new Date(data).toLocaleString('ar-EG') : '-';
                    }
                },
                { data: 'max_points', defaultContent: '-' },
                {
                    data: null,
                    render: function(data, type, row) {
                        // Display associated files
                        let files = row.assignment_files;
                        let fileList = '';
                        if (files && files.length) {
                            fileList = '<ul class="list-unstyled">';
                            files.forEach(file => {
                                fileList += `<li><a href="${file.file_path}" target="_blank">${file.file_name}</a></li>`;
                            });
                            fileList += '</ul>';
                        } else {
                            fileList = 'لا يوجد ملفات';
                        }
                        return fileList;
                    }
                },
                {
                    data: null, // Use null for action buttons column
                    orderable: false, // Don't allow sorting on this column
                    render: function(data, type, row) { // Use row data
                        return `
                           <button class="btn btn-sm btn-primary" onclick="editAssignment(${row.id})" title="تعديل الواجب"><i class="fas fa-edit"></i> تعديل</button>
                        
                            <button class="btn btn-sm btn-info" onclick="viewSubmissions('${row.id}')" title="عرض التسليمات">
                            <i class="fas fa-eye"></i> التسليمات
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteAssignment('${row.id}')" title="حذف الواجب">
                                <i class="fas fa-trash"></i> حذف
                            </button>
                        `;
                    }
                },
            ],
            language: dataTableArabic,
            processing: true,
            serverSide: false, // Assuming data is small enough for client-side processing
            responsive: true
        });
    });


    // Removed createAssignment function as it's handled by the modal in the old template
    // If you need a separate create page, the button logic above handles the link

    function viewSubmissions(assignmentId) {
        $('#submissionsModal').modal('show');

        if (submissionsTable) {
            submissionsTable.destroy();
        }

        submissionsTable = $('#submissionsTable').DataTable({
            ajax: {
                // TODO: Need an API endpoint to get submissions for an assignment
                url: '#', // Placeholder - needs backend route e.g /api/courses/${window.courseId}/assignments/${assignmentId}/submissions
                dataSrc: '',
                // Add Authorization header
                headers: { 'Authorization': 'Bearer ' + adminToken }, // Add auth header
                error: function (jqXHR, textStatus, errorThrown) {
                     console.error("Error loading submissions:", textStatus, errorThrown);
                     $('#submissionsTable tbody').html('<tr><td colspan="5" class="text-center text-danger">خطأ في تحميل التسليمات.</td></tr>');
                 }
            },
            columns: [
                // TODO: Adjust data fields based on the actual API response for submissions
                { data: 'student_name', defaultContent: 'غير معروف' }, // Assuming API returns student name
                {
                    data: 'submitted_at',
                    render: function(data) {
                        return data ? new Date(data).toLocaleString('ar-EG') : '-';
                    }
                },
                {
                    data: 'status',
                    render: function(data) {
                        // Add more statuses if needed
                        if (data === 'graded') return '<span class="badge bg-success">تم التقييم</span>';
                        if (data === 'submitted') return '<span class="badge bg-warning text-dark">بإنتظار التقييم</span>';
                        if (data === 'late') return '<span class="badge bg-danger">متأخر</span>';
                        return data || '-';
                    }
                },
                { data: 'grade', defaultContent: '-' }, // Show '-' if grade is null/undefined
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        // TODO: Need submission ID from API response (assuming row.id)
                        return row.status === 'graded' ?
                            `<button class="btn btn-sm btn-secondary" disabled>تم التقييم</button>` :
                            `<button class="btn btn-sm btn-primary" onclick="showGradeForm('${row.id}')">تقييم</button>`;
                   }
                },
            ],
            language: dataTableArabic,
            processing: true,
            serverSide: false, // Adjust if using server-side processing for submissions
            responsive: true,
            searching: false, // Disable search for submissions table if not needed
            lengthChange: false // Disable length change for submissions table
        });
    }

    function showGradeForm(submissionId) {
        $('#submissionId').val(submissionId);
        // TODO: Optionally fetch current submission details to pre-fill form
        $('#gradeSubmissionModal').modal('show');
    }

    function gradeSubmission() {
        const submissionId = $('#submissionId').val();
        const grade = $('#submissionGrade').val();
        const feedback = $('#submissionFeedback').val();

        if (!grade) {
            alert('الرجاء إدخال الدرجة.');
            return;
        }

        const gradeData = { grade: grade, feedback: feedback };

        $.ajax({
            url: `/api/submissions/${submissionId}/grade`, // Corrected API endpoint
            method: 'PUT',
            contentType: 'application/json',
            headers: { 'Authorization': 'Bearer ' + adminToken }, // Add auth header
            data: JSON.stringify(gradeData),
            success: function() {
                submissionsTable.ajax.reload(null, false); // Reload without resetting page
                $('#gradeSubmissionModal').modal('hide');
                $('#gradeSubmissionForm')[0].reset();
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'حدث خطأ أثناء التقييم');
            }
        });
    }

    function deleteAssignment(assignmentId) {
        if (confirm('هل أنت متأكد من حذف هذا الواجب/الاختبار؟')) {
           $.ajax({
                url: `/api/courses/${window.courseId}/assignments/${assignmentId}`,
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + adminToken },
                success: function() {
                    assignmentsTable.ajax.reload(null, false);
                },
                error: function(xhr) {
                    alert(xhr.responseJSON?.error || 'حدث خطأ أثناء الحذف');
                }
            });
        }
    }

    function editAssignment(assignmentId){
        $.ajax({
            url: `/api/assignments/${assignmentId}`,
            method: 'GET',
            headers: { 'Authorization': 'Bearer ' + adminToken },
            success: function(assignment) {
                $('#editAssignmentTitle').val(assignment.title);
                $('#editAssignmentDescription').val(assignment.description);
                $('#editAssignmentForm').data('id', assignment.id);

                // Format due date for datetime-local input
                if (assignment.due_date) {
                    const dueDate = new Date(assignment.due_date);
                    // Adjust for local timezone before formatting
                    const offset = dueDate.getTimezoneOffset() * 60000; // Offset in milliseconds
                    const localDate = new Date(dueDate.getTime() - offset);
                    const formattedDate = localDate.toISOString().slice(0, 16); // YYYY-MM-DDTHH:MM
                    $('#editAssignmentDueDate').val(formattedDate);
                } else {
                    $('#editAssignmentDueDate').val('');
                }

                $('#editAssignmentMaxPoints').val(assignment.max_points);

                // Clear previous file list and display current ones
                const fileListContainer = $('#editCurrentFilesList');
                fileListContainer.empty(); // Clear previous list
                let files = assignment.assignment_files;
                if (files && files.length) {
                    let fileListHtml = '<p>الملفات الحالية:</p><ul class="list-unstyled">';
                    files.forEach(file => {
                        fileListHtml += `
                            <li id="file-${file.id}">
                                <a href="${file.file_path}" target="_blank">${file.file_name}</a> 
                                <button type="button" class="btn btn-sm btn-danger ms-2" onclick="deleteAssignmentFile(${assignment.id}, ${file.id})" title="حذف الملف">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </li>`;
                    });
                    fileListHtml += '</ul>';
                    fileListContainer.html(fileListHtml);
                } else {
                    fileListContainer.html('<p>لا يوجد ملفات مرفقة حالياً.</p>');
                }
                 // Reset the file input field for new uploads
                 $('#editUploadFiles').val(''); 

                $('#editAssignmentModal').modal('show');
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'حدث خطأ أثناء جلب بيانات الواجب.');
            }
        });
    }
    
    // Function to delete an individual file associated with an assignment
    function deleteAssignmentFile(assignmentId, fileId) {
        if (!confirm('هل أنت متأكد من حذف هذا الملف؟ لا يمكن التراجع عن هذا الإجراء.')) {
            return;
        }
        
        $.ajax({
            url: `/api/assignments/${assignmentId}/files/${fileId}`, 
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + adminToken },
            success: function() {
                alert('تم حذف الملف بنجاح.');
                // Remove the file entry from the list in the modal
                $(`#file-${fileId}`).remove();
                // Optionally, reload the main assignments table if file info is displayed there
                assignmentsTable.ajax.reload(null, false); 
            },
            error: function(xhr) {
                 alert(xhr.responseJSON?.error || 'حدث خطأ أثناء حذف الملف.');
            }
        });
    }


    function saveAssignmentChanges() {
        const assignmentId = $('#editAssignmentForm').data('id');
        // Use FormData to handle both text fields and file uploads
        const formData = new FormData($('#editAssignmentForm')[0]); 
    
        // Get other data manually if needed, though FormData should capture it
        // const title = $('#editAssignmentTitle').val();
        // formData.append('title', title); // Only needed if not captured automatically
        
         // Basic validation example (can be expanded)
        if (!formData.get('title')) {
             alert('الرجاء إدخال عنوان الواجب.');
            return;
        }

        $.ajax({
            url: `/api/assignments/${assignmentId}`, // Corrected endpoint to match editAssignment fetch
            method: 'PUT',
            contentType: false, // Important: Let jQuery/browser set Content-Type for FormData
            processData: false, // Important: Prevent jQuery from processing the FormData
            headers: { 'Authorization': 'Bearer ' + adminToken },
            data: formData, // Send FormData object
            success: function() {
                alert('تم تعديل الواجب بنجاح');
                assignmentsTable.ajax.reload(null, false); // Reload the table without resetting the page
                $('#editAssignmentModal').modal('hide');
                // Optionally clear the form after successful submission
                 $('#editAssignmentForm')[0].reset(); 
                 $('#editCurrentFilesList').empty(); // Clear the current files list area
            },
            error: function(xhr) {
                console.error("Save changes error:", xhr.status, xhr.statusText, xhr.responseJSON);
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    alert(xhr.responseJSON.error); // Corrected this line
                } else {
                    alert('حدث خطأ أثناء حفظ التغييرات.');
                }
            }
        });
    }
