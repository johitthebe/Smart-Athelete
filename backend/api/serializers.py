from rest_framework import serializers
from accounts.models import User  # your custom user model

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'password', 'role']
        read_only_fields = ['id', 'role']  # role is set later by choose-role

    def create(self, validated_data):
        user = User(**validated_data, role=role)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
