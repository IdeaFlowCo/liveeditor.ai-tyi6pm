import React from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.10.0
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { Modal } from '../common/Modal';
import { useAuth } from '../../hooks/useAuth';

// Define a global constant for the default message
const DEFAULT_MESSAGE =
  "You're currently using the application anonymously. Your work is only saved in this browser session and will be lost when you close the browser.";

// Define the props for the AnonymousWarning component
interface AnonymousWarningProps {
  message?: string;
  asModal?: boolean;
  isVisible?: boolean;
  onClose?: () => void;
  className?: string;
  children?: React.ReactNode;
}

/**
 * A functional component that displays a warning to anonymous users about the limitations of anonymous usage
 * @param {AnonymousWarningProps} props - props
 * @returns {JSX.Element} The rendered component
 */
const AnonymousWarning: React.FC<AnonymousWarningProps> = ({
  message = DEFAULT_MESSAGE,
  asModal = false,
  isVisible = true,
  onClose,
  className,
  children,
}) => {
  // Get the navigation function from react-router-dom
  const navigate = useNavigate();

  // Use the useAuth hook to get authentication functions
  const { setRedirectUrl } = useAuth();

  // Define a handler function for the register button click
  const handleRegisterClick = () => {
    // Set the redirect URL to the current URL
    setRedirectUrl(window.location.pathname);
    // Navigate to the register page
    navigate('/register');
  };

  // Define a handler function for the login button click
  const handleLoginClick = () => {
    // Set the redirect URL to the current URL
    setRedirectUrl(window.location.pathname);
    // Navigate to the login page
    navigate('/login');
  };

  // Conditionally render either an Alert or Modal component based on the asModal prop
  if (asModal) {
    return (
      <Modal
        isOpen={isVisible}
        onClose={onClose || (() => {})}
        title="Anonymous Usage Warning"
      >
        <div className="p-4">
          <p className="mb-4">{message}</p>
          <div className="flex justify-end">
            <Button variant="secondary" onClick={handleRegisterClick} className="mr-2">
              Create Account
            </Button>
            <Button variant="primary" onClick={handleLoginClick}>
              Login
            </Button>
          </div>
        </div>
      </Modal>
    );
  }

  // Render an Alert component if asModal is false
  return (
    isVisible && (
      <Alert
        message={message}
        variant="warning"
        className={classNames('mb-4', className)}
        dismissible={true}
        onDismiss={onClose}
      >
        {children}
        <div className="mt-2">
          <Button variant="secondary" size="sm" onClick={handleRegisterClick} className="mr-2">
            Create Account
          </Button>
          <Button variant="primary" size="sm" onClick={handleLoginClick}>
            Login
          </Button>
        </div>
      </Alert>
    )
  );
};

// Export the AnonymousWarning component as the default export
export default AnonymousWarning;