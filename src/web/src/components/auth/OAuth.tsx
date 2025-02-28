import React, { useState } from 'react'; // ^18.2.0
import { FaGoogle, FaMicrosoft } from 'react-icons/fa'; // ^4.8.0
import { useAuth } from '../../hooks/useAuth';
import Button from '../../components/common/Button';
import { OAuthProvider } from '../../types/auth';

interface OAuthProps {
  className?: string;
  onSuccess?: () => void;
  onError?: (error: Error) => void;
  isProcessing?: boolean;
}

/**
 * Provides OAuth authentication buttons for social login with providers like Google and Microsoft
 * 
 * @param className - Optional CSS class for styling the container
 * @param onSuccess - Callback function executed after successful authentication
 * @param onError - Callback function executed when authentication fails
 * @param isProcessing - Flag to indicate if authentication is in progress
 */
const OAuth: React.FC<OAuthProps> = ({
  className = '',
  onSuccess,
  onError,
  isProcessing = false
}) => {
  // Get auth functionality from useAuth hook
  const { loginWithOAuth } = useAuth();
  
  // Track loading state for each provider independently
  const [loadingProvider, setLoadingProvider] = useState<OAuthProvider | null>(null);
  
  /**
   * Initiates the OAuth login process with the specified provider
   * 
   * @param provider - The OAuth provider to authenticate with
   * @param event - The click event from the button
   */
  const handleOAuthLogin = async (provider: OAuthProvider, event: React.MouseEvent) => {
    // Prevent default form submission behavior
    event.preventDefault();
    
    // Set loading state for the specific provider
    setLoadingProvider(provider);
    
    try {
      // Call loginWithOAuth from useAuth hook with the selected provider
      await loginWithOAuth(provider);
      
      // Handle success by calling onSuccess callback prop
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      // Handle errors by calling onError callback prop
      if (onError) {
        onError(error instanceof Error ? error : new Error('Authentication failed'));
      }
      console.error('OAuth login error:', error);
    } finally {
      // Reset loading state when complete
      setLoadingProvider(null);
    }
  };
  
  return (
    <div className={`oauth-providers space-y-3 ${className}`}>
      <Button 
        variant="secondary"
        isFullWidth
        leftIcon={<FaGoogle />}
        onClick={(e) => handleOAuthLogin(OAuthProvider.GOOGLE, e)}
        isLoading={loadingProvider === OAuthProvider.GOOGLE || isProcessing}
        disabled={loadingProvider !== null || isProcessing}
        aria-label="Continue with Google"
      >
        Continue with Google
      </Button>
      
      <Button 
        variant="secondary"
        isFullWidth
        leftIcon={<FaMicrosoft />}
        onClick={(e) => handleOAuthLogin(OAuthProvider.MICROSOFT, e)}
        isLoading={loadingProvider === OAuthProvider.MICROSOFT || isProcessing}
        disabled={loadingProvider !== null || isProcessing}
        aria-label="Continue with Microsoft"
      >
        Continue with Microsoft
      </Button>
    </div>
  );
};

export default OAuth;