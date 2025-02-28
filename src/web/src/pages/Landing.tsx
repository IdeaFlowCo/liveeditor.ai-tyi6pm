import React, { useState, useEffect, useCallback } from 'react'; // React v18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.14.2
import MainLayout from '../components/layout/MainLayout';
import Button from '../components/common/Button';
import DocumentUpload from '../components/document/DocumentUpload';
import useAuth from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';
import logo from '../assets/images/logo.svg';
import { trackEvent } from '../lib/analytics';

/**
 * @function Landing
 * @description The landing page component that welcomes users and provides immediate access to the application's functionality
 * @returns {JSX.Element} Rendered landing page component
 */
const Landing: React.FC = () => {
  // IE3: Get authentication state and functions from useAuth hook
  const { isAuthenticated, createAnonymousSession } = useAuth();

  // IE3: Use useNavigate hook to programmatically navigate between routes
  const navigate = useNavigate();

  /**
   * @function handleStartWriting
   * @description Initiates the writing process by creating an anonymous session if needed and navigating to the editor
   * @returns {void}
   */
  const handleStartWriting = useCallback(async () => {
    // Track event for analytics
    trackEvent('navigation', 'start_writing_clicked');

    // If user is not authenticated, create anonymous session
    if (!isAuthenticated) {
      try {
        await createAnonymousSession();
      } catch (error) {
        console.error('Error creating anonymous session:', error);
        // Handle error creating anonymous session
      }
    }

    // Navigate to the editor page
    navigate(ROUTES.EDITOR);
    // Optionally pass initial state for empty document
  }, [isAuthenticated, createAnonymousSession, navigate]);

  /**
   * @function handleDocumentUpload
   * @description Handles successful document upload by navigating to the editor with the uploaded document
   * @param {object} uploadedDocument - The uploaded document object
   * @returns {void}
   */
  const handleDocumentUpload = useCallback(async (uploadedDocument: any) => {
    // Track upload event for analytics
    trackEvent('document', 'document_uploaded', {
      filename: uploadedDocument.name,
      fileSize: uploadedDocument.size,
      fileType: uploadedDocument.type,
    });

    // If user is not authenticated, create anonymous session
    if (!isAuthenticated) {
      try {
        await createAnonymousSession();
      } catch (error) {
        console.error('Error creating anonymous session:', error);
        // Handle error creating anonymous session
      }
    }

    // Navigate to editor page with the uploaded document ID
    navigate(ROUTES.EDITOR);
  }, [isAuthenticated, createAnonymousSession, navigate]);

  /**
   * @function scrollToFeatures
   * @description Scrolls the page to the features section
   * @returns {void}
   */
  const scrollToFeatures = useCallback(() => {
    // Find the features section element by ID
    const featuresSection = document.getElementById('features');

    // Scroll the element into view with smooth behavior
    featuresSection?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // LD1: Implement hero section with main value proposition and call-to-action buttons
  // LD1: Implement features section showcasing key capabilities
  // LD1: Implement how it works section with step-by-step explanation
  // LD1: Implement optional testimonials section with user quotes
  // LD1: Implement final call-to-action section with start writing button
  return (
    <MainLayout>
      {/* Hero Section */}
      <section className="text-center py-20">
        <img src={logo} alt="AI Writing Enhancement Logo" className="mx-auto h-24 w-auto mb-8" />
        <h1 className="text-4xl font-bold mb-4">Unlock Your Writing Potential with AI</h1>
        <p className="text-lg text-gray-700 mb-8">
          Improve your writing with intelligent suggestions and edits. Start creating amazing content today!
        </p>
        <Button variant="primary" size="lg" onClick={handleStartWriting} className="mr-4">
          Start Writing
        </Button>
        <Button variant="secondary" size="lg" onClick={scrollToFeatures}>
          Explore Features
        </Button>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 bg-gray-50">
        <div className="container mx-auto">
          <h2 className="text-3xl font-semibold text-center mb-8">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature Cards */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-2">AI-Powered Suggestions</h3>
              <p className="text-gray-600">
                Get intelligent suggestions for grammar, style, and tone to enhance your writing.
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-2">Track Changes</h3>
              <p className="text-gray-600">
                Review and accept or reject changes with a familiar track changes interface.
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-2">Document Management</h3>
              <p className="text-gray-600">
                Save, organize, and access your documents from anywhere with our secure cloud storage.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16">
        <div className="container mx-auto">
          <h2 className="text-3xl font-semibold text-center mb-8">How It Works</h2>
          <div className="flex flex-col md:flex-row items-center justify-center">
            {/* Steps with icons and explanations */}
            <div className="md:w-1/3 p-4 text-center">
              <span className="text-5xl text-blue-500 mb-4">1</span>
              <h3 className="text-xl font-semibold mb-2">Input Your Text</h3>
              <p className="text-gray-600">
                Paste, type, or upload your document to get started.
              </p>
            </div>
            <div className="md:w-1/3 p-4 text-center">
              <span className="text-5xl text-blue-500 mb-4">2</span>
              <h3 className="text-xl font-semibold mb-2">Get AI Suggestions</h3>
              <p className="text-gray-600">
                Our AI will analyze your text and provide intelligent suggestions.
              </p>
            </div>
            <div className="md:w-1/3 p-4 text-center">
              <span className="text-5xl text-blue-500 mb-4">3</span>
              <h3 className="text-xl font-semibold mb-2">Review and Improve</h3>
              <p className="text-gray-600">
                Review the suggestions, accept or reject changes, and finalize your document.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="py-20 bg-gray-100 text-center">
        <div className="container mx-auto">
          <h2 className="text-3xl font-semibold mb-8">Ready to Enhance Your Writing?</h2>
          <DocumentUpload onUploadSuccess={handleDocumentUpload} />
          <p className="mt-4 text-gray-600">Or start writing directly in our editor:</p>
          <Button variant="primary" size="lg" onClick={handleStartWriting} className="mt-4">
            Start Writing
          </Button>
        </div>
      </section>
    </MainLayout>
  );
};

export default Landing;