import React from 'react'; // React v18.2.0

// Standard interface for icon props
export interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  color?: string;
  title?: string;
}

// Factory function to create standardized icon components
export const createIcon = (renderFunc: React.FC<IconProps>): React.FC<IconProps> => {
  const Icon: React.FC<IconProps> = ({ 
    size = 24, 
    color = 'currentColor',
    title,
    viewBox = '0 0 24 24',
    ...rest 
  }) => {
    // Generate a unique ID for accessibility if title is provided
    const titleId = title ? `icon-title-${Math.random().toString(36).substring(2, 9)}` : undefined;
    
    return (
      <svg
        width={size}
        height={size}
        viewBox={viewBox}
        fill="none"
        stroke={color}
        xmlns="http://www.w3.org/2000/svg"
        role={title ? 'img' : 'presentation'}
        aria-labelledby={titleId}
        {...rest}
      >
        {title && <title id={titleId}>{title}</title>}
        {renderFunc({ size, color, title, ...rest })}
      </svg>
    );
  };
  
  return Icon;
};

// Text formatting icons
export const BoldIcon = createIcon(({ color }) => (
  <>
    <path
      d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M6 12h9a4 4 0 014 4 4 4 0 01-4 4H6z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const ItalicIcon = createIcon(({ color }) => (
  <path
    d="M19 4h-9M14 20H5M15 4L9 20"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  />
));

export const UnderlineIcon = createIcon(({ color }) => (
  <>
    <path
      d="M6 3v7a6 6 0 006 6 6 6 0 006-6V3"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <line x1="4" y1="21" x2="20" y2="21" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </>
));

export const StrikethroughIcon = createIcon(({ color }) => (
  <>
    <path
      d="M17.5 12h-11"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M16 6a4 4 0 00-4-4 4 4 0 00-4 4M8 18a4 4 0 004 4 4 4 0 004-4"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

// Heading icon with level indicator
export const HeadingIcon: React.FC<IconProps & { level: 1 | 2 | 3 }> = ({ 
  level = 1, 
  ...props 
}) => {
  const renderHeading = ({ color }: IconProps) => {
    return (
      <>
        <path
          d="M4 12h16M4 6v12M12 6v12M20 6v12"
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <text
          x="8"
          y="18"
          fontSize="10"
          fill={color}
          textAnchor="middle"
        >
          {level}
        </text>
      </>
    );
  };

  const HeadingIconComponent = createIcon(renderHeading);
  return <HeadingIconComponent {...props} />;
};

export const ParagraphIcon = createIcon(({ color }) => (
  <path
    d="M10 4h6a4 4 0 014 4 4 4 0 01-4 4h-6v8M14 4v8"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  />
));

export const BulletListIcon = createIcon(({ color }) => (
  <>
    <circle cx="6" cy="6" r="2" fill={color} />
    <line x1="10" y1="6" x2="22" y2="6" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <circle cx="6" cy="12" r="2" fill={color} />
    <line x1="10" y1="12" x2="22" y2="12" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <circle cx="6" cy="18" r="2" fill={color} />
    <line x1="10" y1="18" x2="22" y2="18" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </>
));

export const OrderedListIcon = createIcon(({ color }) => (
  <>
    <line x1="10" y1="6" x2="22" y2="6" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="10" y1="12" x2="22" y2="12" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="10" y1="18" x2="22" y2="18" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <text x="6" y="8" fontSize="10" fill={color} textAnchor="middle">1</text>
    <text x="6" y="14" fontSize="10" fill={color} textAnchor="middle">2</text>
    <text x="6" y="20" fontSize="10" fill={color} textAnchor="middle">3</text>
  </>
));

export const BlockquoteIcon = createIcon(({ color }) => (
  <>
    <rect x="4" y="4" width="16" height="16" rx="2" ry="2" fill="none" stroke={color} strokeWidth="2" />
    <line x1="8" y1="9" x2="16" y2="9" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="8" y1="13" x2="14" y2="13" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="8" y1="17" x2="12" y2="17" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </>
));

export const CodeBlockIcon = createIcon(({ color }) => (
  <>
    <polyline points="16 18 22 12 16 6" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <polyline points="8 6 2 12 8 18" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </>
));

export const ClearFormatIcon = createIcon(({ color }) => (
  <>
    <path
      d="M6 12h12M7 5l10 14"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M12 19l-3-3M15 8l-3-3"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

// Track changes icons
export const AcceptIcon = createIcon(({ color }) => (
  <path
    d="M5 12l5 5L20 7"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  />
));

export const RejectIcon = createIcon(({ color }) => (
  <>
    <path
      d="M6 6l12 12M18 6L6 18"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

// Navigation icons
export const PreviousIcon = createIcon(({ color }) => (
  <path
    d="M15 18l-6-6 6-6"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  />
));

export const NextIcon = createIcon(({ color }) => (
  <path
    d="M9 18l6-6-6-6"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  />
));

// Collapse/expand icon with direction
export const CollapseIcon: React.FC<IconProps & { direction: 'left' | 'right' | 'up' | 'down' }> = ({ 
  direction = 'down', 
  ...props 
}) => {
  const renderCollapse = ({ color }: IconProps) => {
    switch (direction) {
      case 'up':
        return (
          <path
            d="M18 15l-6-6-6 6"
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      case 'down':
        return (
          <path
            d="M6 9l6 6 6-6"
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      case 'left':
        return (
          <path
            d="M15 18l-6-6 6-6"
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      case 'right':
        return (
          <path
            d="M9 18l6-6-6-6"
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      default:
        return null;
    }
  };
  
  const CollapseIconComponent = createIcon(renderCollapse);
  return <CollapseIconComponent {...props} direction={direction} />;
};

// Document action icons
export const SaveIcon = createIcon(({ color }) => (
  <>
    <path
      d="M17 21H7a4 4 0 01-4-4V7a4 4 0 014-4h10a4 4 0 014 4v10a4 4 0 01-4 4z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M7 3v8h10V3"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M14 3v8"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const UndoIcon = createIcon(({ color }) => (
  <>
    <path
      d="M3 10h10a7 7 0 017 7v0a7 7 0 01-7 7H9"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <polyline
      points="9 6 3 10 9 14"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const RedoIcon = createIcon(({ color }) => (
  <>
    <path
      d="M21 10H11a7 7 0 00-7 7v0a7 7 0 007 7h4"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <polyline
      points="15 6 21 10 15 14"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

// Sidebar and UI icons
export const ChatIcon = createIcon(({ color }) => (
  <>
    <path
      d="M3 7v10a3 3 0 003 3h12a3 3 0 003-3V7a3 3 0 00-3-3H6a3 3 0 00-3 3z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M8 10h8M8 14h4"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const TemplateIcon = createIcon(({ color }) => (
  <>
    <path
      d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M14 8V2M9 13h6M9 17h6"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const UserIcon = createIcon(({ color }) => (
  <>
    <path
      d="M16 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle
      cx="12"
      cy="7"
      r="4"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const SettingsIcon = createIcon(({ color }) => (
  <>
    <circle
      cx="12"
      cy="12"
      r="3"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const UploadIcon = createIcon(({ color }) => (
  <>
    <path
      d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <polyline
      points="17 8 12 3 7 8"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <line
      x1="12"
      y1="3"
      x2="12"
      y2="15"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const DownloadIcon = createIcon(({ color }) => (
  <>
    <path
      d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <polyline
      points="7 10 12 15 17 10"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <line
      x1="12"
      y1="15"
      x2="12"
      y2="3"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const SpinnerIcon = createIcon(({ color }) => (
  <>
    <circle
      cx="12"
      cy="12"
      r="10"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeDasharray="32"
      strokeDashoffset="8"
      strokeLinecap="round"
      className="icon-spinner"
    />
  </>
));

// Alert icon with variants
export const AlertIcon: React.FC<IconProps & { variant?: 'error' | 'warning' | 'info' | 'success' }> = ({ 
  variant = 'info', 
  ...props 
}) => {
  const renderAlert = ({ color }: IconProps) => {
    // Define variant-specific colors if color prop is not provided
    let iconColor = color;
    if (!props.color) {
      switch (variant) {
        case 'error':
          iconColor = '#DC3545'; // Red
          break;
        case 'warning':
          iconColor = '#FFC107'; // Yellow
          break;
        case 'info':
          iconColor = '#17A2B8'; // Blue
          break;
        case 'success':
          iconColor = '#28A745'; // Green
          break;
        default:
          iconColor = color;
      }
    }

    // Different icon shapes based on variant
    switch (variant) {
      case 'error':
      case 'warning':
        return (
          <>
            <path
              d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
              fill="none"
              stroke={iconColor}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <line x1="12" y1="9" x2="12" y2="13" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="12" y1="17" x2="12.01" y2="17" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </>
        );
      case 'info':
        return (
          <>
            <circle cx="12" cy="12" r="10" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="12" y1="16" x2="12" y2="12" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="12" y1="8" x2="12.01" y2="8" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </>
        );
      case 'success':
        return (
          <>
            <circle cx="12" cy="12" r="10" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M8 12l3 3 6-6" fill="none" stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </>
        );
      default:
        return null;
    }
  };
  
  const AlertIconComponent = createIcon(renderAlert);
  return <AlertIconComponent {...props} />;
};

export const CloseIcon = createIcon(({ color }) => (
  <>
    <path
      d="M18 6L6 18M6 6l12 12"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const MenuIcon = createIcon(({ color }) => (
  <>
    <line x1="3" y1="12" x2="21" y2="12" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="3" y1="6" x2="21" y2="6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="3" y1="18" x2="21" y2="18" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </>
));

export const DocumentIcon = createIcon(({ color }) => (
  <>
    <path
      d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M14 2v6h6M16 13H8M16 17H8M10 9H8"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));

export const AiIcon = createIcon(({ color }) => (
  <>
    <circle
      cx="12"
      cy="12"
      r="9"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M8 12a2 2 0 11-4 0 2 2 0 014 0zM14 9a2 2 0 11-4 0 2 2 0 014 0zM14 15a2 2 0 11-4 0 2 2 0 014 0zM20 12a2 2 0 11-4 0 2 2 0 014 0z"
      fill={color}
      stroke="none"
    />
    <path
      d="M7 10.5L12 8M12 8L17 10.5M7 13.5L12 16M12 16L17 13.5"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>
));