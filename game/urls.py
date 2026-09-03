from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('join/', views.join_room, name='join_room'),
    path('play/<str:room_code>/', views.play, name='play'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/kahoot/new/', views.kahoot_new, name='kahoot_new'),
    path('teacher/kahoot/start/', views.kahoot_start, name='kahoot_start'),
    path('teacher/kahoot/import/', views.kahoot_import, name='kahoot_import'),
    path('teacher/kahoot/import/template/', views.kahoot_import_template, name='kahoot_import_template'),
    path('teacher/kahoot/public/', views.kahoot_public_list, name='kahoot_public_list'),
    path('teacher/kahoot/public/<int:pk>/clone/', views.kahoot_public_clone, name='kahoot_public_clone'),
    path('teacher/kahoot/<int:pk>/edit/', views.kahoot_editor, name='kahoot_editor'),
    path('teacher/kahoot/<int:pk>/meta/', views.kahoot_editor_meta, name='kahoot_editor_meta'),
    path('teacher/kahoot/<int:pk>/questions/add/', views.kahoot_question_add, name='kahoot_question_add'),
    path('teacher/kahoot/<int:pk>/questions/save/', views.kahoot_question_save, name='kahoot_question_save'),
    path('teacher/kahoot/<int:pk>/questions/<int:qid>/delete/', views.kahoot_question_delete_api, name='kahoot_question_delete_api'),
    path('teacher/kahoot/<int:pk>/', views.kahoot_detail, name='kahoot_detail'),
    path('teacher/kahoot/<int:pk>/delete/', views.kahoot_delete, name='kahoot_delete'),
    path('teacher/kahoot/<int:pk>/room/', views.kahoot_create_room, name='kahoot_create_room'),
    path('teacher/kahoot/ai/', views.kahoot_ai, name='kahoot_ai'),
    path('teacher/kahoot/ai/discard/', views.kahoot_ai_discard, name='kahoot_ai_discard'),
    path('teacher/questions/', views.question_list, name='question_list'),
    path('teacher/questions/create/', views.question_create, name='question_create'),
    path('teacher/questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('teacher/questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('teacher/rooms/create/', views.room_create, name='room_create'),
    path('teacher/rooms/<int:pk>/', views.room_host, name='room_host'),
    path('teacher/rooms/<int:pk>/analytics/', views.room_analytics_page, name='room_analytics_page'),
    path('teacher/rooms/<int:pk>/analytics/data/', views.room_analytics_data, name='room_analytics_data'),
    path('api/room/<str:room_code>/state/', views.room_state_api, name='room_state_api'),
]
