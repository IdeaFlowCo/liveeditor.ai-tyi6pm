import React, { useCallback } from 'react'; // React v18.2.0
import { Link, useNavigate } from 'react-router-dom'; // react-router-dom v6.15.0
import MainLayout from '../components/layout/MainLayout';
import Button from '../components/common/Button';
import { ROUTES } from '../constants/routes';

/**
 * A functional component that renders a 404 Not Found page with navigation options
 * @returns {JSX.Element} The rendered NotFound page component
 */
const NotFound: React.FC = () => {
  // Get navigate function from useNavigate hook for programmatic navigation
  const navigate = useNavigate();

  /**
   * Event handler for navigating back to the previous page
   * @param {React.MouseEvent<HTMLButtonElement>} event - The mouse event
   * @returns {void} No return value
   */
  const handleGoBack = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
    // Prevent default button click behavior
    event.preventDefault();
    // Use browser history to go back to the previous page
    window.history.back();
  }, []);

  // Render MainLayout with header and footer but no sidebar
  return (
    <MainLayout showSidebar={false}>
      <div className="flex flex-col items-center justify-center h-full">
        {/* Display 404 error heading with appropriate styling */}
        <h1 className="text-4xl font-bold text-gray-800 mb-4">404 - Not Found</h1>
        {/* Show friendly error message explaining that the page wasn't found */}
        <p className="text-gray-600 mb-8">
          Oops! It looks like the page you are looking for could not be found.
        </p>
        {/* Provide a Button to navigate back to the home page */}
        <Link to={ROUTES.HOME}>
          <Button variant="primary" className="mr-4">
            Go to Home
          </Button>
        </Link>
        {/* Offer a secondary option to go back to the previous page using browser history */}
        <Button variant="secondary" onClick={handleGoBack}>
          Go Back
        </Button>
      </div>
    </MainLayout>
  );
};

export default NotFound;