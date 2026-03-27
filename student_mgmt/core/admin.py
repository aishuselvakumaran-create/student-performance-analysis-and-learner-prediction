from django.contrib import admin
from .models import User, Faculty, Student, Score, Notification

admin.site.register(User)
admin.site.register(Faculty)
admin.site.register(Student)
admin.site.register(Score)
admin.site.register(Notification)
