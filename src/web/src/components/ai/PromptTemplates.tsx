import React, { useMemo, useState, useEffect } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import { TemplateItem } from './TemplateItem';
import { PromptTemplate } from '../../types/ai';
import { useAi } from '../../hooks/useAi';
import { PROMPT_CATEGORIES } from '../../constants/ai';
import { useSidebar } from '../../hooks/useSidebar';
import { AI_EVENTS } from '../../lib/analytics/events';
import { trackEvent } from '../../lib/analytics';

/**
 * Interface defining the props for the PromptTemplates component
 */
interface PromptTemplatesProps {
  className?: string;
  showRecentTemplates?: boolean;
  showAllCategories?: boolean;
  onTemplateSelect?: (templateId: string) => void;
}

/**
 * Functional component that renders a list of AI improvement templates
 * @param props - PromptTemplatesProps
 * @returns Rendered template list component
 */
export const PromptTemplates: React.FC<PromptTemplatesProps> = (props) => {
  // Destructure props
  const { className, showRecentTemplates, showAllCategories, onTemplateSelect } = props;

  // Get templates and selectedTemplate from useAi hook
  const { templates, selectedTemplate } = useAi();

  // Get sidebar isOpen state from useSidebar hook
  const { isOpen } = useSidebar();

  // Set up state for tracking favorite templates
  const [favoriteTemplates, setFavoriteTemplates] = useState<string[]>([]);

  /**
   * Retrieves recently used templates from localStorage or state
   * @param allTemplates - PromptTemplate[]
   * @returns Array of recently used templates, sorted by most recent
   */
  const getRecentTemplates = (allTemplates: PromptTemplate[]): PromptTemplate[] => {
    // Retrieve recent template IDs from localStorage or state
    const recentTemplateIds = JSON.parse(localStorage.getItem('recentTemplates') || '[]') as string[];

    // Filter allTemplates to include only those with IDs in the recent list
    const recentTemplates = allTemplates.filter(template => recentTemplateIds.includes(template.id));

    // Sort templates based on their order in the recent list
    const sortedTemplates = recentTemplates.sort((a, b) => {
      const aIndex = recentTemplateIds.indexOf(a.id);
      const bIndex = recentTemplateIds.indexOf(b.id);
      return aIndex - bIndex;
    });

    // Return the filtered and sorted templates array
    return sortedTemplates;
  };

  /**
   * Organizes templates into category groups
   * @param templates - PromptTemplate[]
   * @returns Object with category keys and arrays of templates
   */
  const groupTemplatesByCategory = (templates: PromptTemplate[]): Record<string, PromptTemplate[]> => {
    // Create empty result object
    const groupedTemplates: Record<string, PromptTemplate[]> = {};

    // Iterate through templates array
    templates.forEach(template => {
      // Group templates by their category property
      if (!groupedTemplates[template.category]) {
        groupedTemplates[template.category] = [];
      }
      groupedTemplates[template.category].push(template);
    });

    // Sort templates within each category alphabetically by name
    Object.keys(groupedTemplates).forEach(category => {
      groupedTemplates[category].sort((a, b) => a.name.localeCompare(b.name));
    });

    // Return the grouped templates object
    return groupedTemplates;
  };

  // Use useMemo to group templates by category
  const groupedTemplates = useMemo(() => {
    return groupTemplatesByCategory(templates);
  }, [templates]);

  // Use useMemo to get recent templates if showRecentTemplates is true
  const recentTemplates = useMemo(() => {
    if (showRecentTemplates) {
      return getRecentTemplates(templates);
    }
    return [];
  }, [showRecentTemplates, templates]);

  // Generate className using classNames utility combining provided className and conditional styles
  const promptTemplatesClassName = classNames(
    'prompt-templates',
    {
      'prompt-templates--open': isOpen,
    },
    className
  );

  // Render the component
  return (
    <div className={promptTemplatesClassName}>
      {/* Render section for recently used templates if showRecentTemplates and recentTemplates exist */}
      {showRecentTemplates && recentTemplates.length > 0 && (
        <section className="prompt-templates__section">
          <h3 className="prompt-templates__title">Recently Used</h3>
          <ul className="prompt-templates__list">
            {recentTemplates.map(template => (
              <li key={template.id} className="prompt-templates__item">
                {/* Render TemplateItem components for each template */}
                <TemplateItem
                  template={template}
                  isSelected={selectedTemplate?.id === template.id}
                  isRecent={true}
                  isFavorite={favoriteTemplates.includes(template.id)}
                  onSelect={() => {
                    // Track template selection using trackEvent with AI_EVENTS.USE_TEMPLATE
                    trackEvent(AI_EVENTS.USE_TEMPLATE, 'template_selected', {
                      templateId: template.id,
                      templateName: template.name,
                    });
                    if (onTemplateSelect) {
                      onTemplateSelect(template.id);
                    }
                  }}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Render sections for each category group based on showAllCategories */}
      {showAllCategories &&
        Object.entries(groupedTemplates).map(([category, templates]) => (
          <section key={category} className="prompt-templates__section">
            <h3 className="prompt-templates__title">{category}</h3>
            <ul className="prompt-templates__list">
              {templates.map(template => (
                <li key={template.id} className="prompt-templates__item">
                  {/* Render TemplateItem components for each template */}
                  <TemplateItem
                    template={template}
                    isSelected={selectedTemplate?.id === template.id}
                    isRecent={false}
                    isFavorite={favoriteTemplates.includes(template.id)}
                    onSelect={() => {
                      // Track template selection using trackEvent with AI_EVENTS.USE_TEMPLATE
                      trackEvent(AI_EVENTS.USE_TEMPLATE, 'template_selected', {
                        templateId: template.id,
                        templateName: template.name,
                      });
                      if (onTemplateSelect) {
                        onTemplateSelect(template.id);
                      }
                    }}
                  />
                </li>
              ))}
            </ul>
          </section>
        ))}
    </div>
  );
};