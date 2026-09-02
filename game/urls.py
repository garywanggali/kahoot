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
    path('teacher/rooms/<int:pk>/reset/', views.room_reset, name='room_reset'),
    path('teacher/rooms/<int:pk>/', views.room_host, name='room_host'),
    path('api/room/<str:room_code>/state/', views.room_state_api, name='room_state_api'),
]
