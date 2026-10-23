from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    # We need to make sure passwords are hidden and confirmed
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'middle_name', 'last_name', 'date_of_birth', 'phone_number', 'role', 'password']
    
    def create(self, validated_data):
        # This automatically hashes the password securely in the database
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            middle_name=validated_data.get('middle_name', ''),
            last_name=validated_data['last_name'],
            date_of_birth=validated_data.get('date_of_birth'),
            phone_number=validated_data.get('phone_number', ''),
            role=validated_data['role'],
            password=validated_data['password']
        )
        return user