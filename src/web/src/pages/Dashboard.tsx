import React, { useEffect, useCallback } from 'react'; // React v18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.15.0

import MainLayout from '../components/layout/MainLayout';
import DocumentList from '../components/document/DocumentList';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Spinner from '../components/common/Spinner';
import useAuth from '../hooks/useAuth';
import useDocument from '../hooks/useDocument';
import ROUTES from '../constants/routes';

/**
 * @function Dashboard
 * @description Main dashboard component that shows the user's documents and document management options
 * @returns {JSX.Element} Dashboard page component
 */
const Dashboard: React.FC = () => {
  // LD1: Initialize navigate function from useNavigate
  const navigate = useNavigate();

  // LD1: Get user data and authentication status from useAuth hook
  const { user, isAuthenticated } = useAuth();

  // LD1: Get document data and functions from useDocument hook
  const { documents, loading, fetchUserDocuments, createNewDocument } = useDocument();

  // LD1: Fetch user documents when component mounts using useEffect
  useEffect(() => {
    if (isAuthenticated) {
      fetchUserDocuments();
    }
  }, [isAuthenticated, fetchUserDocuments]);

  /**
   * @function handleCreateNewDocument
   * @description Creates a new document and navigates to the editor
   * @returns {Promise<void>} Async function with no return value
   */
  const handleCreateNewDocument = useCallback(async () => {
    try {
      // LD1: Call createNewDocument function from useDocument hook
      const newDocument = await createNewDocument('Untitled Document', '');
      // LD1: When document is created, get the new document ID
      if (newDocument && newDocument.id) {
        // LD1: Navigate to editor route with the new document ID
        navigate(`${ROUTES.EDITOR}/${newDocument.id}`);
      } else {
        console.error('Failed to create new document or missing document ID.');
      }
    } catch (error) {
      // LD1: Handle any errors that occur during document creation
      console.error('Error creating new document:', error);
    }
  }, [createNewDocument, navigate]);

  /**
   * @function handleSelectDocument
   * @description Handles selection of an existing document and navigates to the editor
   * @param {Document} document - document
   * @returns {void} No return value
   */
  const handleSelectDocument = useCallback((document: Document) => {
    // LD1: Extract document ID from the selected document
    const documentId = document.id;
    // LD1: Navigate to the editor route with the selected document ID
    navigate(`${ROUTES.EDITOR}/${documentId}`);
  }, [navigate]);

  /**
   * @function renderDocumentStats
   * @description Renders statistics cards showing document metrics
   * @returns {JSX.Element} Statistics card components
   */
  const renderDocumentStats = useCallback(() => {
    // LD1: Calculate document statistics (total count, documents with AI edits)
    const totalDocuments = documents ? documents.length : 0;
    const aiEditedDocuments = documents ? documents.filter(doc => doc.stats.suggestionCount > 0).length : 0;

    // LD1: Render card components with statistics and appropriate icons
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Card>
          <div className="flex items-center">
            <div className="text-3xl font-bold mr-2">{totalDocuments}</div>
            <div>Total Documents</div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <div className="text-3xl font-bold mr-2">{aiEditedDocuments}</div>
            <div>Documents with AI Edits</div>
          </div>
        </Card>
      </div>
    );
  }, [documents]);

  // LD1: Render MainLayout with appropriate props
  return (
    <MainLayout>
      {/* LD1: Render welcome section with user's name */}
      <div className="mb-4">
        <h1 className="text-2xl font-semibold">
          Welcome, {isAuthenticated && user ? user.firstName : 'Guest'}!
        </h1>
      </div>

      {/* LD1: Render document statistics (count, recent edits) */}
      {renderDocumentStats()}

      {/* LD1: Render 'Create New Document' button */}
      <Button onClick={handleCreateNewDocument} className="mb-4">
        Create New Document
      </Button>

      {/* LD1: Render DocumentList component with the user's documents */}
      {loading ? (
        // LD1: Show loading spinner while documents are being fetched
        <div className="flex justify-center items-center">
          <Spinner size="md" />
        </div>
      ) : documents && documents.length > 0 ? (
        <DocumentList documents={documents} onSelectDocument={handleSelectDocument} />
      ) : (
        // LD1: Handle empty state when no documents exist
        <div className="text-center">No documents yet. Create one to get started!</div>
      )}
    </MainLayout>
  );
};

// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default Dashboard;