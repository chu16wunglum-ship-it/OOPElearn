from django.urls import path

from . import views

app_name = 'courses'

urlpatterns = [
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('create/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('<int:pk>/roster/', views.course_roster, name='course_roster'),
    path('<int:pk>/report/', views.course_report, name='course_report'),
    path('<int:course_pk>/students/<int:student_id>/report/', views.student_report, name='student_report'),
    path('<int:course_pk>/students/<int:student_id>/ai-summary/', views.student_ai_summary, name='student_ai_summary'),
    path('<int:course_pk>/lessons/add/', views.lesson_create, name='lesson_create'),
    path('lessons/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:pk>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lessons/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('lessons/<int:pk>/progress/', views.update_video_progress, name='update_video_progress'),
    path('lessons/<int:pk>/board/', views.lesson_board, name='lesson_board'),
    path('lessons/<int:pk>/ai-chat/', views.lesson_ai_ask, name='lesson_ai_ask'),
]
