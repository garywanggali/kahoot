from django.shortcuts import redirect
from django.urls import path, re_path

from . import views


def _legacy_kahoot_redirect(request, rest=''):
    """Keep old /teacher/kahoot/... bookmarks working after Shoot rename."""
    target = '/teacher/shoot/'
    if rest:
        target += rest
    qs = request.META.get('QUERY_STRING')
    if qs:
        target = f'{target}?{qs}'
    return redirect(target, permanent=False)


urlpatterns = [
    path('', views.index, name='index'),
    path('join/', views.join_room, name='join_room'),
    path('play/<str:room_code>/', views.play, name='play'),
    path('practice/<str:practice_code>/', views.practice_play, name='practice_play'),
    path('practice/<str:practice_code>/start/', views.practice_start, name='practice_start'),
    path('practice/<str:practice_code>/answer/', views.practice_answer, name='practice_answer'),
    path('practice/<str:practice_code>/finish/', views.practice_finish, name='practice_finish'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/practice/', views.practice_assign, name='practice_assign'),
    path('teacher/settings/', views.teacher_settings, name='teacher_settings'),
    path('teacher/shoot/new/', views.shoot_new, name='shoot_new'),
    path('teacher/shoot/start/', views.shoot_start, name='shoot_start'),
    path('teacher/shoot/import/', views.shoot_import, name='shoot_import'),
    path('teacher/shoot/import/template/', views.shoot_import_template, name='shoot_import_template'),
    path('teacher/shoot/public/', views.shoot_public_list, name='shoot_public_list'),
    path('teacher/shoot/public/<int:pk>/preview/', views.shoot_public_preview, name='shoot_public_preview'),
    path('teacher/shoot/public/<int:pk>/clone/', views.shoot_public_clone, name='shoot_public_clone'),
    path('teacher/shoot/<int:pk>/edit/', views.shoot_editor, name='shoot_editor'),
    path('teacher/shoot/<int:pk>/meta/', views.shoot_editor_meta, name='shoot_editor_meta'),
    path('teacher/shoot/<int:pk>/questions/add/', views.shoot_question_add, name='shoot_question_add'),
    path('teacher/shoot/<int:pk>/questions/save/', views.shoot_question_save, name='shoot_question_save'),
    path('teacher/shoot/<int:pk>/questions/<int:qid>/delete/', views.shoot_question_delete_api, name='shoot_question_delete_api'),
    path('teacher/shoot/<int:pk>/', views.shoot_detail, name='shoot_detail'),
    path('teacher/shoot/<int:pk>/delete/', views.shoot_delete, name='shoot_delete'),
    path('teacher/shoot/<int:pk>/room/', views.shoot_create_room, name='shoot_create_room'),
    path('teacher/shoot/ai/', views.shoot_ai, name='shoot_ai'),
    path('teacher/shoot/ai/discard/', views.shoot_ai_discard, name='shoot_ai_discard'),
    # Legacy URL prefix compatibility
    re_path(r'^teacher/kahoot/(?P<rest>.*)$', _legacy_kahoot_redirect),
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
