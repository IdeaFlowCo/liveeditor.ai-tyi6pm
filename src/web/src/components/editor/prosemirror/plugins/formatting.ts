import { Plugin, EditorState, Transaction } from 'prosemirror-state'; // v1.19.0
import { toggleMark, setBlockType } from 'prosemirror-commands'; // v1.4.1
import { wrapInList, liftListItem, sinkListItem } from 'prosemirror-schema-list'; // v1.2.2
import { 
  InputRule, 
  wrappingInputRule, 
  textblockTypeInputRule, 
  markInputRule, 
  inputRules 
} from 'prosemirror-inputrules'; // v1.2.0

import { EditorSchema } from '../schema';
import { FORMATTING_OPTIONS } from '../../../constants/editor';

/**
 * Interface for a formatting command that can be executed on the editor
 */
export interface FormattingCommand {
  /**
   * Execute the formatting command
   * @param state Current editor state
   * @param dispatch Function to dispatch transactions
   * @returns Boolean indicating whether the command was applied
   */
  execute: (state: EditorState, dispatch?: (tr: Transaction) => void) => boolean;
  
  /**
   * Check if the formatting is currently active
   * @param state Current editor state
   * @returns Boolean indicating whether the formatting is active
   */
  isActive: (state: EditorState) => boolean;
}

/**
 * Interface for a map of formatting commands keyed by formatting type
 */
export interface FormattingCommandMap {
  /**
   * Map of commands indexed by formatting type
   */
  commands: Record<string, FormattingCommand>;
}

/**
 * Checks if a mark is active at the current selection
 * @param type Mark type name
 * @param state Current editor state
 * @returns Boolean indicating whether the mark is active
 */
export function isMarkActive(type: string, state: EditorState): boolean {
  if (!type || !state.schema.marks[type]) return false;
  
  const { from, $from, to, empty } = state.selection;
  
  if (empty) {
    // If cursor is in empty space, check storedMarks for pending marks
    return !!state.storedMarks?.some(mark => mark.type.name === type);
  }
  
  // Check if the mark exists in the selected range
  return state.doc.rangeHasMark(from, to, state.schema.marks[type]);
}

/**
 * Checks if a block type is active at the current selection
 * @param type Node type name
 * @param state Current editor state
 * @returns Boolean indicating whether the block type is active
 */
export function isBlockActive(type: string, state: EditorState): boolean {
  if (!type || !state.schema.nodes[type]) return false;
  
  const { $from, $to } = state.selection;
  const nodeType = state.schema.nodes[type];
  
  // Check if the parent node is of the specified type
  return $from.parent.type === nodeType && $from.parent === $to.parent;
}

/**
 * Checks if a list type is active at the current selection
 * @param type List node type name
 * @param state Current editor state
 * @returns Boolean indicating whether the list type is active
 */
export function isListActive(type: string, state: EditorState): boolean {
  if (!type || !state.schema.nodes[type]) return false;
  
  const { $from } = state.selection;
  const nodeType = state.schema.nodes[type];
  
  // Check through ancestor nodes for the list type
  for (let depth = $from.depth; depth > 0; depth--) {
    if ($from.node(depth).type === nodeType) {
      return true;
    }
  }
  
  return false;
}

/**
 * Creates a map of formatting commands for the editor
 * @param schema Editor schema with node and mark definitions
 * @returns Map of formatting commands
 */
