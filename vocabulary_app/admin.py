from django.contrib import admin
from django.contrib.admin import ModelAdmin
from vocabulary_app.models import Language, UserLanguages, VocabularyCategory
from vocabulary_app.models import UserLanguages
from django.forms import CheckboxSelectMultiple
from django.db import models

admin.site.register(Language)
admin.site.register(VocabularyCategory)

@admin.register(UserLanguages)
class UserLanguagesAdmin(ModelAdmin):
    formfield_overrides = {
    models.ManyToManyField: {"widget": CheckboxSelectMultiple},
    }