import React, { useCallback } from 'react'; // React v18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.15.0
import { saveAs } from 'file-saver'; // file-saver v2.0.5
import { Button } from '../../components/common/Button';
import Dropdown from '../../components/common/Dropdown';
import Modal from '../../components/common/Modal';
import Tooltip from '../../components/common/Tooltip';
import DocumentSavePrompt from './DocumentSavePrompt';
import AnonymousWarning from '../auth/AnonymousWarning';
import { ROUTES } from '../../constants/routes';
import {
  useAppDispatch,
  useAppSelector
} from '../../store';
import {
  useDocument,
} from '../../hooks/useDocument';
import { useAuth } from '../../hooks/useAuth';
import { documentActions } from '../../store/slices/documentSlice';
import { Document } from '../../types/document';

// Define the DocumentActionsProps interface
interface DocumentActionsProps {
  onAction?: () => void;
}

/**
 * React functional component that provides document action buttons and menus
 * @param {DocumentActionsProps} props - props
 * @returns {JSX.Element}
 */
export const DocumentActions: React.FC<DocumentActionsProps> = (props) => {
  // Access the navigate function from react-router-dom
  const navigate = useNavigate();

  // Access the dispatch function from Redux
  const dispatch = useAppDispatch();

  // Access the useDocument hook
  const { document } = useDocument();

  // Access the useAuth hook
  const { isAuthenticated } = useAuth();

  // Define state for the save prompt modal
  const [isSavePromptOpen, setIsSavePromptOpen] = React.useState(false);

  // Define state for the delete confirmation modal
  const [isDeleteConfirmationOpen, setIsDeleteConfirmationOpen] = React.useState(false);

  /**
   * Handles the document save operation, checking auth status and showing prompts if needed
   * @param {React.MouseEvent<HTMLButtonElement>} event - event
   * @returns {void}
   */
  const handleSave = (event: React.MouseEvent<HTMLButtonElement>): void => {
    // Prevent default button behavior
    event.preventDefault();

    // Check if user is authenticated
    if (isAuthenticated) {
      // If authenticated, dispatch save document action
      dispatch(documentActions.saveDocument(document as Document));
    } else {
      // If not authenticated, show save prompt
      setIsSavePromptOpen(true);
    }

    // Call onAction callback if provided
    if (props.onAction) {
      props.onAction();
    }
  };

  /**
   * Handles document download operation
   * @param {React.MouseEvent<HTMLButtonElement>} event - event
   * @returns {void}
   */
  const handleDownload = (event: React.MouseEvent<HTMLButtonElement>): void => {
    // Prevent default button behavior
    event.preventDefault();

    // Check if document exists
    if (document) {
      // Generate filename based on document title
      const filename = document.metadata.title || 'document';

      // Dispatch download document action
      dispatch(documentActions.downloadDocument(document));

      // Use file-saver to trigger browser download
      //saveAs(new Blob([document.content]), `${filename}.txt`);

      // Call onAction callback if provided
      if (props.onAction) {
        props.onAction();
      }
    }
  };

  /**
   * Handles document deletion with confirmation
   * @param {React.MouseEvent<HTMLButtonElement>} event - event
   * @returns {void}
   */
  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>): void => {
    // Prevent default button behavior
    event.preventDefault();

    // Show delete confirmation modal
    setIsDeleteConfirmationOpen(true);

    // Call onAction callback if provided
    if (props.onAction) {
      props.onAction();
    }
  };

  /**
   * Executes the actual document deletion after confirmation
   * @returns {void}
   */
  const confirmDelete = (): void => {
    // Check if document exists and has an ID
    if (document && document.id) {
      // Dispatch delete document action with document ID
      dispatch(documentActions.deleteDocument(document.id));

      // Close confirmation modal
      setIsDeleteConfirmationOpen(false);

      // Navigate to documents list page
      navigate(ROUTES.DOCUMENTS);
    }

    // Call onAction callback if provided
    if (props.onAction) {
      props.onAction();
    }
  };

  /**
   * Handles document sharing functionality
   * @param {React.MouseEvent<HTMLButtonElement>} event - event
   * @returns {void}
   */
  const handleShare = (event: React.MouseEvent<HTMLButtonElement>): void => {
    // Prevent default button behavior
    event.preventDefault();

    // Generate shareable link or prepare document for sharing
    // Implement sharing mechanism (copy link, email, etc.)
    // Show success notification

    // Call onAction callback if provided
    if (props.onAction) {
      props.onAction();
    }
  };

  return (
    <>
      <div className="flex items-center space-x-2">
        {/* Save Button with Tooltip */}
        <Tooltip content="Save document">
          <Button onClick={handleSave}>Save</Button>
        </Tooltip>

        {/* Download Button with Tooltip */}
        <Tooltip content="Download document">
          <Button onClick={handleDownload}>Download</Button>
        </Tooltip>

        {/* Share Button with Tooltip */}
        <Tooltip content="Share document">
          <Button onClick={handleShare}>Share</Button>
        </Tooltip>

        {/* Delete Button with Tooltip */}
        <Tooltip content="Delete document">
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </Tooltip>
      </div>

      {/* Save Prompt Modal */}
      <DocumentSavePrompt
        isOpen={isSavePromptOpen}
        onClose={() => setIsSavePromptOpen(false)}
        document={document}
        onSaveSuccess={() => {
          if (props.onAction) {
            props.onAction();
          }
        }}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteConfirmationOpen}
        onClose={() => setIsDeleteConfirmationOpen(false)}
        title="Confirm Delete"
      >
        <div className="p-4">
          <p className="mb-4">Are you sure you want to delete this document?</p>
          <div className="flex justify-end">
            <Button
              variant="secondary"
              onClick={() => setIsDeleteConfirmationOpen(false)}
              className="mr-2"
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={confirmDelete}>
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};