export function createFormattingCommands(schema: EditorSchema): FormattingCommandMap {
  const commands: Record<string, FormattingCommand> = {};
  
  // Mark toggle commands for character formatting
  if (schema.marks.bold) {
    commands[FORMATTING_OPTIONS.BOLD] = {
      execute: toggleMark(schema.marks.bold),
      isActive: (state) => isMarkActive('bold', state)
    };
  }
  
  if (schema.marks.em) {
    commands[FORMATTING_OPTIONS.ITALIC] = {
      execute: toggleMark(schema.marks.em),
      isActive: (state) => isMarkActive('em', state)
    };
  }
  
  if (schema.marks.underline) {
    commands[FORMATTING_OPTIONS.UNDERLINE] = {
      execute: toggleMark(schema.marks.underline),
      isActive: (state) => isMarkActive('underline', state)
    };
  }
  
  // Heading commands for different heading levels
  if (schema.nodes.heading) {
    commands[FORMATTING_OPTIONS.HEADING1] = {
      execute: setBlockType(schema.nodes.heading, { level: 1 }),
      isActive: (state) => {
        return isBlockActive('heading', state) && 
               state.selection.$from.parent.attrs.level === 1;
      }
    };
    
    commands[FORMATTING_OPTIONS.HEADING2] = {
      execute: setBlockType(schema.nodes.heading, { level: 2 }),
      isActive: (state) => {
        return isBlockActive('heading', state) && 
               state.selection.$from.parent.attrs.level === 2;
      }
    };
    
    commands[FORMATTING_OPTIONS.HEADING3] = {
      execute: setBlockType(schema.nodes.heading, { level: 3 }),
      isActive: (state) => {
        return isBlockActive('heading', state) && 
               state.selection.$from.parent.attrs.level === 3;
      }
    };
  }
  
  // Paragraph command to reset to normal text
  if (schema.nodes.paragraph) {
    commands['paragraph'] = {
      execute: setBlockType(schema.nodes.paragraph),
      isActive: (state) => isBlockActive('paragraph', state)
    };
  }
  
  // List commands for bullet and ordered lists
  if (schema.nodes.bullet_list) {
    commands[FORMATTING_OPTIONS.BULLET_LIST] = {
      execute: wrapInList(schema.nodes.bullet_list),
      isActive: (state) => isListActive('bullet_list', state)
    };
  }
  
  if (schema.nodes.ordered_list) {
    commands[FORMATTING_OPTIONS.ORDERED_LIST] = {
      execute: wrapInList(schema.nodes.ordered_list),
      isActive: (state) => isListActive('ordered_list', state)
    };
  }
  
  // List item indentation commands
  if (schema.nodes.list_item) {
    commands['lift_list_item'] = {
      execute: liftListItem(schema.nodes.list_item),
      isActive: () => false // No active state for this command
    };
    
    commands['sink_list_item'] = {
      execute: sinkListItem(schema.nodes.list_item),
      isActive: () => false // No active state for this command
    };
  }
  
  // Block quote command
  if (schema.nodes.blockquote) {
    commands[FORMATTING_OPTIONS.BLOCKQUOTE] = {
      execute: (state, dispatch) => {
        // If already in a blockquote, set to paragraph instead
        if (isBlockActive('blockquote', state)) {
          return setBlockType(schema.nodes.paragraph)(state, dispatch);
        }
        return setBlockType(schema.nodes.blockquote)(state, dispatch);
      },
      isActive: (state) => isBlockActive('blockquote', state)
    };
  }
  
  // Code block command
  if (schema.nodes.code_block) {
    commands[FORMATTING_OPTIONS.CODE_BLOCK] = {
      execute: (state, dispatch) => {
        // If already in a code block, set to paragraph instead
        if (isBlockActive('code_block', state)) {
          return setBlockType(schema.nodes.paragraph)(state, dispatch);
        }
        return setBlockType(schema.nodes.code_block)(state, dispatch);
      },
      isActive: (state) => isBlockActive('code_block', state)
    };
  }
  
  return { commands };
}

/**
 * Creates input rules for markdown-style formatting shortcuts
 * @param schema Editor schema with node and mark definitions
 * @returns Array of input rules for formatting shortcuts
 */
export function createFormattingInputRules(schema: EditorSchema): InputRule[] {
  const rules: InputRule[] = [];
  
  // Heading rules for markdown-style headings
  if (schema.nodes.heading) {
    // # heading 1
    rules.push(
      textblockTypeInputRule(/^# (.*)$/, schema.nodes.heading, { level: 1 })
    );
    
    // ## heading 2
    rules.push(
      textblockTypeInputRule(/^## (.*)$/, schema.nodes.heading, { level: 2 })
    );
    
    // ### heading 3
    rules.push(
      textblockTypeInputRule(/^### (.*)$/, schema.nodes.heading, { level: 3 })
    );
  }
  
  // List rules for markdown-style lists
  if (schema.nodes.bullet_list) {
    // * or - for bullet lists
    rules.push(
      wrappingInputRule(
        /^\s*([-*]) (.*)$/,
        schema.nodes.bullet_list
      )
    );
  }
  
  if (schema.nodes.ordered_list) {
    // 1. for ordered lists
    rules.push(
      wrappingInputRule(
        /^\s*(\d+)\. (.*)$/,
        schema.nodes.ordered_list,
        (match) => ({ order: +match[1] }),
        (match, node) => node.childCount + node.attrs.order
      )
    );
  }
  
  // Block quote rule for markdown-style blockquotes
  if (schema.nodes.blockquote) {
    // > for blockquotes
    rules.push(
      wrappingInputRule(/^\s*> (.*)$/, schema.nodes.blockquote)
    );
  }
  
  // Mark rules for markdown-style text formatting
  if (schema.marks.bold) {
    // **bold** or __bold__
    rules.push(
      markInputRule(/(?:\*\*|__)([^*_]+)(?:\*\*|__)$/, schema.marks.bold)
    );
  }
  
  if (schema.marks.em) {
    // *italic* or _italic_
    rules.push(
      markInputRule(/(?:\*|_)([^*_]+)(?:\*|_)$/, schema.marks.em)
    );
  }
  
  if (schema.marks.code) {
    // `code`
    rules.push(
      markInputRule(/(?:`)([^`]+)(?:`)$/, schema.marks.code)
    );
  }
  
  return rules;
}

/**
 * Creates a ProseMirror plugin for formatting functionality
 * @param schema Editor schema with node and mark definitions
 * @returns Plugin that provides formatting functionality
 */
export function createFormattingPlugin(schema: EditorSchema): Plugin {
  // Create input rules for markdown-style formatting shortcuts
  const inputRulesList = createFormattingInputRules(schema);
  
  // Return the plugin created from the input rules
  return inputRules({ rules: inputRulesList });
}