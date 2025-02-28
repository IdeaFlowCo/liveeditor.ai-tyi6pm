import React from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import { Button } from '../common/Button';
import { PromptTemplate } from '../../types/ai';
import { useAi } from '../../hooks/useAi';
import { AI_EVENTS } from '../../lib/analytics/events';
import { trackEvent } from '../../lib/analytics';

/**
 * Interface defining the props for the TemplateItem component
 */
interface TemplateItemProps {
  template: PromptTemplate;
  isSelected?: boolean;
  isRecent?: boolean;
  isFavorite?: boolean;
  onSelect?: () => void;
  className?: string;
}

/**
 * Functional component that renders a single template button
 * @param props - TemplateItemProps
 * @returns Rendered button component for the template
 */
export const TemplateItem: React.FC<TemplateItemProps> = (props) => {
  // Destructure props
  const { template, isSelected, isRecent, isFavorite, onSelect, className } = props;

  // Get selectedTemplate from useAi hook to check if current template is selected
  const { handleTemplateSelect, selectedTemplate } = useAi();

  // Determine if the current template is selected
  const isCurrentlySelected = selectedTemplate?.id === template.id;

  // Determine button variant based on isSelected status
  const variant = isCurrentlySelected ? 'primary' : 'secondary';

  // Generate className using classNames utility combining provided className and conditional styles
  const buttonClassName = classNames(
    'template-item',
    {
      'template-item--selected': isCurrentlySelected,
      'template-item--recent': isRecent,
      'template-item--favorite': isFavorite,
    },
    className
  );

  // Set up indicator for recent or favorite templates
  let indicator = null;
  if (isRecent) {
    indicator = '*';
  } else if (isFavorite) {
    indicator = '★';
  }

  /**
   * Handles the click event when a template is selected
   * @param event - React.MouseEvent<HTMLButtonElement>
   * @returns void
   */
  const handleTemplateClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    // Prevent default browser behavior if necessary
    event.preventDefault();

    // Track template selection using trackEvent with AI_EVENTS.USE_TEMPLATE
    trackEvent(AI_EVENTS.USE_TEMPLATE, 'template_selected', {
      templateId: template.id,
      templateName: template.name,
    });

    // Call handleTemplateSelect from useAi hook with template.id
    handleTemplateSelect(template);

    // Call onSelect callback if provided
    if (onSelect) {
      onSelect();
    }
  };

  // Render Button component with appropriate props and template name
  return (
    <Button
      variant={variant}
      className={buttonClassName}
      onClick={handleTemplateClick}
      title={template.description} // Add tooltip with template description using title attribute
    >
      {template.name}
    </Button>
  );
};