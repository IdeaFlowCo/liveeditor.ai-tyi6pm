import React from 'react'; // React v18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.15.0
import classNames from 'classnames'; // classnames v2.3.2

import Card from '../common/Card';
import Badge from '../common/Badge';
import { DocumentActions } from './DocumentActions';
import {
  Document,
  DocumentMetadata,
  DocumentStats,
  DocumentState,
} from '../../types/document';
import { formatDocumentDate, truncateText } from '../../utils/formatting';
import { ROUTES } from '../../constants/routes';

/**
 * Props for the DocumentCard component
 */
interface DocumentCardProps {
  document: Document;
  onDelete?: (id: string) => void;
  className?: string;
}

/**
 * Helper function to determine document status badge text and variant
 * @param document 
 * @returns 
 */
const getStatusBadge = (document: Document): { text: string; variant: string } => {
  if (document.isAnonymous) {
    return { text: 'Anonymous', variant: 'warning' };
  }

  switch (document.state) {
    case DocumentState.DRAFT:
      return { text: 'Draft', variant: 'info' };
    case DocumentState.SAVED:
      return { text: 'Saved', variant: 'success' };
    case DocumentState.MODIFIED:
      return { text: 'Modified', variant: 'warning' };
    default:
      return { text: 'Unknown', variant: 'secondary' };
  }
};

/**
 * A card component that displays document information and provides actions
 * @param props 
 * @returns 
 */
const DocumentCard: React.FC<DocumentCardProps> = (props) => {
  // LD1: Destructure the document and other props from the component props
  const { document, onDelete, className } = props;

  // LD1: Extract metadata and stats from the document object
  const { metadata, stats } = document;

  // LD1: Initialize navigate function from React Router
  const navigate = useNavigate();

  // LD1: Create handleCardClick function to navigate to the editor when the card is clicked
  const handleCardClick = () => {
    navigate(`${ROUTES.EDITOR}/${document.id}`);
  };

  // LD1: Format last modified date using formatDocumentDate utility
  const lastModified = formatDocumentDate(metadata.updatedAt);

  // LD1: Truncate document title if it exceeds maximum length
  const truncatedTitle = truncateText(metadata.title, 30);

  // LD1: Determine document status badge variant based on document state and isAnonymous flag
  const statusBadge = getStatusBadge(document);

  // LD1: Render Card component with isInteractive prop to enable hover/click effects
  return (
    <Card
      className={classNames('document-card', className)}
      isInteractive
      onClick={handleCardClick}
    >
      {/* LD1: Display document title as card header with appropriate truncation */}
      <h3 className="text-lg font-semibold mb-1">{truncatedTitle}</h3>

      {/* LD1: Show last modified date below the title */}
      <p className="text-sm text-gray-500 mb-2">{lastModified}</p>

      <div className="flex items-center justify-between">
        {/* LD1: Display AI edit count badge showing stats.suggestionCount */}
        <Badge variant="secondary">{stats.suggestionCount} AI Edits</Badge>

        {/* LD1: Show document status badge (Anonymous, Draft, etc.) */}
        <Badge variant={statusBadge.variant}>{statusBadge.text}</Badge>
      </div>

      {/* LD1: Render DocumentActions component with relevant actions for the document */}
      <div className="mt-4">
        <DocumentActions onDelete={onDelete} />
      </div>
    </Card>
  );
};

// IE3: Export DocumentCard component
export default DocumentCard;