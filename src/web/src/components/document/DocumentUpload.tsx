import React, { useState, useRef, useCallback } from 'react'; // React v18.2.0
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { Spinner } from '../common/Spinner';
import { useDocument } from '../../hooks/useDocument';
import { SUPPORTED_UPLOAD_FORMATS, MAX_UPLOAD_SIZE } from '../../constants/editor';
import { trackEvent } from '../../lib/analytics';
import { EVENT_CATEGORY } from '../../lib/analytics';
import { handleError } from '../../utils/error-handling';
import { formatFileSize } from '../../utils/formatting';

/**
 * A React component that provides a user interface for uploading document files to the application
 *
 * @param props - Component properties including styling, callbacks, and display options
 */
const DocumentUpload: React.FC<DocumentUploadProps> = ({
  className,
  onUploadSuccess,
  buttonLabel = 'Upload Document',
  showFileInfo = true,
  resetOnSuccess = true,
}) => {
  // Component state for managing selected file, loading status, and error messages
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Reference to the file input element for programmatic triggering
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Access the uploadDocument function from the useDocument hook
  const { uploadDocumentFile } = useDocument();

  /**
   * Handles the file input change event, validates the selected file, and updates the component state
   *
   * @param event - The file input change event
   */
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    // LD1: Extract the selected file from event.target.files
    const file = event.target.files && event.target.files[0];

    // LD2: Validate if a file was selected
    if (!file) {
      return; // No file selected, do nothing
    }

    // LD3: Check if the file format is supported using SUPPORTED_UPLOAD_FORMATS
    const isSupportedFormat = SUPPORTED_UPLOAD_FORMATS.includes(file.type);

    // LD4: Check if the file size is within MAX_UPLOAD_SIZE limit
    const isWithinSizeLimit = file.size <= MAX_UPLOAD_SIZE;

    // LD5: If valid, update the selectedFile state and clear any error message
    if (isSupportedFormat && isWithinSizeLimit) {
      setSelectedFile(file);
      setError('');
    } else if (!isSupportedFormat) {
      // LD6: If invalid format, set error message about unsupported file type
      setError(`Unsupported file format. Please upload one of the following formats: ${SUPPORTED_UPLOAD_FORMATS.join(', ')}`);
    } else {
      // LD7: If file too large, set error message about file size limit
      setError(`File size exceeds the maximum limit of ${formatFileSize(MAX_UPLOAD_SIZE)}.`);
    }
  };

  /**
   * Processes the selected file for upload, calls the API, and handles the response
   */
  const handleUpload = async (): Promise<void> => {
    // LD1: Check if a file is selected; return early if not
    if (!selectedFile) {
      return; // No file selected, do nothing
    }

    // LD2: Set loading state to true
    setLoading(true);

    // LD3: Clear any previous error messages
    setError('');

    try {
      // LD4: Call uploadDocument function from useDocument hook with the selected file
      await uploadDocumentFile(selectedFile);

      // LD5: On success, track successful upload event with analytics
      trackEvent(EVENT_CATEGORY.DOCUMENT, 'document_import', {
        filename: selectedFile.name,
        fileSize: selectedFile.size,
        fileType: selectedFile.type,
      });

      // LD6: If onUploadSuccess callback provided, call it with the uploaded document data
      if (onUploadSuccess) {
        onUploadSuccess(selectedFile);
      }

      // LD7: Reset the form after successful upload if resetOnSuccess is true
      if (resetOnSuccess) {
        resetForm();
      }
    } catch (err: any) {
      // LD8: On error, call handleError utility and set error message state
      const errorMessage = handleError(err).message;
      setError(errorMessage);
    } finally {
      // LD9: Set loading state to false regardless of outcome
      setLoading(false);
    }
  };

  /**
   * Resets the component state to its initial values
   */
  const resetForm = (): void => {
    // LD1: Reset the selectedFile state to null
    setSelectedFile(null);

    // LD2: Clear the error message state
    setError('');

    // LD3: Reset the file input value if fileInputRef.current exists
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // Clear the selected file in the input
    }
  };

  /**
   * Programmatically triggers the file input click event
   */
  const triggerFileInput = (): void => {
    // LD1: Check if fileInputRef.current exists
    if (fileInputRef.current) {
      // LD2: Call click() method on the file input element to open file selection dialog
      fileInputRef.current.click();
    }
  };

  return (
    <div className={className}>
      {/* Hidden file input */}
      <input
        type="file"
        accept={SUPPORTED_UPLOAD_FORMATS.join(',')}
        onChange={handleFileChange}
        style={{ display: 'none' }}
        ref={fileInputRef}
        data-testid="file-input"
      />

      {/* Button to trigger file selection */}
      <Button onClick={triggerFileInput} disabled={loading} data-testid="upload-button">
        {buttonLabel}
      </Button>

      {/* Display selected file name */}
      {selectedFile && (
        <div className="mt-2 text-sm text-gray-500" data-testid="selected-file-name">
          Selected file: {selectedFile.name}
        </div>
      )}

      {/* Upload button */}
      {selectedFile && (
        <Button onClick={handleUpload} disabled={loading} className="mt-4" data-testid="confirm-upload-button">
          {loading ? <Spinner size="sm" color="white" /> : 'Confirm Upload'}
        </Button>
      )}

      {/* Loading indicator */}
      {loading && !selectedFile && (
        <div className="mt-4" data-testid="upload-spinner">
          <Spinner size="md" color="primary" center />
        </div>
      )}

      {/* Error message */}
      {error && (
        <Alert variant="error" message={error} className="mt-4" data-testid="upload-error-alert" />
      )}

      {/* Supported file formats information */}
      {showFileInfo && (
        <div className="mt-4 text-sm text-gray-500" data-testid="supported-formats-info">
          Supported formats: {SUPPORTED_UPLOAD_FORMATS.join(', ')}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;

// Define the DocumentUploadProps interface
interface DocumentUploadProps {
  className?: string;
  onUploadSuccess?: (file: File) => void;
  buttonLabel?: string;
  showFileInfo?: boolean;
  resetOnSuccess?: boolean;
}