import React, { useState, useEffect } from 'react'; // React v18.2.0
import { Link, useLocation } from 'react-router-dom'; // react-router-dom v6.15.0
import classNames from 'classnames'; // classnames v2.3.2

import { useAuth } from '../../hooks/useAuth';
import { Button } from '../common/Button';
import Dropdown from '../common/Dropdown';
import { ROUTES } from '../../constants/routes';
import useMediaQuery from '../../hooks/useMediaQuery';
import { 
  MenuIcon, 
  CloseIcon, 
  UserIcon, 
  SettingsIcon, 
  DocumentIcon,
  AiIcon
} from '../../assets/icons';
import { User, AnonymousUser } from '../../types/user';

/**
 * A functional component that renders the application header with navigation links and authentication options
 * @returns {JSX.Element} The rendered header component
 */
const Header: React.FC = () => {
  // Use useAuth hook to get authentication state and user info
  const { isAuthenticated, user, logout } = useAuth();

  // Use useLocation hook to get current route for active link highlighting
  const location = useLocation();

  // Use useMediaQuery hook to detect if viewport is mobile sized
  const isMobile = useMediaQuery('(max-width: 768px)');

  // Manage mobile menu open/close state with useState hook
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  /**
   * Toggles the mobile menu visibility state
   * @returns {void} No return value
   */
  const handleMobileMenuToggle = () => {
    // Set the isMobileMenuOpen state to the opposite of its current value
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  /**
   * Handles user logout action
   * @returns {void} No return value
   */
  const handleLogout = async () => {
    // Call the logout function from useAuth hook
    await logout();
    // Close the mobile menu if open by setting isMobileMenuOpen to false
    setIsMobileMenuOpen(false);
  };

  // Create user dropdown options for authenticated users
  const userDropdownOptions = [
    { 
      label: 'My Documents', 
      value: 'documents', 
      icon: <DocumentIcon size={16} color="currentColor" /> 
    },
    { 
      label: 'Settings', 
      value: 'settings', 
      icon: <SettingsIcon size={16} color="currentColor" /> 
    },
  ];

  return (
    <header className="bg-white shadow">
      <div className="container mx-auto py-4 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Application logo/brand that links to home page */}
        <Link to={ROUTES.HOME} className="text-xl font-bold text-gray-800 flex items-center">
          <AiIcon size={32} color="#2C6ECB" className="mr-2" />
          AI Writing Enhancement
        </Link>

        {/* Mobile menu toggle button */}
        {isMobile ? (
          <button 
            onClick={handleMobileMenuToggle} 
            className="text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? (
              <CloseIcon size={24} />
            ) : (
              <MenuIcon size={24} />
            )}
          </button>
        ) : (
          // Main navigation links appropriate to authentication status
          <nav className="hidden md:flex items-center space-x-4">
            <Link
              to={ROUTES.HOME}
              className={classNames(
                "py-2 text-gray-700 hover:text-blue-500 transition-colors",
                { "text-blue-500": location.pathname === ROUTES.HOME }
              )}
            >
              Home
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to={ROUTES.DOCUMENTS}
                  className={classNames(
                    "py-2 text-gray-700 hover:text-blue-500 transition-colors",
                    { "text-blue-500": location.pathname === ROUTES.DOCUMENTS }
                  )}
                >
                  My Documents
                </Link>
                {/* User dropdown menu for authenticated users */}
                <Dropdown
                  options={userDropdownOptions}
                  value={null}
                  onChange={(value: string) => {
                    if (value === 'documents') {
                      window.location.href = ROUTES.DOCUMENTS;
                    } else if (value === 'settings') {
                      window.location.href = ROUTES.SETTINGS;
                    }
                  }}
                  renderTrigger={({ selectedOption, isOpen, toggleDropdown, disabled }) => (
                    <button
                      type="button"
                      className={classNames(
                        "flex items-center py-2 text-gray-700 hover:text-blue-500 transition-colors focus:outline-none",
                        { "text-blue-500": location.pathname === ROUTES.SETTINGS },
                        "space-x-2"
                      )}
                      onClick={toggleDropdown}
                      disabled={disabled}
                      aria-haspopup="true"
                      aria-expanded={isOpen}
                    >
                      <UserIcon size={20} color="currentColor" />
                      <span>{(user as User)?.firstName || 'User'}</span>
                    </button>
                  )}
                />
                <Button variant="secondary" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              // Show login/register buttons for anonymous users
              <>
                <Button variant="secondary" size="sm" onClick={() => window.location.href = ROUTES.LOGIN}>
                  Login
                </Button>
                <Button variant="primary" size="sm" onClick={() => window.location.href = ROUTES.REGISTER}>
                  Register
                </Button>
              </>
            )}
          </nav>
        )}
      </div>

      {/* Implement responsive design with mobile menu toggle for small screens */}
      {isMobile && (
        <div className={classNames("md:hidden absolute top-full left-0 w-full bg-white shadow-md z-10 transition-all duration-300 overflow-hidden", {
          "max-h-96": isMobileMenuOpen,
          "max-h-0": !isMobileMenuOpen
        })}>
          <nav className="flex flex-col p-4 space-y-2">
            <Link
              to={ROUTES.HOME}
              className={classNames(
                "py-2 text-gray-700 hover:text-blue-500 transition-colors",
                { "text-blue-500": location.pathname === ROUTES.HOME }
              )}
            >
              Home
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to={ROUTES.DOCUMENTS}
                  className={classNames(
                    "py-2 text-gray-700 hover:text-blue-500 transition-colors",
                    { "text-blue-500": location.pathname === ROUTES.DOCUMENTS }
                  )}
                >
                  My Documents
                </Link>
                <Link
                  to={ROUTES.SETTINGS}
                  className={classNames(
                    "py-2 text-gray-700 hover:text-blue-500 transition-colors",
                    { "text-blue-500": location.pathname === ROUTES.SETTINGS }
                  )}
                >
                  Settings
                </Link>
                <Button variant="secondary" size="sm" onClick={handleLogout} isFullWidth>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Button variant="secondary" size="sm" onClick={() => window.location.href = ROUTES.LOGIN} isFullWidth>
                  Login
                </Button>
                <Button variant="primary" size="sm" onClick={() => window.location.href = ROUTES.REGISTER} isFullWidth>
                  Register
                </Button>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;