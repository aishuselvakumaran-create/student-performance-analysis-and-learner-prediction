from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', views.view_students, name='view_students'),
    path('admin/students/add/', views.add_student, name='add_student'),
    path('admin/students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('admin/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('admin/students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('admin/faculty/', views.view_faculty, name='view_faculty'),
    path('admin/faculty/add/', views.add_faculty, name='add_faculty'),
    path('admin/faculty/edit/<int:faculty_id>/', views.edit_faculty, name='edit_faculty'),
    path('admin/faculty/delete/<int:faculty_id>/', views.delete_faculty, name='delete_faculty'),
    path('admin/marklist/', views.admin_marklist, name='admin_marklist'),

    # Faculty
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/upload-scores/', views.upload_scores, name='upload_scores'),
    path('faculty/results/', views.faculty_results, name='faculty_results'),
    path('faculty/scores/edit/<int:score_id>/', views.edit_score, name='edit_score'),
    path('faculty/scores/delete/<int:score_id>/', views.delete_score, name='delete_score'),
    path('faculty/student/<int:student_id>/', views.faculty_student_detail, name='faculty_student_detail'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/marklist/', views.student_marklist, name='student_marklist'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),

    # ML Prediction
    path('predict/<int:student_id>/', views.predict_student_category, name='predict_category'),
    path('predict/chart-data/', views.prediction_chart_data, name='prediction_chart_data'),
    # CSV Import
path('admin/students/import-csv/', views.import_students_csv, name='import_students_csv'),
path('admin/students/sample-csv/', views.sample_students_csv, name='sample_students_csv'),
path('admin/faculty/import-csv/', views.import_faculty_csv, name='import_faculty_csv'),
path('admin/faculty/sample-csv/', views.sample_faculty_csv, name='sample_faculty_csv'),
path('faculty/upload-scores/csv/', views.import_scores_csv, name='import_scores_csv'),
path('faculty/upload-scores/sample-csv/', views.sample_scores_csv, name='sample_scores_csv'),
]