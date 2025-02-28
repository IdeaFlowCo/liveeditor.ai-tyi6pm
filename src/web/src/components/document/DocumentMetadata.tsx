import React from 'react'; // react ^18.2.0
import classNames from 'classnames'; // classnames ^2.3.2
import {
  Document,
  DocumentMetadata as DocumentMetadataType,
  DocumentStats,
} from '../../types/document';
import {
  formatDocumentDate,
} from '../../utils/formatting';
import Badge from '../common/Badge';
import Tooltip from '../common/Tooltip';
import { useDocument } from '../../hooks/useDocument';

/**
 * Interface defining the properties for the DocumentMetadata component
 */
interface DocumentMetadataProps {
  className?: string;
  compact?: boolean;
  showStats?: boolean;
  showTags?: boolean;
  showDates?: boolean;
  document?: Document;
}

/**
 * Component for displaying document metadata such as creation date, modification date, word count, and tags
 *
 * @param props - DocumentMetadataProps
 * @returns Rendered document metadata component
 */
const DocumentMetadata: React.FC<DocumentMetadataProps> = (props) => {
  // LD1: Destructure props with defaults (compact=false, showStats=true, showTags=true, showDates=true)
  const {
    className,
    compact = false,
    showStats = true,
    showTags = true,
    showDates = true,
    document: propDocument,
  } = props;

  // LD1: Get document and stats from either props or useDocument hook
  const { document } = useDocument();
  const currentDocument = propDocument || document;

  if (!currentDocument) {
    return null; // Or display a placeholder/loading state
  }

  const metadata = currentDocument.metadata;
  const stats = currentDocument.stats;

  if (!metadata) {
    return null;
  }

  // LD1: Format creation date and last modified date using formatDocumentDate utility
  const createdAtFormatted = metadata.createdAt ? formatDocumentDate(metadata.createdAt) : 'N/A';
  const updatedAtFormatted = metadata.updatedAt ? formatDocumentDate(metadata.updatedAt) : 'N/A';

  // LD1: Generate metadata section with title and last modified information
  const metadataSection = showDates ? (
    <div className="text-sm text-gray-500">
      Created: {createdAtFormatted}
      <br />
      Last Modified: {updatedAtFormatted}
    </div>
  ) : null;

  // LD1: Generate stats section with word count, character count, and suggestion counts
  const statsSection = showStats && stats ? (
    <div className="text-sm text-gray-500">
      {stats.wordCount} words, {stats.characterCount} characters
      {stats.suggestionCount > 0 && (
        <>
          <Tooltip content="Total number of AI suggestions">
            , {stats.suggestionCount} suggestions
          </Tooltip>
          {stats.acceptedSuggestions > 0 && (
            <Tooltip content="Number of accepted AI suggestions">
              , {stats.acceptedSuggestions} accepted
            </Tooltip>
          )}
          {stats.rejectedSuggestions > 0 && (
            <Tooltip content="Number of rejected AI suggestions">
              , {stats.rejectedSuggestions} rejected
            </Tooltip>
          )}
          {stats.pendingSuggestions > 0 && (
            <Tooltip content="Number of pending AI suggestions">
              , {stats.pendingSuggestions} pending
            </Tooltip>
          )}
        </>
      )}
    </div>
  ) : null;

  // LD1: Generate tags section with document tags displayed as Badge components
  const tagsSection = showTags && metadata.tags && metadata.tags.length > 0 ? (
    <div className="mt-2">
      {metadata.tags.map((tag) => (
        <Badge key={tag} className="mr-1">
          {tag}
        </Badge>
      ))}
    </div>
  ) : null;

  // LD1: Apply conditional rendering based on compact prop and presence of data
  if (compact && !metadataSection && !statsSection && !tagsSection) {
    return null;
  }

  // LD1: Apply appropriate class names and styling based on compact mode
  const metadataClasses = classNames(
    'document-metadata',
    {
      'text-sm': compact,
      'mt-2': !compact,
    },
    className
  );

  // LD1: Return the complete metadata display with all relevant sections
  return (
    <div className={metadataClasses}>
      {metadataSection}
      {statsSection}
      {tagsSection}
    </div>
  );
};

// IE3: Export DocumentMetadata component for use throughout the application
export default DocumentMetadata;