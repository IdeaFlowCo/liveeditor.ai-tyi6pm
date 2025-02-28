import React, { ReactNode } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import Header from './Header';
import Footer from './Footer';
import Sidebar from './Sidebar';
import AiSidebar from '../ai/AiSidebar';
import ErrorBoundary from '../common/ErrorBoundary';
import { useMediaQuery, useIsMobile } from '../../hooks/useMediaQuery';
import useSidebar from '../../hooks/useSidebar';

/**
 * @interface MainLayoutProps
 * @description Defines the props for the MainLayout component.
 * @param {ReactNode} children - The content to be rendered within the layout.
 * @param {string} [className] - Optional CSS class name for custom styling.
 * @param {boolean} [showSidebar] - Optional flag to show or hide the sidebar. Defaults to true.
 * @param {boolean} [showHeader] - Optional flag to show or hide the header. Defaults to true.
 * @param {boolean} [showFooter] - Optional flag to show or hide the footer. Defaults to true.
 */
interface MainLayoutProps {
  children: ReactNode;
  className?: string;
  showSidebar?: boolean;
  showHeader?: boolean;
  showFooter?: boolean;
}

/**
 * @function MainLayout
 * @description Main layout component that structures the application interface with header, content area, sidebar, and footer
 * @param {MainLayoutProps} props - The props for the MainLayout component
 * @returns {JSX.Element} The rendered layout component with all its children
 */
const MainLayout: React.FC<MainLayoutProps> = (props) => {
  // LD1: Destructure props including children, className, and flags for showing different layout elements
  const { children, className, showSidebar = true, showHeader = true, showFooter = true } = props;

  // IE3: Get sidebar state and toggle function from useSidebar hook
  const { isOpen } = useSidebar();

  // IE3: Determine if viewport is mobile using useIsMobile hook
  const isMobile = useIsMobile();

  // LD1: Calculate main content container classes based on sidebar visibility and additional className
  const mainContentClasses = classNames(
    'main-content',
    'flex-grow',
    'flex',
    'flex-row',
    'min-h-screen',
    {
      'ml-0 md:ml-80': showSidebar && isOpen && !isMobile, // Push content when sidebar is open on desktop
    },
    className
  );

  // LD1: Render ErrorBoundary as outer wrapper to catch any rendering errors
  return (
    <ErrorBoundary name="MainLayout">
      {/* LD1: Conditionally render Header component based on showHeader prop (defaults to true) */}
      {showHeader && <Header />}

      {/* LD1: Create main content area with responsive grid layout */}
      <div className={mainContentClasses}>
        {/* LD1: Conditionally render Sidebar with AiSidebar as children when showSidebar is true */}
        {showSidebar && (
          <Sidebar>
            <AiSidebar />
          </Sidebar>
        )}

        {/* LD1: Render main content container with children passed to the component */}
        <main className="flex-grow p-4">
          {children}
        </main>
      </div>

      {/* LD1: Conditionally render Footer component based on showFooter prop (defaults to true) */}
      {showFooter && <Footer />}
    </ErrorBoundary>
  );
};

// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default MainLayout;