from django.contrib import admin

from vocabulary_app.models import Language
from vocabulary_app.models import UserLanguages


admin.site.register(Language)
admin.site.register(UserLanguages)
