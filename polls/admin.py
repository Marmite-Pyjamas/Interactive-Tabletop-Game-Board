from django.contrib import admin
from .models import Question, Cord

# Admin file, handles created models and registers them to database

# Question was used in testing, Cord is relevant to project
admin.site.register(Question)
admin.site.register(Cord)
