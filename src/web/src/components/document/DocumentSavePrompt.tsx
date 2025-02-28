import React, { useState, useCallback } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { LoginForm } from '../auth/LoginForm';
import { RegisterForm } from '../auth/RegisterForm';
import { useAuth } from '../../hooks/useAuth';
import { useDocument } from '../../hooks/useDocument';
import { Document } from '../../types/document';

/**
 * Interface defining the props for the DocumentSavePrompt component
 */
interface DocumentSavePromptProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document | null;
  onSaveSuccess: () => void;
}

/**
 * A functional component that displays a modal prompting anonymous users to create an account when attempting to save a document
 */
export const DocumentSavePrompt: React.FC<DocumentSavePromptProps> = ({
  isOpen,
  onClose,
  document,
  onSaveSuccess,
}) => {
  // Destructure props to get isOpen, onClose, document, and onSaveSuccess
  // Initialize state for activeTab, isSaving, and error
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Access authentication state and functions using useAuth hook
  const { login, register, convertToRegistered, user } = useAuth();

  // Access document operations using useDocument hook
  const { saveDocumentChanges } = useDocument();

  /**
   * Changes the active tab between login and register views
   * @param tabName 
   */
  const handleTabChange = useCallback((tabName: 'login' | 'register') => {
    // Set the activeTab state to the provided tabName
    setActiveTab(tabName);
    // Clear any previous error messages
    setError(null);
  }, []);

  /**
   * Handles saving the document to session storage for anonymous users
   */
  const handleAnonymousSave = useCallback(async () => {
    // Set isSaving state to true
    setIsSaving(true);
    setError(null);

    try {
      // Attempt to save document to session storage using the document hook
      if (document) {
        await saveDocumentChanges();
        // Call onSaveSuccess callback if save is successful
        onSaveSuccess();
        // Close the modal with onClose
        onClose();
      } else {
        setError("No document to save");
      }
    } catch (err: any) {
      // Display error message if save fails
      setError(err.message || 'Failed to save document');
    } finally {
      // Set isSaving state to false regardless of outcome
      setIsSaving(false);
    }
  }, [onClose, onSaveSuccess, document, saveDocumentChanges]);

  /**
   * Handles successful authentication (login or register) and saves document
   */
  const handleAuthSuccess = useCallback(async () => {
    // Set isSaving state to true
    setIsSaving(true);
    setError(null);

    try {
      // Attempt to save document to user's account using the document hook
      if (document) {
        await saveDocumentChanges();
        // Call onSaveSuccess callback if save is successful
        onSaveSuccess();
      } else {
        setError("No document to save");
      }
      // Close the modal with onClose
      onClose();
    } catch (err: any) {
      // Display error message if save fails
      setError(err.message || 'Failed to save document');
    } finally {
      // Set isSaving state to false regardless of outcome
      setIsSaving(false);
    }
  }, [onClose, onSaveSuccess, document, saveDocumentChanges]);

  // Return a Modal component with appropriate content based on the activeTab state
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Save Your Document"
    >
      {error && <Alert variant="error" message={error} />}
      <div className="flex justify-around mb-4">
        {/* Include tab navigation between Login and Register views */}
        <Button
          variant={activeTab === 'login' ? 'primary' : 'secondary'}
          onClick={() => handleTabChange('login')}
          size="sm"
        >
          Login
        </Button>
        <Button
          variant={activeTab === 'register' ? 'primary' : 'secondary'}
          onClick={() => handleTabChange('register')}
          size="sm"
        >
          Register
        </Button>
      </div>

      {/* Display LoginForm or RegisterForm based on activeTab */}
      {activeTab === 'login' ? (
        <LoginForm onSuccess={handleAuthSuccess} redirectTo={""} showRegisterLink={false} />
      ) : (
        <RegisterForm onSuccess={handleAuthSuccess} isAnonymousConversion={true} showLoginLink={false} />
      )}

      <div className="mt-4">
        {/* Include anonymous save option with warning about limitations */}
        <Button
          variant="tertiary"
          onClick={handleAnonymousSave}
          disabled={isSaving}
        >
          Continue Anonymously (Session Storage Only)
        </Button>
        <Alert
          variant="warning"
          message="Your document will only be saved in your browser's session storage. It may be lost if you clear your browser data."
        />
      </div>
    </Modal>
  );
};