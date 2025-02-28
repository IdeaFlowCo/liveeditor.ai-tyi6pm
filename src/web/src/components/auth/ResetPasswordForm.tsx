import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../../common/Button';
import Input from '../../common/Input';
import Alert from '../../common/Alert';
import { resetPassword } from '../../../api/auth';
import { ROUTES } from '../../../constants/routes';

interface ResetPasswordFormProps {
  token: string;
  onSubmit: (password: string, confirmPassword: string) => Promise<void>;
  loading?: boolean;
}

const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({
  token,
  onSubmit,
  loading = false
}) => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    password?: string;
    confirmPassword?: string;
    general?: string;
  }>({});
  const [passwordStrength, setPasswordStrength] = useState(0);
  const navigate = useNavigate();

  // Update password strength when password changes
  useEffect(() => {
    calculatePasswordStrength();
  }, [password]);

  // Calculate the strength of the entered password
  const calculatePasswordStrength = () => {
    if (!password) {
      setPasswordStrength(0);
      return;
    }
    
    let strength = 0;
    
    // Length check
    if (password.length >= 10) strength += 1;
    
    // Complexity checks
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/\d/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    setPasswordStrength(Math.min(4, strength));
  };

  // Get password strength label and color
  const getPasswordStrengthInfo = () => {
    const labels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
    const colors = [
      'bg-red-500',
      'bg-orange-500',
      'bg-yellow-500',
      'bg-green-500',
      'bg-green-700'
    ];
    
    return {
      label: passwordStrength > 0 ? labels[passwordStrength - 1] : 'Too Weak',
      color: passwordStrength > 0 ? colors[passwordStrength - 1] : 'bg-gray-200'
    };
  };

  // Validate the password meets requirements
  const validatePassword = () => {
    const newErrors: {
      password?: string;
      confirmPassword?: string;
    } = {};
    
    // Check minimum length
    if (password.length < 10) {
      newErrors.password = 'Password must be at least 10 characters long';
    }
    
    // Check complexity
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasDigit = /\d/.test(password);
    const hasSpecialChar = /[^A-Za-z0-9]/.test(password);
    
    if (!(hasUppercase && hasLowercase && hasDigit && hasSpecialChar)) {
      newErrors.password = 'Password must include uppercase, lowercase, number, and special character';
    }
    
    // Check passwords match
    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validatePassword()) {
      try {
        await onSubmit(password, confirmPassword);
      } catch (error: any) {
        setErrors({
          general: error.message || 'Failed to reset password. Please try again later.'
        });
      }
    }
  };

  const strengthInfo = getPasswordStrengthInfo();

  return (
    <div className="w-full max-w-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Reset Your Password</h2>
      
      {errors.general && (
        <Alert
          variant="error"
          message={errors.general}
          className="mb-4"
        />
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="New Password"
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          helperText="Must be at least 10 characters with uppercase, lowercase, number, and special character"
          fullWidth
          autoComplete="new-password"
          required
        />
        
        {/* Password Strength Indicator */}
        {password && (
          <div className="mb-2">
            <div className="flex justify-between mb-1">
              <span className="text-sm">Password Strength:</span>
              <span className="text-sm font-medium">{strengthInfo.label}</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className={`h-full ${strengthInfo.color} transition-all duration-300`} 
                style={{ width: `${(passwordStrength / 4) * 100}%` }}
              ></div>
            </div>
          </div>
        )}
        
        <Input
          label="Confirm Password"
          type="password"
          id="confirm-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={errors.confirmPassword}
          fullWidth
          autoComplete="new-password"
          required
        />
        
        <Button
          type="submit"
          isLoading={loading}
          isFullWidth
        >
          Reset Password
        </Button>
        
        <div className="text-center mt-4">
          <Link 
            to={ROUTES.LOGIN} 
            className="text-[#2C6ECB] hover:text-[#2C6ECB]/80 text-sm"
          >
            Back to Login
          </Link>
        </div>
      </form>
    </div>
  );
};

export default ResetPasswordForm;