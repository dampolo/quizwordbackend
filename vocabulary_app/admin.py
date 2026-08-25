from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db import models
from django.forms import CheckboxSelectMultiple

from vocabulary_app.models import Language, UserLanguages, VocabularyCategory

admin.site.register(Language)
admin.site.register(VocabularyCategory)

@admin.register(UserLanguages)
class UserLanguagesAdmin(ModelAdmin):
    formfield_overrides = {
    models.ManyToManyField: {"widget": CheckboxSelectMultiple},
    }