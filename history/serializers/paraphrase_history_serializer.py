from rest_framework import serializers

from history.models import ParaphraseHistory


class ParaphraseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParaphraseHistory
        exclude = ["display_name", "created_by"]
