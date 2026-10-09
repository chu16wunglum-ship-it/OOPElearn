from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('pretest-import/', views.pretest_import, name='pretest_import'),
    path('lesson/<int:lesson_id>/<str:kind>/manage/', views.quiz_manage, name='quiz_manage'),
    path('lesson/<int:lesson_id>/<str:kind>/question/add/', views.question_add, name='question_add'),
    path('question/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('lesson/<int:lesson_id>/<str:kind>/take/', views.quiz_take, name='quiz_take'),
    path('lesson/<int:lesson_id>/invideo/answer/', views.invideo_answer, name='invideo_answer'),
    path('boss-battles/', views.boss_battle_hub, name='boss_battle_hub'),
    path('lesson/<int:lesson_id>/boss-battle/', views.boss_battle_play, name='boss_battle_play'),
    path('lesson/<int:lesson_id>/boss-battle/answer/', views.boss_battle_answer, name='boss_battle_answer'),
    path('lesson/<int:lesson_id>/boss-battle/finish/', views.boss_battle_finish, name='boss_battle_finish'),
    path('attempt/<int:pk>/result/', views.attempt_result, name='attempt_result'),
    path('attempt/<int:pk>/ai-summary/', views.attempt_ai_summary, name='attempt_ai_summary'),
]
