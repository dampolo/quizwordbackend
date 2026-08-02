from vocabulary_app.models import UserLanguages

class UserLanguageStatus:
    @staticmethod
    def languages_active(user):
        user_languages = UserLanguages.objects.filter(user=user).first()

        if user_languages is None:
            return False

        return (
            user_languages.native_language is not None
            and user_languages.learning_languages.exists()
        )