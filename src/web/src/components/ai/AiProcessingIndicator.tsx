import React, { useState, useEffect } from 'react'; // React v18.2.0
import { useSelector } from 'react-redux'; // ^8.1.1
import { selectProcessingStatus, selectAiError } from '../../store/slices/aiSlice';
import { ProcessingStatus } from '../../types/ai';
import { Spinner } from '../common/Spinner';
import { Alert } from '../common/Alert';
import { motion } from 'framer-motion'; // ^6.3.0
import classNames from 'classnames'; // ^2.3.2

/**
 * Interface defining the props for the AiProcessingIndicator component.
 */
interface AiProcessingIndicatorProps {
  /**
   * Optional status to override Redux state. Useful for isolated scenarios.
   */
  status?: ProcessingStatus;
  /**
   * Optional progress value (0-100) for the progress bar.
   */
  progress?: number;
  /**
   * Optional message to display instead of the default status messages.
   */
  message?: string;
  /**
   * Whether to show the progress as a percentage.
   */
  showPercentage?: boolean;
  /**
   * Whether to use a compact display style.
   */
  compact?: boolean;
  /**
   * Optional CSS class name to apply to the component.
   */
  className?: string;
}

/**
 * A component that displays the current status of AI processing operations with visual feedback.
 *
 * @param {AiProcessingIndicatorProps} props - The props for the component.
 * @returns {JSX.Element} Rendered component
 */
export const AiProcessingIndicator: React.FC<AiProcessingIndicatorProps> = (props) => {
  // LD1: Destructure props: status (optional), progress (optional), message (optional), showPercentage, compact, className
  const {
    status: propStatus,
    progress: propProgress,
    message: propMessage,
    showPercentage,
    compact,
    className,
  } = props;

  // LD1: Use Redux selectors to get processing status from store if not provided via props
  const processingStatus = useSelector(selectProcessingStatus);
  const status = propStatus || processingStatus;

  // LD1: Get AI error state from Redux store
  const aiError = useSelector(selectAiError);

  // LD1: Determine if processing is active (REQUESTING or PROCESSING states)
  const isProcessing = status === ProcessingStatus.REQUESTING || status === ProcessingStatus.PROCESSING;

  // LD1: Implement useEffect to handle progress animation
  const [animatedProgress, setAnimatedProgress] = useState(0);
  useEffect(() => {
    if (propProgress !== undefined) {
      // Animate the progress bar
      const animationDuration = 500; // 0.5 seconds
      let startTime: number;

      const animate = (currentTime: number) => {
        if (!startTime) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const progress = Math.min(timeElapsed / animationDuration, 1); // Ensure progress doesn't exceed 1
        setAnimatedProgress(Math.round(progress * propProgress)); // Update animated progress

        if (progress < 1) {
          requestAnimationFrame(animate); // Continue animation
        }
      };

      requestAnimationFrame(animate); // Start animation
    } else {
      setAnimatedProgress(0); // Reset progress when propProgress is not defined
    }
  }, [propProgress]);

  // LD1: Define status-specific messages for different processing states
  let message = propMessage;
  if (!message) {
    switch (status) {
      case ProcessingStatus.REQUESTING:
        message = 'Requesting AI assistance...';
        break;
      case ProcessingStatus.PROCESSING:
        message = 'Generating improvement suggestions...';
        break;
      case ProcessingStatus.COMPLETED:
        message = 'AI processing complete!';
        break;
      case ProcessingStatus.ERROR:
        message = aiError?.message || 'An error occurred during AI processing.';
        break;
      default:
        message = 'Idle';
        break;
    }
  }

  // LD1: Create a progress bar component with animated width based on progress value
  const ProgressBar = () => (
    <div className="relative pt-1">
      <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-200 dark:bg-gray-700">
        <motion.div
          style={{ width: `${animatedProgress}%` }}
          className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary"
          transition={{ duration: 0.5 }}
        >
          {showPercentage && <span className="text-xs">{animatedProgress}%</span>}
        </motion.div>
      </div>
    </div>
  );

  // LD1: Render appropriate visual indicator based on current status (spinner for processing, check for completed, etc.)
  let indicatorContent: JSX.Element | null = null;

  if (status === ProcessingStatus.ERROR && aiError) {
    // LD1: For ERROR status, render Alert component with error message
    indicatorContent = (
      <Alert
        variant="error"
        message={message}
        className="mb-2"
      />
    );
  } else if (status === ProcessingStatus.IDLE) {
    // LD1: For IDLE status, render nothing or minimal placeholder based on compact mode
    if (!compact) {
      indicatorContent = <p>Ready for AI assistance.</p>;
    }
  } else if (isProcessing) {
    // LD1: For REQUESTING/PROCESSING status, render spinner and progress information
    indicatorContent = (
      <>
        <div className="flex items-center">
          <Spinner size="sm" className="mr-2" />
          <span>{message}</span>
        </div>
        {propProgress !== undefined && <ProgressBar />}
      </>
    );
  } else if (status === ProcessingStatus.COMPLETED) {
    // LD1: For COMPLETED status, render success confirmation with check icon
    indicatorContent = (
      <div className="flex items-center text-green-500">
        <span>{message}</span>
      </div>
    );
  }

  // LD1: Apply animation effects for smooth transitions between states
  const containerVariants = {
    hidden: { opacity: 0, height: 0, transition: { duration: 0.3 } },
    visible: { opacity: 1, height: 'auto', transition: { duration: 0.3 } },
  };

  // LD1: Apply compact styling when compact prop is true for space-constrained contexts
  const compactClasses = compact ? 'text-sm' : 'mb-2';

  // LD1: Include appropriate ARIA attributes for accessibility
  return (
    <motion.div
      className={classNames(
        'ai-processing-indicator',
        compactClasses,
        className
      )}
      variants={containerVariants}
      initial="hidden"
      animate={indicatorContent ? 'visible' : 'hidden'}
      role="status"
      aria-live="polite"
    >
      {indicatorContent}
    </motion.div>
  );
};
// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default AiProcessingIndicator;