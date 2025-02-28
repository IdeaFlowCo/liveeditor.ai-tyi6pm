"""
Defines Marshmallow schemas for user data validation, serialization, and deserialization 
in the AI writing enhancement platform. These schemas support both authenticated and 
anonymous users, handling profile data, preferences, and account operations.
"""

import marshmallow as ma
from marshmallow import fields, validate, ValidationError

from ...core.utils.validators import is_valid_email, is_valid_password


class UserResponseSchema(ma.Schema):
    """Schema for serializing user data in API responses"""
    
    user_id = fields.String(dump_only=True)
    email = fields.Email()
    first_name = fields.String()
    last_name = fields.String()
    created_at = fields.DateTime(dump_only=True)
    last_login = fields.DateTime(dump_only=True)
    email_verified = fields.Boolean(dump_only=True)
    is_anonymous = fields.Boolean(dump_only=True)
    preferences = fields.Nested('UserPreferencesSchema', dump_only=True)
    
    class Meta:
        """Meta class for configuration"""
        exclude = ('password_hash',)


class UserProfileSchema(ma.Schema):
    """Schema for validating user profile information"""
    
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=50))
    
    class Meta:
        """Meta class for configuration"""
        # Marshmallow 3.x has strict validation by default


class UserUpdateSchema(ma.Schema):
    """Schema for validating user profile update requests"""
    
    first_name = fields.String(validate=validate.Length(min=1, max=50))
    last_name = fields.String(validate=validate.Length(min=1, max=50))
    
    class Meta:
        """Meta class for configuration"""
        partial = True
        unknown = ma.EXCLUDE


class UserPreferencesSchema(ma.Schema):
    """Schema for user preferences data"""
    
    theme = fields.String(validate=validate.OneOf(['light', 'dark', 'system']))
    font_size = fields.Integer(validate=validate.Range(min=8, max=24))
    default_prompt_categories = fields.List(fields.String())
    notification_settings = fields.Dict()
    privacy_settings = fields.Dict()


class UserPreferencesUpdateSchema(ma.Schema):
    """Schema for validating user preference updates"""
    
    theme = fields.String(validate=validate.OneOf(['light', 'dark', 'system']))
    font_size = fields.Integer(validate=validate.Range(min=8, max=24))
    default_prompt_categories = fields.List(fields.String())
    notification_settings = fields.Dict()
    privacy_settings = fields.Dict()
    
    class Meta:
        """Meta class for configuration"""
        partial = True
        unknown = ma.EXCLUDE


class ChangeEmailSchema(ma.Schema):
    """Schema for validating email change requests"""
    
    new_email = fields.Email(required=True, validate=lambda e: is_valid_email(e))
    current_password = fields.String(required=True)
    
    class Meta:
        """Meta class for configuration"""
        # Marshmallow 3.x has strict validation by default


class ChangePasswordSchema(ma.Schema):
    """Schema for validating password change requests"""
    
    current_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=lambda p: is_valid_password(p))
    confirm_password = fields.String(
        required=True,
        validate=validate.Equal(field='new_password', error='Passwords must match')
    )
    
    class Meta:
        """Meta class for configuration"""
        # Marshmallow 3.x has strict validation by default
    
    def validate_new_password(self, data):
        """
        Validates that new password meets strength requirements and differs from current
        
        Args:
            data: Schema data dictionary
            
        Returns:
            Validated data or raises ValidationError
        """
        if data.get('new_password') == data.get('current_password'):
            raise ValidationError(
                'New password must be different from current password',
                field_name='new_password'
            )
        
        # Password strength is already validated by the field validator
        return data