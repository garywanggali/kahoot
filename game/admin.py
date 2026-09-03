from django.contrib import admin

from .models import (
    Answer,
    Player,
    Question,
    Room,
    RoomQuestion,
    Teacher,
    TeacherInviteCode,
)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('username', 'display_name', 'gender', 'is_active', 'created_at')
    search_fields = ('username', 'display_name')
    list_filter = ('is_active', 'gender')


@admin.register(TeacherInviteCode)
class TeacherInviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'max_uses', 'used_count', 'is_active', 'note', 'created_at')
    search_fields = ('code', 'note')
    list_filter = ('is_active',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'teacher', 'is_public', 'time_limit', 'created_at')
    list_filter = ('question_type', 'is_public')
    search_fields = ('text',)
    raw_id_fields = ('teacher',)


admin.site.register(Room)
admin.site.register(RoomQuestion)
admin.site.register(Player)
admin.site.register(Answer)
