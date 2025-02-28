import React from 'react'; // React 18.2.0
import classnames from 'classnames'; // v2.3.2
import Card from '../common/Card';
import logo from '../../assets/images/logo.svg';

/**
 * Props interface for the AuthLayout component
 */
interface AuthLayoutProps {
  /** Title displayed at the top of the auth layout */
  title: string;
  /** Content to be rendered within the auth layout */
  children: React.ReactNode;
}

/**
 * A layout component that provides a consistent structure for authentication-related pages
 * such as login, registration, and password reset.
 * 
 * It creates a centered card layout with the application logo and title, designed
 * specifically for the authentication flow.
 */
const AuthLayout: React.FC<AuthLayoutProps> = ({ title, children }) => {
  const currentYear = new Date().getFullYear();
  
  return (
    <div className={classnames("min-h-screen flex flex-col items-center justify-center bg-[#F5F7FA] py-8 px-4")}>
      <div className="w-full max-w-md mx-auto">
        {/* Logo and title */}
        <div className="text-center mb-6">
          <img 
            src={logo} 
            alt="AI Writing Enhancement" 
            className="h-16 mx-auto mb-4"
          />
          <h1 className="text-2xl font-semibold text-gray-800">{title}</h1>
        </div>
        
        {/* Auth form card */}
        <Card 
          variant="elevated"
          isFullWidth
          className="mb-6"
        >
          {children}
        </Card>
        
        {/* Footer with copyright and links */}
        <footer className="text-center text-sm text-gray-600">
          <p className="mb-2">
            &copy; {currentYear} AI Writing Enhancement. All rights reserved.
          </p>
          <div>
            <a href="/terms" className="text-[#2C6ECB] hover:underline">Terms</a>
            <span className="mx-2">•</span>
            <a href="/privacy" className="text-[#2C6ECB] hover:underline">Privacy</a>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default AuthLayout;