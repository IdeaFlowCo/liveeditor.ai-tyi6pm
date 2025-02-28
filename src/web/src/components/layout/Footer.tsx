import React from 'react'; // React v18.2.0
import { Link } from 'react-router-dom'; // react-router-dom v6.15.0
import classNames from 'classnames'; // classnames v2.3.2
import { ROUTES } from '../../constants/routes';
import { Button } from '../common/Button';

interface FooterProps {
  className?: string;
}

/**
 * Footer component providing consistent navigation, links, and copyright information
 * across the application
 */
export const Footer: React.FC<FooterProps> = ({ className }) => {
  // Get current year for dynamic copyright text
  const currentYear = new Date().getFullYear();

  // Navigation links to key application sections
  const quickLinks = [
    { name: 'Home', path: ROUTES.HOME },
    { name: 'My Documents', path: ROUTES.DOCUMENTS },
    { name: 'Settings', path: ROUTES.SETTINGS },
  ];

  // External links for help, terms, and privacy policy
  const supportLinks = [
    { name: 'Help Center', path: '#help', external: true },
    { name: 'Privacy Policy', path: '#privacy', external: true },
    { name: 'Terms of Service', path: '#terms', external: true },
    { name: 'Cookie Policy', path: '#cookies', external: true },
  ];

  // Social media links with appropriate icons
  const socialLinks = [
    { 
      name: 'Twitter', 
      ariaLabel: 'Follow us on Twitter', 
      icon: 'M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84' 
    },
    { 
      name: 'LinkedIn', 
      ariaLabel: 'Connect with us on LinkedIn', 
      icon: 'M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z' 
    },
    { 
      name: 'GitHub', 
      ariaLabel: 'Join our GitHub community', 
      icon: 'M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z' 
    },
  ];

  return (
    <footer 
      className={classNames('bg-gray-100 text-gray-800 py-8', className)}
      role="contentinfo"
      aria-label="Site footer"
    >
      <div className="container mx-auto px-4">
        {/* Main footer content with responsive layout */}
        <div className="flex flex-wrap -mx-4">
          {/* Branding section */}
          <div className="w-full sm:w-1/2 lg:w-1/3 px-4 mb-8 lg:mb-0">
            <h2 className="text-xl font-semibold mb-4">AI Writing Enhancement</h2>
            <p className="mb-4 text-gray-600">
              Streamline your writing process with intelligent suggestions and edits powered by AI.
            </p>
            <Link to={ROUTES.HOME}>
              <Button 
                variant="primary" 
                size="sm" 
                aria-label="Get started with AI Writing Enhancement"
              >
                Get Started
              </Button>
            </Link>
          </div>

          {/* Quick Links */}
          <div className="w-full sm:w-1/2 lg:w-1/3 px-4 mb-8 lg:mb-0">
            <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
            <nav aria-label="Footer quick links navigation">
              <ul className="space-y-2">
                {quickLinks.map((link) => (
                  <li key={link.name}>
                    <Link 
                      to={link.path} 
                      className="text-gray-600 hover:text-[#2C6ECB] focus:text-[#2C6ECB] focus:outline-none focus:underline transition-colors"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
                <li>
                  <a 
                    href="#contact" 
                    className="text-gray-600 hover:text-[#2C6ECB] focus:text-[#2C6ECB] focus:outline-none focus:underline transition-colors"
                  >
                    Contact Us
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          {/* Support & Legal */}
          <div className="w-full sm:w-1/2 lg:w-1/3 px-4">
            <h3 className="text-lg font-semibold mb-4">Support & Legal</h3>
            <nav aria-label="Footer support and legal navigation">
              <ul className="space-y-2">
                {supportLinks.map((link) => (
                  <li key={link.name}>
                    <a 
                      href={link.path} 
                      className="text-gray-600 hover:text-[#2C6ECB] focus:text-[#2C6ECB] focus:outline-none focus:underline transition-colors"
                      target={link.external ? "_blank" : undefined}
                      rel={link.external ? "noopener noreferrer" : undefined}
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </div>

        {/* Bottom footer with copyright and social media */}
        <div className="pt-8 mt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row md:justify-between items-center">
            <p className="mb-4 md:mb-0 text-gray-600">
              © {currentYear} AI Writing Enhancement. All rights reserved.
            </p>
            <div className="flex space-x-4">
              {/* Social media links */}
              {socialLinks.map((social) => (
                <a 
                  key={social.name}
                  href="#" 
                  className="text-gray-500 hover:text-[#2C6ECB] focus:text-[#2C6ECB] focus:outline-none focus:ring-2 focus:ring-[#2C6ECB] rounded-full p-1 transition-colors"
                  aria-label={social.ariaLabel}
                >
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d={social.icon} />
                  </svg>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;