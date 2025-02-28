"""
Defines Marshmallow schemas for authentication-related requests and responses in the AI 
writing enhancement platform, including user login, registration, token refresh, 
password reset, and anonymous session conversion. These schemas provide validation,
serialization, and deserialization of authentication data.
"""

import marshmallow as ma
from marshmallow import fields, validate, ValidationError
from ...core.utils.validators import is_valid_email, is_valid_password


class LoginSchema(ma.Schema):
    """Schema for validating user login requests"""
    
    email = fields.Email(
        required=True, 
        error_messages={"required": "Email is required."}
    )
    password = fields.String(
        required=True,
        error_messages={"required": "Password is required."},
        validate=validate.Length(min=8, max=100)
    )


class RegisterSchema(ma.Schema):
    """Schema for validating user registration requests"""
    
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required."}
    )
    password = fields.String(
        required=True,
        error_messages={"required": "Password is required."},
        validate=lambda p: is_valid_password(p) or "Password does not meet security requirements."
    )
    first_name = fields.String(
        required=True,
        error_messages={"required": "First name is required."},
        validate=validate.Length(min=1, max=50)
    )
    last_name = fields.String(
        required=True,
        error_messages={"required": "Last name is required."},
        validate=validate.Length(min=1, max=50)
    )


class TokenResponseSchema(ma.Schema):
    """Schema for serializing authentication token responses"""
    
    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)
    token_type = fields.String(default="bearer")
    expires_in = fields.Integer(required=True)
    user_id = fields.String(required=True)


class RefreshTokenSchema(ma.Schema):
    """Schema for validating token refresh requests"""
    
    refresh_token = fields.String(
        required=True,
        error_messages={"required": "Refresh token is required."}
    )


class PasswordResetRequestSchema(ma.Schema):
    """Schema for validating password reset requests"""
    
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required."}
    )


class PasswordResetConfirmSchema(ma.Schema):
    """Schema for validating password reset confirmation"""
    
    token = fields.String(
        required=True,
        error_messages={"required": "Token is required."}
    )
    new_password = fields.String(
        required=True,
        error_messages={"required": "New password is required."},
        validate=lambda p: is_valid_password(p) or "Password does not meet security requirements."
    )


class EmailVerificationSchema(ma.Schema):
    """Schema for validating email verification requests"""
    
    token = fields.String(
        required=True,
        error_messages={"required": "Token is required."}
    )


class AnonymousSessionSchema(ma.Schema):
    """Schema for representing anonymous session data"""
    
    session_id = fields.String(required=True)
    expires_at = fields.DateTime(required=True)


class AnonymousSessionConversionSchema(ma.Schema):
    """Schema for converting anonymous sessions to registered accounts"""
    
    session_id = fields.String(required=True)
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required."}
    )
    password = fields.String(
        required=True,
        error_messages={"required": "Password is required."},
        validate=lambda p: is_valid_password(p) or "Password does not meet security requirements."
    )
    first_name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=50)
    )
    last_name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=50)
    )