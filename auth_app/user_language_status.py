from vocabulary_app.models import UserLanguages

class UserLanguageStatus:
    @staticmethod
    def languages_active(user):
        try:
            user_languages = user.user_languages
        except UserLanguages.DoesNotExist:
            return False

        has_native = user_languages.native_language is not None
        has_learning = user_languages.learning_languages.exists()

        return has_native and has_learning