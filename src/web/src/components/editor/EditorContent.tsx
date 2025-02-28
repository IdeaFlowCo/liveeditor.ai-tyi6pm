import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react'; // React v18.2.0
import { EditorState, Transaction } from 'prosemirror-state'; // v1.4.1
import { EditorView } from 'prosemirror-view'; // v1.28.1
import { Node } from 'prosemirror-model'; // v1.18.1

import {
  createEditorState,
  createEditorView,
  schema,
  getDocumentFromHtml,
  getDocumentFromText,
} from './prosemirror/setup';
import SuggestionInline from './SuggestionInline';
import { useEditorContext } from '../../contexts/EditorContext';
import useTrackChanges from '../../hooks/useTrackChanges';

/**
 * Interface defining the props for the EditorContent component
 */
interface EditorContentProps {
  /** Initial document content (HTML or plain text) */
  initialContent?: string;
  /** Whether the editor is in read-only mode */
  readOnly?: boolean;
  /** Callback function when the content changes */
  onContentChange?: (content: string) => void;
  /** Optional CSS class name for the editor container */
  className?: string;
}

/**
 * Main component for rendering the document editor content area with ProseMirror integration
 * and track changes functionality
 * @param props
 * @returns Rendered editor component
 */
const EditorContent: React.FC<EditorContentProps> = (props) => {
  // LD1: Create a ref for the editor container DOM element
  const editorContainerRef = useRef<HTMLDivElement>(null);

  // LD1: Access the editor context using useEditorContext hook
  const { updateEditorState } = useEditorContext();

  // LD1: Access track changes functionality using useTrackChanges hook
  const { scrollToChange } = useTrackChanges();

  // LD1: Initialize state for editor view and editor state
  const [view, setView] = useState<EditorView | null>(null);
  const [state, setState] = useState<EditorState>(createEditorState());

  // LD1: Handle editor initialization when component mounts
  useEffect(() => {
    if (editorContainerRef.current) {
      // LD1: Implement function to initialize the editor
      const initializeEditor = (
        container: HTMLElement,
        initialContent: string,
        readOnly: boolean
      ): EditorView => {
        // LD1: Parse initial content to create ProseMirror document node
        let doc: Node | null = null;
        if (initialContent) {
          if (initialContent.trim().startsWith('<')) {
            // LD1: Looks like HTML
            doc = getDocumentFromHtml(initialContent, schema);
          } else {
            // LD1: Plain text
            doc = getDocumentFromText(initialContent, schema);
          }
        }

        // LD1: Create initial editor state with document and plugins
        const initialState = createEditorState({ content: doc });

        // LD1: Create editor view attached to the container element
        const editorView = createEditorView(container, initialState, {
          editable: !readOnly,
          dispatchTransaction: (transaction) => {
            // LD1: Apply transaction to create a new editor state
            const newState = state.apply(transaction);

            // LD1: Update the editor view with the new state
            editorView.updateState(newState);

            // LD1: Notify the editor context of state changes
            updateEditorState(newState);
          },
        });

        return editorView;
      };

      // LD1: Initialize the editor with the container, initial content, and readOnly prop
      const editorView = initializeEditor(
        editorContainerRef.current,
        props.initialContent || '',
        props.readOnly || false
      );

      // LD1: Set the editor view in the component state
      setView(editorView);
    }

    // LD1: Clean up the editor when the component unmounts
    return () => {
      if (view) {
        view.destroy();
        setView(null);
      }
    };
  }, []);

  // LD1: Set up effect to update editor when content changes
  useEffect(() => {
    if (view && props.initialContent !== undefined) {
      // LD1: Implement function to handle updates to the editor from external sources
      const handleEditorUpdate = (content: string): void => {
        // LD1: Check if editor view exists
        if (!view) return;

        // LD1: Parse new content into ProseMirror document
        let newDoc: Node | null = null;
        if (content) {
          if (content.trim().startsWith('<')) {
            // LD1: Looks like HTML
            newDoc = getDocumentFromHtml(content, schema);
          } else {
            // LD1: Plain text
            newDoc = getDocumentFromText(content, schema);
          }
        }

        // LD1: Replace current document with new content
        const transaction = view.state.tr.replaceWith(
          0,
          view.state.doc.content.size,
          newDoc ? newDoc.content : null
        );

        // LD1: Update editor view with new state
        view.dispatch(transaction);
      };

      handleEditorUpdate(props.initialContent);
    }
  }, [props.initialContent, view]);

  // LD1: Create function to handle editor state updates
  const handleTransaction = useCallback(
    (transaction: Transaction, view: EditorView) => {
      // LD1: Apply transaction to create a new editor state
      const newState = state.apply(transaction);

      // LD1: Update the editor view with the new state
      view.updateState(newState);

      // LD1: Notify the editor context of state changes
      setState(newState);

      // LD1: Call the onContentChange callback if provided
      if (props.onContentChange) {
        props.onContentChange(newState.doc.textContent);
      }
    },
    [props.onContentChange, state]
  );

  // LD1: Implement function to handle paste events with content normalization
  const onPaste = useCallback((event: ClipboardEvent) => {
    // LD1: Prevent default paste behavior
    event.preventDefault();

    // LD1: Extract pasted content as text and HTML
    const text = event.clipboardData?.getData('text') || '';
    const html = event.clipboardData?.getData('text/html') || '';

    // LD1: Normalize content to remove problematic formatting
    const normalizedContent = html || text;

    // LD1: Parse content into appropriate ProseMirror structure
    let pasteContent: Node | null = null;
    if (normalizedContent.trim().startsWith('<')) {
      // LD1: Looks like HTML
      pasteContent = getDocumentFromHtml(normalizedContent, schema);
    } else {
      // LD1: Plain text
      pasteContent = getDocumentFromText(normalizedContent, schema);
    }

    // LD1: Insert parsed content at current selection
    if (pasteContent) {
      const transaction = view?.state.tr.replaceSelection(
        pasteContent.slice(0)
      );
      if (transaction) {
        view?.dispatch(transaction);
      }
    }
  }, [view]);

  // LD1: Return a div with proper styling as the editor container
  return (
    <div
      ref={editorContainerRef}
      className={props.className}
      style={{
        border: '1px solid #ccc',
        borderRadius: '5px',
        padding: '10px',
        minHeight: '200px',
      }}
      onPaste={onPaste}
      aria-label="Document editor"
      aria-live="polite"
      role="textbox"
      tabIndex={0}
    />
  );
};

export default EditorContent;