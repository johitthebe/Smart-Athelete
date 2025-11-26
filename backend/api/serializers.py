from rest_framework import serializers
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'password', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role')  # <- make sure role is used
        user = User(**validated_data, role=role)  # set role here
        user.set_password(password)
        user.save()
        return user
