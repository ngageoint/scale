from django.contrib.auth.models import User
from rest_framework import serializers


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'is_staff')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email',''),
            first_name=validated_data.get('first_name',''),
            last_name=validated_data.get('last_name',''),
            is_staff = validated_data.get('is_staff', False)
        )

        user.set_password(validated_data['password'])
        user.save()

        return user

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            if k == 'password':
                instance.set_password(v)
            else:
                setattr(instance, k, v)

        instance.save()

        return instance