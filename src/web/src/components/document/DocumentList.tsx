import React, { useState, useEffect, useCallback } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import DocumentCard from './DocumentCard';
import { Document, DocumentFilter, DocumentListResponse } from '../../types/document';
import { getDocuments, deleteDocument } from '../../api/document';
import useAuth from '../../hooks/useAuth';
import useDocument from '../../hooks/useDocument';
import Button from '../common/Button';
import Input from '../common/Input';
import Dropdown from '../common/Dropdown';
import Spinner from '../common/Spinner';

/**
 * Props for the DocumentList component
 */
interface DocumentListProps {
  isGrid?: boolean;
  searchTerm?: string;
  filter?: DocumentFilter;
  sortBy?: string;
  perPage?: number;
  onSelectDocument: (document: Document) => void;
  onDeleteDocument?: (id: string) => void;
  className?: string;
}

/**
 * Component that displays a paginated list of documents with filtering and sorting capabilities
 * @param {DocumentListProps} props - props
 * @returns {JSX.Element} Rendered document list component
 */
const DocumentList: React.FC<DocumentListProps> = (props) => {
  // LD1: Destructure props including isGrid, searchTerm, filter, sortBy, perPage, callbacks
  const { 
    isGrid = true, 
    searchTerm: initialSearchTerm = '',
    filter: initialFilter, 
    sortBy: initialSortBy = 'recent', 
    perPage: initialPerPage = 10,
    onSelectDocument, 
    onDeleteDocument, 
    className 
  } = props;

  // LD1: Initialize state for documents, loading, current page, and total pages
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalDocuments, setTotalDocuments] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>(initialSearchTerm);
  const [filter, setFilter] = useState<DocumentFilter>(initialFilter || {});
  const [sortBy, setSortBy] = useState<string>(initialSortBy);
  const [perPage, setPerPage] = useState<number>(initialPerPage);

  // LD1: Access authentication state using useAuth hook
  const { isAuthenticated, isAnonymous } = useAuth();

  // LD1: Implement fetchDocuments function to load documents with current filters
  /**
   * Fetches documents based on current pagination, search, and filter state
   * @param {number} page - page
   * @returns {Promise<void>} No direct return value, updates component state
   */
  const fetchDocuments = useCallback(async (page: number = 1) => {
    // Set loading state to true
    setLoading(true);

    try {
      // Construct API parameters including page, perPage, search, and filter criteria
      const params: any = {
        page,
        perPage,
        search: searchTerm,
        sortBy,
        ...filter
      };

      // Call getDocuments API function with parameters
      const response: DocumentListResponse = await getDocuments(params);

      // Update documents, total, and pagination state with response data
      setDocuments(response.documents);
      setTotalPages(response.totalPages);
      setTotalDocuments(response.total);
      setCurrentPage(response.page);
    } catch (error) {
      // Handle potential errors with appropriate error state
      console.error('Error fetching documents:', error);
    } finally {
      // Set loading state to false when complete
      setLoading(false);
    }
  }, [searchTerm, filter, sortBy, perPage, getDocuments]);

  // LD1: Create handlePageChange function to navigate between pages
  /**
   * Handles pagination control clicks
   * @param {number} newPage - newPage
   * @returns {void} No return value
   */
  const handlePageChange = (newPage: number): void => {
    // Validate that new page is within valid range
    if (newPage < 1 || newPage > totalPages) return;

    // Update current page state
    setCurrentPage(newPage);

    // Fetch documents for the new page
    fetchDocuments(newPage);
  };

  // LD1: Create handleSearch function to filter documents by search term
  /**
   * Handles search input changes
   * @param {React.ChangeEvent<HTMLInputElement>} event - event
   * @returns {void} No return value
   */
  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>): void => {
    // Extract search term from input event
    const term = event.target.value;

    // Update local search state
    setSearchTerm(term);

    // Reset to first page
    setCurrentPage(1);

    // Trigger document fetch with new search criteria
    setFilter(prevFilter => ({ ...prevFilter, title: term }));
  };

  // LD1: Create handleSort function to change document sorting
  /**
   * Handles sort option selection
   * @param {string} sortOption - sortOption
   * @returns {void} No return value
   */
  const handleSort = (sortOption: string): void => {
    // Update sort state with new option
    setSortBy(sortOption);

    // Reset to first page
    setCurrentPage(1);

    // Fetch documents with new sorting
    fetchDocuments(1);
  };

  // LD1: Create handleDelete function to delete documents with confirmation
  /**
   * Handles document deletion with confirmation
   * @param {string} id - id
   * @returns {Promise<void>} No direct return value
   */
  const handleDelete = async (id: string): Promise<void> => {
    // Display confirmation dialog to user
    const confirmed = window.confirm('Are you sure you want to delete this document?');

    if (confirmed) {
      try {
        // Call deleteDocument API function
        await deleteDocument(id);

        // Refresh document list after successful deletion
        fetchDocuments(currentPage);

        // Call onDeleteDocument callback if provided
        if (onDeleteDocument) {
          onDeleteDocument(id);
        }
      } catch (error) {
        // Handle potential errors with appropriate feedback
        console.error('Error deleting document:', error);
        alert('Failed to delete document. Please try again.');
      }
    }
  };

  // LD1: Use useEffect to fetch documents when filter criteria change
  useEffect(() => {
    fetchDocuments(currentPage);
  }, [fetchDocuments, currentPage]);

  // LD1: Render the grid or list view based on isGrid prop
  const renderGridView = (): JSX.Element => (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {documents.map(document => (
        <DocumentCard 
          key={document.id} 
          document={document} 
          onDelete={onDeleteDocument} 
          className="h-full"
        />
      ))}
    </div>
  );

  // LD1: Render documents in a tabular list layout
  const renderListView = (): JSX.Element => (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Modified</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AI Edits</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {documents.map(document => (
            <tr key={document.id} onClick={() => onSelectDocument(document)} className="hover:bg-gray-100 cursor-pointer">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{document.metadata.title}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{document.metadata.updatedAt}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{document.stats.suggestionCount}</td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button onClick={(e) => {e.stopPropagation(); handleDelete(document.id);}} className="text-red-600 hover:text-red-900">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // LD1: Display loading spinner while documents are being fetched
  const renderLoadingState = (): JSX.Element => (
    <div className="flex justify-center items-center h-32">
      <Spinner size="md" color="primary" />
    </div>
  );

  // LD1: Show empty state when no documents are available
  const renderEmptyState = (): JSX.Element => (
    <div className="text-center py-8">
      {searchTerm ? (
        <p>No documents found matching your search.</p>
      ) : isAuthenticated ? (
        <p>You have no documents yet. Create one to get started!</p>
      ) : (
        <p>Create an account to save your documents!</p>
      )}
    </div>
  );

  // LD1: Render pagination controls if there are multiple pages
  const renderPagination = (): JSX.Element => (
    <div className="flex justify-between items-center mt-4">
      <Button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
        Previous
      </Button>
      <span>Page {currentPage} of {totalPages} (Total: {totalDocuments})</span>
      <Button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>
        Next
      </Button>
    </div>
  );

  // LD1: Apply appropriate responsive styling for grid/list views
  return (
    <div className={classNames('document-list', className)}>
      {/* Search Input */}
      <Input 
        type="search" 
        placeholder="Search documents..." 
        value={searchTerm} 
        onChange={handleSearch} 
        className="mb-4" 
      />

      {/* Sort Dropdown */}
      <Dropdown
        options={[
          { label: 'Most Recent', value: 'recent' },
          { label: 'Title (A-Z)', value: 'title_asc' },
          { label: 'Title (Z-A)', value: 'title_desc' }
        ]}
        value={sortBy}
        onChange={handleSort}
        placeholder="Sort by"
        className="mb-4"
      />

      {/* Document List */}
      {loading ? renderLoadingState() : documents.length > 0 ? (
        isGrid ? renderGridView() : renderListView()
      ) : (
        renderEmptyState()
      )}

      {/* Pagination */}
      {totalPages > 1 && renderPagination()}
    </div>
  );
};

// IE3: Export DocumentList component
export default DocumentList;