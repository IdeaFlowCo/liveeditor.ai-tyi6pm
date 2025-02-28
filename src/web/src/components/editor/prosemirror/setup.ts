import { EditorState, Plugin, PluginKey } from 'prosemirror-state'; // v1.4.2
import { EditorView } from 'prosemirror-view'; // v1.30.2
import { Schema, DOMParser, DOMSerializer } from 'prosemirror-model'; // v1.19.0
import { dropCursor } from 'prosemirror-dropcursor'; // v1.5.0
import { gapCursor } from 'prosemirror-gapcursor'; // v1.3.1
import { inputRules, smartQuotes } from 'prosemirror-inputrules'; // v1.2.0

import { schema } from './schema';
import { createTrackChangesPlugin } from './plugins/track-changes';
import { createSuggestionsPlugin } from './plugins/suggestions';
import { historyPlugin, historyKeymap } from './plugins/history';
import { createKeymapPlugin } from './plugins/keymap';
import { createCollaborativePlugin } from './plugins/collaborative';
import { DEFAULT_EDITOR_CONFIG } from '../../../constants/editor';

/**
 * Plugin key for accessing editor setup state
 */
export const editorSetupPluginKey = new PluginKey('editorSetup');

/**
 * Creates an initial ProseMirror EditorState with all required plugins
 * @param options Configuration options
 * @returns Configured ProseMirror editor state
 */
export function createEditorState(options: {
  content?: string | Node | null;
  enableTrackChanges?: boolean;
  enableSuggestions?: boolean;
  onSave?: (state: EditorState) => void;
} = {}): EditorState {
  const {
    content = null,
    enableTrackChanges = true,
    enableSuggestions = true,
    onSave = null,
  } = options;

  // Get plugins in the right order
  const plugins = getEditorSetupPlugins({
    enableTrackChanges,
    enableSuggestions,
    onSave,
  });

  // Create initial document
  let doc = null;
  if (content) {
    if (typeof content === 'string') {
      if (content.trim().startsWith('<')) {
        // Looks like HTML
        doc = getDocumentFromHtml(content, schema);
      } else {
        // Plain text
        doc = getDocumentFromText(content, schema);
      }
    } else if ((content as Node).type) {
      // It's already a ProseMirror document
      doc = content;
    }
  }

  // Create the editor state with plugins
  return EditorState.create({
    schema,
    plugins,
    doc,
  });
}

/**
 * Creates a ProseMirror EditorView attached to a DOM element
 * @param element DOM element to attach the editor to
 * @param state Initial editor state
 * @param options Configuration options
 * @returns Configured ProseMirror editor view
 */
export function createEditorView(
  element: HTMLElement, 
  state: EditorState, 
  options: {
    handleDOMEvents?: Record<string, (view: EditorView, event: Event) => boolean>;
    editable?: boolean | (() => boolean);
    dispatchTransaction?: (tr: Transaction) => void;
    attributes?: Record<string, string>;
    transformPasted?: (slice: any) => any;
    transformCopied?: (slice: any) => any;
    handlePaste?: (view: EditorView, event: ClipboardEvent, slice: any) => boolean;
    handleDrop?: (view: EditorView, event: DragEvent, slice: any, moved: boolean) => boolean;
    handleKeyDown?: (view: EditorView, event: KeyboardEvent) => boolean;
    handleClick?: (view: EditorView, pos: number, event: MouseEvent) => boolean;
    handleDoubleClick?: (view: EditorView, pos: number, event: MouseEvent) => boolean;
    handleTripleClick?: (view: EditorView, pos: number, event: MouseEvent) => boolean;
    handleTextInput?: (view: EditorView, from: number, to: number, text: string) => boolean;
    nodeViews?: Record<string, any>;
    clipboardSerializer?: any;
    transformPastedHTML?: (html: string) => string;
    onFocus?: (view: EditorView, event: FocusEvent) => void;
    onBlur?: (view: EditorView, event: FocusEvent) => void;
  } = {}
): EditorView {
  const {
    handleDOMEvents = {},
    editable = true,
    dispatchTransaction = null,
    attributes = {},
    transformPasted = null,
    transformCopied = null,
    handlePaste = null,
    handleDrop = null,
    handleKeyDown = null,
    handleClick = null,
    handleDoubleClick = null,
    handleTripleClick = null,
    handleTextInput = null,
    nodeViews = {},
    clipboardSerializer = null,
    transformPastedHTML = null,
    onFocus = null,
    onBlur = null,
  } = options;

  // Create editor view config
  const editorViewConfig: Record<string, any> = {
    state,
    attributes: {
      class: 'prosemirror-editor',
      spellcheck: 'true',
      ...attributes
    },
    editable: typeof editable === 'function' ? editable : () => editable,
    handleDOMEvents: {
      ...handleDOMEvents,
      focus: (view: EditorView, event: FocusEvent) => {
        if (onFocus) {
          onFocus(view, event);
        }
        return false;
      },
      blur: (view: EditorView, event: FocusEvent) => {
        if (onBlur) {
          onBlur(view, event);
        }
        return false;
      },
    },
    nodeViews,
  };

  // Handle custom transaction dispatch if provided
  if (dispatchTransaction) {
    editorViewConfig.dispatchTransaction = dispatchTransaction;
  }

  // Add optional handlers if provided
  if (transformPasted) {
    editorViewConfig.transformPasted = transformPasted;
  }
  if (transformCopied) {
    editorViewConfig.transformCopied = transformCopied;
  }
  if (handlePaste) {
    editorViewConfig.handlePaste = handlePaste;
  }
  if (handleDrop) {
    editorViewConfig.handleDrop = handleDrop;
  }
  if (handleKeyDown) {
    editorViewConfig.handleKeyDown = handleKeyDown;
  }
  if (handleClick) {
    editorViewConfig.handleClick = handleClick;
  }
  if (handleDoubleClick) {
    editorViewConfig.handleDoubleClick = handleDoubleClick;
  }
  if (handleTripleClick) {
    editorViewConfig.handleTripleClick = handleTripleClick;
  }
  if (handleTextInput) {
    editorViewConfig.handleTextInput = handleTextInput;
  }
  if (clipboardSerializer) {
    editorViewConfig.clipboardSerializer = clipboardSerializer;
  }
  if (transformPastedHTML) {
    editorViewConfig.transformPastedHTML = transformPastedHTML;
  }

  // Create and return the editor view
  return new EditorView(element, editorViewConfig);
}

