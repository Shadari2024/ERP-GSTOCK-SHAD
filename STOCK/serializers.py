# serializers.py
from rest_framework import serializers
from .models import SystemeLicence

class LicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemeLicence
        fields = '__all__'
        read_only_fields = ('date_activation', 'date_expiration')

class GenerateLicenceSerializer(serializers.Serializer):
    email = serializers.EmailField()
    duration_days = serializers.IntegerField(default=30, min_value=1)
