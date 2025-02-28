import React, { useState, useEffect, useCallback } from 'react'; // React v18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.15.0
import MainLayout from '../components/layout/MainLayout';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Card from '../components/common/Card';
import Alert from '../components/common/Alert';
import { Tabs, Tab } from '../components/common/Tabs';
import useAuth, { useAuth as useAuthHook } from '../hooks/useAuth';
import {
  getUserProfile,
  updateUserProfile,
  getUserPreferences,
  updateUserPreferences,
  changeEmail,
  changePassword,
  uploadProfileImage,
  deleteAccount,
} from '../api/user';
import { useTheme } from '../contexts/ThemeContext';
import {
  UserProfile,
  UserPreferences,
  UserUpdateRequest,
  UserPreferencesUpdateRequest,
  ChangeEmailRequest,
  ChangePasswordRequest,
  NotificationPreferences,
  PrivacySettings,
} from '../types/user';

/**
 * Main settings page component with tabbed interface for different settings categories
 * @returns {JSX.Element} Rendered Settings page
 */
const Settings: React.FC = () => {
  // LD1: Initialize state variables for profile data, preferences, form submission state, and alerts
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [alert, setAlert] = useState<{ message: string; type: string } | null>(null);

  // IE3: Get user authentication data and methods from useAuth hook
  const { user, logout } = useAuth();

  // IE3: Get theme information and methods from useTheme hook
  const { theme, setTheme } = useTheme();

  // IE3: Hook for programmatic navigation
  const navigate = useNavigate();

  /**
   * Implement handleProfileUpdate function to update user profile information
   * @param {UserUpdateRequest} data - The updated user profile data
   * @returns {Promise<void>}
   */
  const handleProfileUpdate = async (data: UserUpdateRequest) => {
    setIsLoading(true);
    try {
      const updatedProfile = await updateUserProfile(data);
      setProfile(updatedProfile);
      setAlert({ message: 'Profile updated successfully!', type: 'success' });
    } catch (error: any) {
      setAlert({ message: error.message || 'Failed to update profile.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Implement handlePasswordChange function to update user password
   * @param {ChangePasswordRequest} data - The password change request data
   * @returns {Promise<void>}
   */
  const handlePasswordChange = async (data: ChangePasswordRequest) => {
    setIsLoading(true);
    try {
      await changePassword(data);
      setAlert({ message: 'Password changed successfully!', type: 'success' });
    } catch (error: any) {
      setAlert({ message: error.message || 'Failed to change password.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Implement handleEmailChange function to update user email
   * @param {ChangeEmailRequest} data - The email change request data
   * @returns {Promise<void>}
   */
  const handleEmailChange = async (data: ChangeEmailRequest) => {
    setIsLoading(true);
    try {
      await changeEmail(data);
      setAlert({ message: 'Email changed successfully! Please verify your new email address.', type: 'success' });
    } catch (error: any) {
      setAlert({ message: error.message || 'Failed to change email.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Implement handlePreferencesUpdate function to update user preferences
   * @param {UserPreferencesUpdateRequest} data - The user preferences update request data
   * @returns {Promise<void>}
   */
  const handlePreferencesUpdate = async (data: UserPreferencesUpdateRequest) => {
    setIsLoading(true);
    try {
      const updatedPreferences = await updateUserPreferences(data);
      setPreferences(updatedPreferences);
      setAlert({ message: 'Preferences updated successfully!', type: 'success' });
    } catch (error: any) {
      setAlert({ message: error.message || 'Failed to update preferences.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Implement handleThemeChange function to update application theme
   * @param {string} newTheme - The new theme to apply
   * @returns {void}
   */
  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
  };

  /**
   * Implement handleAccountDeletion function to delete user account
   * @param {string} password - The user's password for verification
   * @returns {Promise<void>}
   */
  const handleAccountDeletion = async (password: string) => {
    setIsLoading(true);
    try {
      await deleteAccount({ password });
      setAlert({ message: 'Account deleted successfully!', type: 'success' });
      logout();
      navigate('/');
    } catch (error: any) {
      setAlert({ message: error.message || 'Failed to delete account.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Implement handleProfileImageUpload function to update profile image
   * @param {File} imageFile - The profile image file to upload
   * @returns {Promise<void>}
   */
  const handleProfileImageUpload = async (imageFile: File) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      const { imageUrl } = await uploadProfileImage(formData);
      setProfile({ ...profile, profileImage: imageUrl } as UserProfile);
      setAlert({ message: 'Profile image updated successfully!', type: 'success' });
    } catch (error: any) {
      setAlert({ message: error.message || 'Failed to upload profile image.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // IE1: Create useEffect to fetch user profile data when component mounts
  useEffect(() => {
    const fetchProfile = async () => {
      setIsLoading(true);
      try {
        const userProfile = await getUserProfile();
        setProfile(userProfile);
      } catch (error: any) {
        setAlert({ message: error.message || 'Failed to load profile.', type: 'error' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // IE1: Create useEffect to fetch user preferences when component mounts
  useEffect(() => {
    const fetchPreferences = async () => {
      setIsLoading(true);
      try {
        const userPreferences = await getUserPreferences();
        setPreferences(userPreferences);
      } catch (error: any) {
        setAlert({ message: error.message || 'Failed to load preferences.', type: 'error' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  // LD1: Return MainLayout component with tabs for different settings categories
  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-semibold mb-4">Settings</h1>

        {alert && <Alert message={alert.message} type={alert.type} />}

        <Tabs>
          <Tab label="Profile">
            <ProfileTab profile={profile} isLoading={isLoading} onUpdate={handleProfileUpdate} onImageUpload={handleProfileImageUpload} />
          </Tab>
          <Tab label="Security">
            <SecurityTab email={profile?.email || ''} isLoading={isLoading} onPasswordChange={handlePasswordChange} onEmailChange={handleEmailChange} />
          </Tab>
          <Tab label="Appearance">
            <AppearanceTab preferences={preferences} currentTheme={theme} isLoading={isLoading} onThemeChange={handleThemeChange} onPreferencesUpdate={handlePreferencesUpdate} />
          </Tab>
          <Tab label="Notifications">
            <NotificationsTab preferences={preferences} isLoading={isLoading} onUpdate={handlePreferencesUpdate} />
          </Tab>
          <Tab label="Privacy">
            <PrivacyTab preferences={preferences} isLoading={isLoading} onUpdate={handlePreferencesUpdate} />
          </Tab>
          <Tab label="Account">
            <AccountTab isLoading={isLoading} onDeleteAccount={handleAccountDeletion} />
          </Tab>
        </Tabs>
      </div>
    </MainLayout>
  );
};

interface ProfileTabProps {
  profile: UserProfile | null;
  isLoading: boolean;
  onUpdate: (data: UserUpdateRequest) => void;
  onImageUpload: (imageFile: File) => void;
}

/**
 * Tab component for managing user profile information
 * @param {ProfileTabProps} props - The props for the ProfileTab component
 * @returns {JSX.Element} Profile settings tab content
 */
const ProfileTab: React.FC<ProfileTabProps> = ({ profile, isLoading, onUpdate, onImageUpload }) => {
  // LD1: Create form for editing first name, last name, and profile image
  const [firstName, setFirstName] = useState(profile?.firstName || '');
  const [lastName, setLastName] = useState(profile?.lastName || '');
  const [imagePreview, setImagePreview] = useState(profile?.profileImage || '');

  // LD1: Implement image upload preview and functionality
  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImagePreview(URL.createObjectURL(file));
      onImageUpload(file);
    }
  };

  // LD1: Add validation for form fields
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onUpdate({ firstName, lastName });
  };

  // LD1: Provide save button to submit profile changes
  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">
            First Name
          </label>
          <Input
            type="text"
            id="firstName"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="mb-4">
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">
            Last Name
          </label>
          <Input
            type="text"
            id="lastName"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="mb-4">
          <label htmlFor="profileImage" className="block text-sm font-medium text-gray-700">
            Profile Image
          </label>
          <Input
            type="file"
            id="profileImage"
            accept="image/*"
            onChange={handleImageChange}
            disabled={isLoading}
          />
          {imagePreview && (
            <img src={imagePreview} alt="Profile Preview" className="mt-2 rounded-full w-20 h-20 object-cover" />
          )}
        </div>
        <Button type="submit" variant="primary" disabled={isLoading}>
          Save Profile
        </Button>
      </form>
    </Card>
  );
};

interface SecurityTabProps {
  email: string;
  isLoading: boolean;
  onPasswordChange: (data: ChangePasswordRequest) => void;
  onEmailChange: (data: ChangeEmailRequest) => void;
}

/**
 * Tab component for managing security settings like password and email
 * @param {SecurityTabProps} props - The props for the SecurityTab component
 * @returns {JSX.Element} Security settings tab content
 */
const SecurityTab: React.FC<SecurityTabProps> = ({ email, isLoading, onPasswordChange, onEmailChange }) => {
  // LD1: Create password change form with current and new password fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // LD1: Create email change form with new email and password verification
  const [newEmail, setNewEmail] = useState('');
  const [passwordVerification, setPasswordVerification] = useState('');

  // LD1: Add validation for password complexity and email format
  const handlePasswordSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (newPassword === confirmPassword) {
      onPasswordChange({ currentPassword, newPassword, confirmPassword });
    } else {
      // TODO: Implement password mismatch error
    }
  };

  const handleEmailSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onEmailChange({ newEmail, password: passwordVerification });
  };

  // LD1: Add separate submit buttons for each form section
  return (
    <Card>
      <form onSubmit={handlePasswordSubmit}>
        <h4 className="text-lg font-semibold mb-4">Change Password</h4>
        <div className="mb-4">
          <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
            Current Password
          </label>
          <Input
            type="password"
            id="currentPassword"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="mb-4">
          <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
            New Password
          </label>
          <Input
            type="password"
            id="newPassword"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="mb-4">
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
            Confirm New Password
          </label>
          <Input
            type="password"
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <Button type="submit" variant="primary" disabled={isLoading}>
          Change Password
        </Button>
      </form>

      <form onSubmit={handleEmailSubmit} className="mt-8">
        <h4 className="text-lg font-semibold mb-4">Change Email</h4>
        <div className="mb-4">
          <label htmlFor="newEmail" className="block text-sm font-medium text-gray-700">
            New Email
          </label>
          <Input
            type="email"
            id="newEmail"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="mb-4">
          <label htmlFor="passwordVerification" className="block text-sm font-medium text-gray-700">
            Password Verification
          </label>
          <Input
            type="password"
            id="passwordVerification"
            value={passwordVerification}
            onChange={(e) => setPasswordVerification(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <Button type="submit" variant="primary" disabled={isLoading}>
          Change Email
        </Button>
      </form>
    </Card>
  );
};

interface AppearanceTabProps {
  preferences: UserPreferences | null;
  currentTheme: string;
  isLoading: boolean;
  onThemeChange: (theme: string) => void;
  onPreferencesUpdate: (data: UserPreferencesUpdateRequest) => void;
}

/**
 * Tab component for customizing UI appearance settings
 * @param {AppearanceTabProps} props - The props for the AppearanceTab component
 * @returns {JSX.Element} Appearance settings tab content
 */
const AppearanceTab: React.FC<AppearanceTabProps> = ({ preferences, currentTheme, isLoading, onThemeChange, onPreferencesUpdate }) => {
  // LD1: Create theme selection controls (light, dark, system)
  const handleThemeSelect = (newTheme: string) => {
    onThemeChange(newTheme);
  };

  // LD1: Add font size adjustment controls
  const handleFontSizeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newFontSize = parseInt(event.target.value);
    onPreferencesUpdate({ fontSize: newFontSize });
  };

  // LD1: Add editor preference options
  // LD1: Provide save button to apply appearance changes
  return (
    <Card>
      <h4 className="text-lg font-semibold mb-4">Theme</h4>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700">
          Select Theme
        </label>
        <div className="mt-2">
          <Button
            variant={currentTheme === 'light' ? 'primary' : 'secondary'}
            onClick={() => handleThemeSelect('light')}
            disabled={isLoading}
          >
            Light
          </Button>
          <Button
            variant={currentTheme === 'dark' ? 'primary' : 'secondary'}
            onClick={() => handleThemeSelect('dark')}
            disabled={isLoading}
            className="ml-2"
          >
            Dark
          </Button>
          <Button
            variant={currentTheme === 'system' ? 'primary' : 'secondary'}
            onClick={() => handleThemeSelect('system')}
            disabled={isLoading}
            className="ml-2"
          >
            System
          </Button>
        </div>
      </div>

      <h4 className="text-lg font-semibold mb-4">Font Size</h4>
      <div className="mb-4">
        <label htmlFor="fontSize" className="block text-sm font-medium text-gray-700">
          Adjust Font Size
        </label>
        <Input
          type="range"
          id="fontSize"
          min="12"
          max="24"
          step="1"
          value={preferences?.fontSize || 16}
          onChange={handleFontSizeChange}
          disabled={isLoading}
        />
      </div>
    </Card>
  );
};

interface NotificationsTabProps {
  preferences: UserPreferences | null;
  isLoading: boolean;
  onUpdate: (data: UserPreferencesUpdateRequest) => void;
}

/**
 * Tab component for managing notification preferences
 * @param {NotificationsTabProps} props - The props for the NotificationsTab component
 * @returns {JSX.Element} Notification settings tab content
 */
const NotificationsTab: React.FC<NotificationsTabProps> = ({ preferences, isLoading, onUpdate }) => {
  // LD1: Create toggles for different notification types (email, document updates, etc.)
  const [emailNotifications, setEmailNotifications] = useState(preferences?.notificationSettings?.email || false);
  const [documentUpdates, setDocumentUpdates] = useState(preferences?.notificationSettings?.documentUpdates || false);
  const [marketingEmails, setMarketingEmails] = useState(preferences?.notificationSettings?.marketing || false);

  // LD1: Group related notification settings into logical sections
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onUpdate({
      notificationSettings: {
        email: emailNotifications,
        documentUpdates: documentUpdates,
        marketing: marketingEmails,
      },
    });
  };

  // LD1: Provide save button to apply notification changes
  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <h4 className="text-lg font-semibold mb-4">Email Notifications</h4>
        <div className="mb-4">
          <label className="inline-flex items-center">
            <Input
              type="checkbox"
              checked={emailNotifications}
              onChange={(e) => setEmailNotifications(e.target.checked)}
              disabled={isLoading}
            />
            <span className="ml-2">Receive general email notifications</span>
          </label>
        </div>

        <h4 className="text-lg font-semibold mb-4">Document Updates</h4>
        <div className="mb-4">
          <label className="inline-flex items-center">
            <Input
              type="checkbox"
              checked={documentUpdates}
              onChange={(e) => setDocumentUpdates(e.target.checked)}
              disabled={isLoading}
            />
            <span className="ml-2">Notify me about document updates</span>
          </label>
        </div>

        <h4 className="text-lg font-semibold mb-4">Marketing Emails</h4>
        <div className="mb-4">
          <label className="inline-flex items-center">
            <Input
              type="checkbox"
              checked={marketingEmails}
              onChange={(e) => setMarketingEmails(e.target.checked)}
              disabled={isLoading}
            />
            <span className="ml-2">Receive marketing emails and promotions</span>
          </label>
        </div>

        <Button type="submit" variant="primary" disabled={isLoading}>
          Save Notifications
        </Button>
      </form>
    </Card>
  );
};

interface PrivacyTabProps {
  preferences: UserPreferences | null;
  isLoading: boolean;
  onUpdate: (data: UserPreferencesUpdateRequest) => void;
}

/**
 * Tab component for managing privacy and data settings
 * @param {PrivacyTabProps} props - The props for the PrivacyTab component
 * @returns {JSX.Element} Privacy settings tab content
 */
const PrivacyTab: React.FC<PrivacyTabProps> = ({ preferences, isLoading, onUpdate }) => {
  // LD1: Create toggles for data collection preferences
  const [dataCollection, setDataCollection] = useState(preferences?.privacySettings?.dataCollection || false);
  const [aiModelTraining, setAiModelTraining] = useState(preferences?.privacySettings?.aiModelTraining || false);
  const [shareUsageStatistics, setShareUsageStatistics] = useState(preferences?.privacySettings?.shareUsageStatistics || false);

  // LD1: Add controls for AI model training participation
  // LD1: Add usage statistics sharing options
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onUpdate({
      privacySettings: {
        dataCollection: dataCollection,
        aiModelTraining: aiModelTraining,
        shareUsageStatistics: shareUsageStatistics,
      },
    });
  };

  // LD1: Provide clear explanations of each privacy setting
  // LD1: Include save button to apply privacy changes
  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <h4 className="text-lg font-semibold mb-4">Data Collection</h4>
        <div className="mb-4">
          <label className="inline-flex items-center">
            <Input
              type="checkbox"
              checked={dataCollection}
              onChange={(e) => setDataCollection(e.target.checked)}
              disabled={isLoading}
            />
            <span className="ml-2">Allow collection of usage data to improve the application</span>
          </label>
        </div>

        <h4 className="text-lg font-semibold mb-4">AI Model Training</h4>
        <div className="mb-4">
          <label className="inline-flex items-center">
            <Input
              type="checkbox"
              checked={aiModelTraining}
              onChange={(e) => setAiModelTraining(e.target.checked)}
              disabled={isLoading}
            />
            <span className="ml-2">Allow my documents to be used for AI model training (anonymized)</span>
          </label>
        </div>

        <h4 className="text-lg font-semibold mb-4">Usage Statistics Sharing</h4>
        <div className="mb-4">
          <label className="inline-flex items-center">
            <Input
              type="checkbox"
              checked={shareUsageStatistics}
              onChange={(e) => setShareUsageStatistics(e.target.checked)}
              disabled={isLoading}
            />
            <span className="ml-2">Share anonymized usage statistics with third parties</span>
          </label>
        </div>

        <Button type="submit" variant="primary" disabled={isLoading}>
          Save Privacy Settings
        </Button>
      </form>
    </Card>
  );
};

interface AccountTabProps {
  isLoading: boolean;
  onDeleteAccount: (password: string) => void;
}

/**
 * Tab component for account management including deletion
 * @param {AccountTabProps} props - The props for the AccountTab component
 * @returns {JSX.Element} Account management tab content
 */
const AccountTab: React.FC<AccountTabProps> = ({ isLoading, onDeleteAccount }) => {
  // LD1: Display account information summary
  const [password, setPassword] = useState('');

  // LD1: Add account deletion section with confirmation flow
  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      onDeleteAccount(password);
    }
  };

  // LD1: Implement password verification for sensitive operations
  // LD1: Include clear warnings about data loss from account deletion
  return (
    <Card>
      <h4 className="text-lg font-semibold mb-4">Account Deletion</h4>
      <p className="mb-4">
        Deleting your account will permanently remove all your data, including documents and settings.
      </p>
      <div className="mb-4">
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Enter Password to Confirm
        </label>
        <Input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
        />
      </div>
      <Button variant="danger" onClick={handleDeleteAccount} disabled={isLoading}>
        Delete Account
      </Button>
    </Card>
  );
};

// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default Settings;