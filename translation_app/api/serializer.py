from rest_framework import serializers


class TranslateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000)
    source = serializers.ChoiceField(choices=["de", "en", "es"])
    target = serializers.ChoiceField(choices=["de", "en", "es"])
