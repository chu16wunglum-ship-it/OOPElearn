from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('lesson/<int:lesson_id>/<str:kind>/manage/', views.quiz_manage, name='quiz_manage'),
    path('lesson/<int:lesson_id>/<str:kind>/question/add/', views.question_add, name='question_add'),
    path('question/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('lesson/<int:lesson_id>/<str:kind>/take/', views.quiz_take, name='quiz_take'),
    path('lesson/<int:lesson_id>/invideo/answer/', views.invideo_answer, name='invideo_answer'),
    path('attempt/<int:pk>/result/', views.attempt_result, name='attempt_result'),
    path('attempt/<int:pk>/ai-summary/', views.attempt_ai_summary, name='attempt_ai_summary'),
]