/**
 * Parses HTML content into a ProseMirror document
 * @param html HTML content
 * @param documentSchema Schema to use for parsing
 * @returns ProseMirror document node
 */
export function getDocumentFromHtml(html: string, documentSchema: Schema = schema): Node {
  const domNode = document.createElement('div');
  domNode.innerHTML = html;
  return DOMParser.fromSchema(documentSchema).parse(domNode);
}

/**
 * Converts plain text content into a ProseMirror document
 * @param text Plain text content
 * @param documentSchema Schema to use for parsing
 * @returns ProseMirror document node
 */
export function getDocumentFromText(text: string, documentSchema: Schema = schema): Node {
  // Split text by newlines
  const paragraphs = text.split(/\r\n|\r|\n/);
  
  // Create paragraphs
  const nodes = paragraphs.map(paragraph => {
    // Skip empty paragraphs
    if (!paragraph.trim()) {
      return documentSchema.nodes.paragraph.create();
    }
    
    // Create a text node with the paragraph content
    const textNode = documentSchema.text(paragraph);
    
    // Create a paragraph node containing the text
    return documentSchema.nodes.paragraph.create({}, textNode);
  });
  
  // Create a document containing all paragraphs
  return documentSchema.nodes.doc.create({}, nodes);
}

/**
 * Serializes a ProseMirror document to HTML
 * @param doc ProseMirror document node
 * @param documentSchema Schema to use for serializing
 * @returns HTML string representation of document
 */
export function serializeToHtml(doc: Node, documentSchema: Schema = schema): string {
  const serializer = DOMSerializer.fromSchema(documentSchema);
  const fragment = serializer.serializeFragment(doc.content);
  
  const tempDiv = document.createElement('div');
  tempDiv.appendChild(fragment);
  
  return tempDiv.innerHTML;
}

/**
 * Creates input rules for automatic text transformations
 * @param documentSchema Schema to use for input rules
 * @returns Input rules plugin
 */
export function createInputRules(documentSchema: Schema = schema): Plugin {
  // Default input rules including smart quotes
  return inputRules({
    rules: [
      ...smartQuotes,
      // Additional custom input rules would be added here
      // Examples could include automatic list creation, block quotes, etc.
    ],
  });
}

/**
 * Collects all essential editor plugins in the correct order
 * @param options Configuration options
 * @returns Array of configured ProseMirror plugins
 */
export function getEditorSetupPlugins(options: {
  enableTrackChanges?: boolean;
  enableSuggestions?: boolean;
  onSave?: (state: EditorState) => void;
} = {}): Plugin[] {
  const {
    enableTrackChanges = true,
    enableSuggestions = true,
    onSave = null,
  } = options;

  const plugins: Plugin[] = [];

  // Track changes plugin (if enabled)
  if (enableTrackChanges) {
    plugins.push(createTrackChangesPlugin({ enabled: true }));
  }

  // Suggestions plugin (if enabled)
  if (enableSuggestions) {
    plugins.push(createSuggestionsPlugin());
  }

  // History plugin for undo/redo
  plugins.push(historyPlugin);

  // Keymap plugin for keyboard shortcuts
  plugins.push(createKeymapPlugin({ onSave }));
  plugins.push(historyKeymap);

  // Input rules for smart typing
  plugins.push(createInputRules());

  // Essential editor plugins
  plugins.push(dropCursor());
  plugins.push(gapCursor());

  // Collaborative editing placeholder (for future expansion)
  plugins.push(createCollaborativePlugin());

  return plugins;
}

/**
 * Default set of editor plugins for quick setup
 */
export const defaultEditorPlugins = getEditorSetupPlugins();

export {
  createEditorState,
  createEditorView,
  getDocumentFromHtml,
  getDocumentFromText,
  serializeToHtml,
  defaultEditorPlugins,
  getEditorSetupPlugins,
  editorSetupPluginKey,
};