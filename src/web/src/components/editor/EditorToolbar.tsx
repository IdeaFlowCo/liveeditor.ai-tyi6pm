import React, { useCallback } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import { Button } from '../common/Button';
import { Tooltip } from '../common/Tooltip';
import { Dropdown } from '../common/Dropdown';
import { useEditorContext } from '../../contexts/EditorContext';
import { FORMATTING_OPTIONS, KEYBOARD_SHORTCUTS } from '../../constants/editor';
import { createFormattingCommands, isMarkActive, isBlockActive } from './prosemirror/plugins/formatting';
import {
  BoldIcon,
  ItalicIcon,
  UnderlineIcon,
  StrikethroughIcon,
  HeadingIcon,
  BulletListIcon,
  OrderedListIcon,
  UndoIcon,
  RedoIcon,
  BlockquoteIcon,
  ClearFormatIcon
} from '../../assets/icons';

/**
 * Interface for the EditorToolbar component props
 */
interface EditorToolbarProps {
  className?: string;
  disabled?: boolean;
}

/**
 * A toolbar component that provides formatting controls for the document editor with Microsoft Word-like functionality
 */
export const EditorToolbar: React.FC<EditorToolbarProps> = ({ className, disabled }) => {
  // Access editor context for state and commands
  const { editorState, editorView, trackChanges, updateEditorState } = useEditorContext();

  // Get formatting commands from context
  const { commands } = React.useMemo(() => createFormattingCommands(editorState.schema), [editorState.schema]);

  /**
   * Handles click events on formatting buttons
   * @param formatType - The type of formatting to apply
   * @param event - The React mouse event
   */
  const handleFormatClick = useCallback((formatType: string, event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault(); // Prevent default browser behavior
    if (!editorView) return;

    // Execute the formatting command for the requested format type
    commands[formatType]?.execute(editorState, updateEditorState);

    editorView.focus(); // Focus the editor after applying formatting
  }, [commands, editorState, updateEditorState, editorView]);

  /**
   * Handles selection changes in the heading dropdown
   * @param headingLevel - The selected heading level
   */
  const handleHeadingChange = useCallback((headingLevel: string) => {
    if (!editorView) return;

    // Execute the heading command with the selected level
    commands[headingLevel]?.execute(editorState, updateEditorState);

    editorView.focus(); // Focus the editor after applying the heading
  }, [commands, editorState, updateEditorState, editorView]);

  /**
   * Toggles list formatting for the current selection
   * @param listType - The type of list to toggle (bullet or ordered)
   */
  const handleListToggle = useCallback((listType: string) => {
    if (!editorView) return;

    // Execute the list toggle command for the specified list type
    commands[listType]?.execute(editorState, updateEditorState);

    editorView.focus(); // Focus the editor after applying the list formatting
  }, [commands, editorState, updateEditorState, editorView]);

  /**
   * Undoes the last change in the editor
   */
  const handleUndo = useCallback(() => {
    if (!editorView) return;

    // Execute the undo command if available
    editorView.focus(); // Focus the editor after undoing
  }, [editorView]);

  /**
   * Redoes the last undone change in the editor
   */
  const handleRedo = useCallback(() => {
    if (!editorView) return;

    // Execute the redo command if available
    editorView.focus(); // Focus the editor after redoing
  }, [editorView]);

  /**
   * Clears all formatting from the current selection
   */
  const handleClearFormat = useCallback(() => {
    if (!editorView) return;

    // Execute the clear formatting command
    editorView.focus(); // Focus the editor after clearing formatting
  }, [editorView]);

  return (
    <div className={classNames('editor-toolbar', className)}>
      {/* Heading format dropdown */}
      <Dropdown
        options={[
          { label: 'Normal', value: 'paragraph' },
          { label: 'Heading 1', value: FORMATTING_OPTIONS.HEADING1 },
          { label: 'Heading 2', value: FORMATTING_OPTIONS.HEADING2 },
          { label: 'Heading 3', value: FORMATTING_OPTIONS.HEADING3 },
        ]}
        value={
          isBlockActive('heading', editorState)
            ? `heading${editorState.selection.$from.parent.attrs.level}`
            : 'paragraph'
        }
        onChange={handleHeadingChange}
        placeholder="Normal"
        disabled={disabled}
        buttonClassName="editor-toolbar-button"
        menuClassName="editor-toolbar-dropdown-menu"
        renderTrigger={({ selectedOption, isOpen, toggleDropdown, disabled }) => (
          <Tooltip content="Heading" position="bottom">
            <Button
              variant="secondary"
              size="sm"
              onClick={toggleDropdown}
              disabled={disabled}
              className="editor-toolbar-button"
            >
              <HeadingIcon level={selectedOption?.value.replace('heading', '') as any} />
            </Button>
          </Tooltip>
        )}
      />

      {/* Text formatting buttons */}
      <Tooltip content={`Bold (${KEYBOARD_SHORTCUTS.BOLD})`} position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={(e) => handleFormatClick(FORMATTING_OPTIONS.BOLD, e)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isMarkActive(FORMATTING_OPTIONS.BOLD, editorState),
          })}
        >
          <BoldIcon />
        </Button>
      </Tooltip>
      <Tooltip content={`Italic (${KEYBOARD_SHORTCUTS.ITALIC})`} position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={(e) => handleFormatClick(FORMATTING_OPTIONS.ITALIC, e)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isMarkActive(FORMATTING_OPTIONS.ITALIC, editorState),
          })}
        >
          <ItalicIcon />
        </Button>
      </Tooltip>
      <Tooltip content={`Underline (${KEYBOARD_SHORTCUTS.UNDERLINE})`} position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={(e) => handleFormatClick(FORMATTING_OPTIONS.UNDERLINE, e)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isMarkActive(FORMATTING_OPTIONS.UNDERLINE, editorState),
          })}
        >
          <UnderlineIcon />
        </Button>
      </Tooltip>
      <Tooltip content="Strikethrough" position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={(e) => handleFormatClick('strikethrough', e)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isMarkActive('strikethrough', editorState),
          })}
        >
          <StrikethroughIcon />
        </Button>
      </Tooltip>

      {/* List formatting buttons */}
      <Tooltip content="Bullet List" position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleListToggle(FORMATTING_OPTIONS.BULLET_LIST)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isBlockActive(FORMATTING_OPTIONS.BULLET_LIST, editorState),
          })}
        >
          <BulletListIcon />
        </Button>
      </Tooltip>
      <Tooltip content="Ordered List" position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleListToggle(FORMATTING_OPTIONS.ORDERED_LIST)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isBlockActive(FORMATTING_OPTIONS.ORDERED_LIST, editorState),
          })}
        >
          <OrderedListIcon />
        </Button>
      </Tooltip>

      {/* Block formatting buttons */}
      <Tooltip content="Blockquote" position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={(e) => handleFormatClick(FORMATTING_OPTIONS.BLOCKQUOTE, e)}
          disabled={disabled}
          className={classNames('editor-toolbar-button', {
            'is-active': isBlockActive(FORMATTING_OPTIONS.BLOCKQUOTE, editorState),
          })}
        >
          <BlockquoteIcon />
        </Button>
      </Tooltip>

      {/* History buttons */}
      <Tooltip content={`Undo (${KEYBOARD_SHORTCUTS.UNDO})`} position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleUndo}
          disabled={disabled}
          className="editor-toolbar-button"
        >
          <UndoIcon />
        </Button>
      </Tooltip>
      <Tooltip content="Redo" position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleRedo}
          disabled={disabled}
          className="editor-toolbar-button"
        >
          <RedoIcon />
        </Button>
      </Tooltip>

      {/* Clear formatting button */}
      <Tooltip content="Clear Formatting" position="bottom">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleClearFormat}
          disabled={disabled}
          className="editor-toolbar-button"
        >
          <ClearFormatIcon />
        </Button>
      </Tooltip>
    </div>
  );
};