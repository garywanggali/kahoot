from django.contrib import admin

from .models import Answer, Player, Question, Room, RoomQuestion

admin.site.register(Question)
admin.site.register(Room)
admin.site.register(RoomQuestion)
admin.site.register(Player)
admin.site.register(Answer)
