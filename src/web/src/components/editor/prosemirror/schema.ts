import { Schema, NodeSpec, MarkSpec, NodeType, MarkType, Fragment } from 'prosemirror-model'; // v1.19.0
import { nodes as baseNodes } from 'prosemirror-schema-basic'; // v1.2.1
import { marks as baseMarks } from 'prosemirror-schema-basic'; // v1.2.1
import { addListNodes } from 'prosemirror-schema-list'; // v1.2.2

/**
 * Track change types for identifying the nature of changes
 */
export const TRACK_CHANGE_TYPES = {
  DELETION: 'deletion',
  INSERTION: 'insertion',
  COMMENT: 'comment'
};

/**
 * Track change attributes for storing metadata about each change
 */
export const TRACK_CHANGE_ATTRIBUTES = {
  AUTHOR: 'author',
  TIMESTAMP: 'timestamp',
  ID: 'id',
  RESOLVED: 'resolved'
};

/**
 * Extends the base nodes with list functionality
 * @param nodes Base node specifications
 * @returns Extended nodes with list support
 */
function extendNodesWithList(nodes: Record<string, NodeSpec>): Record<string, NodeSpec> {
  return addListNodes(nodes, {
    // The node spec for ordered lists
    ordered_list: {
      content: 'list_item+',
      group: 'block',
      attrs: { order: { default: 1 } },
      parseDOM: [{ tag: 'ol', getAttrs(dom: HTMLElement) {
        return { order: dom.hasAttribute('start') ? +dom.getAttribute('start')! : 1 };
      }}],
      toDOM(node) {
        return node.attrs.order === 1 ? ['ol', 0] : ['ol', { start: node.attrs.order }, 0];
      }
    },
    // The node spec for bullet lists
    bullet_list: {
      content: 'list_item+',
      group: 'block',
      parseDOM: [{ tag: 'ul' }],
      toDOM() { return ['ul', 0]; }
    },
    // The node spec for list items
    list_item: {
      content: 'paragraph block*',
      defining: true,
      parseDOM: [{ tag: 'li' }],
      toDOM() { return ['li', 0]; }
    }
  });
}

/**
 * Creates custom node specifications for track changes functionality
 * @returns Track changes node specifications
 */
function createTrackChangesNodes(): Record<string, NodeSpec> {
  return {
    // Node for deleted content
    deletion_node: {
      inline: true,
      group: 'inline',
      attrs: {
        [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.ID]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: { default: false }
      },
      content: 'inline*',
      marks: '',
      parseDOM: [{ tag: 'span.deletion-node' }],
      toDOM(node) {
        return ['span', {
          class: 'deletion-node',
          'data-author': node.attrs[TRACK_CHANGE_ATTRIBUTES.AUTHOR],
          'data-timestamp': node.attrs[TRACK_CHANGE_ATTRIBUTES.TIMESTAMP],
          'data-id': node.attrs[TRACK_CHANGE_ATTRIBUTES.ID],
          'data-resolved': node.attrs[TRACK_CHANGE_ATTRIBUTES.RESOLVED]
        }, 0];
      }
    },
    // Node for inserted content
    insertion_node: {
      inline: true,
      group: 'inline',
      attrs: {
        [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.ID]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: { default: false }
      },
      content: 'inline*',
      marks: '',
      parseDOM: [{ tag: 'span.insertion-node' }],
      toDOM(node) {
        return ['span', {
          class: 'insertion-node',
          'data-author': node.attrs[TRACK_CHANGE_ATTRIBUTES.AUTHOR],
          'data-timestamp': node.attrs[TRACK_CHANGE_ATTRIBUTES.TIMESTAMP],
          'data-id': node.attrs[TRACK_CHANGE_ATTRIBUTES.ID],
          'data-resolved': node.attrs[TRACK_CHANGE_ATTRIBUTES.RESOLVED]
        }, 0];
      }
    }
  };
}

/**
 * Creates custom mark specifications for track changes functionality
 * @returns Track changes mark specifications
 */
function createTrackChangesMarks(): Record<string, MarkSpec> {
  return {
    // Mark for deleted content
    deletion_mark: {
      attrs: {
        [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.ID]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: { default: false }
      },
      inclusive: false,
      parseDOM: [{
        tag: 'span.deletion-mark',
        getAttrs(dom: HTMLElement) {
          return {
            [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: dom.getAttribute('data-author'),
            [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: dom.getAttribute('data-timestamp'),
            [TRACK_CHANGE_ATTRIBUTES.ID]: dom.getAttribute('data-id'),
            [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: dom.getAttribute('data-resolved') === 'true'
          };
        }
      }],
      toDOM(mark) {
        return ['span', {
          class: 'deletion-mark',
          style: 'text-decoration: line-through; color: #FF6B6B;',
          'data-author': mark.attrs[TRACK_CHANGE_ATTRIBUTES.AUTHOR],
          'data-timestamp': mark.attrs[TRACK_CHANGE_ATTRIBUTES.TIMESTAMP],
          'data-id': mark.attrs[TRACK_CHANGE_ATTRIBUTES.ID],
          'data-resolved': mark.attrs[TRACK_CHANGE_ATTRIBUTES.RESOLVED]
        }, 0];
      }
    },
    // Mark for inserted content
    insertion_mark: {
      attrs: {
        [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.ID]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: { default: false }
      },
      inclusive: false,
      parseDOM: [{
        tag: 'span.insertion-mark',
        getAttrs(dom: HTMLElement) {
          return {
            [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: dom.getAttribute('data-author'),
            [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: dom.getAttribute('data-timestamp'),
            [TRACK_CHANGE_ATTRIBUTES.ID]: dom.getAttribute('data-id'),
            [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: dom.getAttribute('data-resolved') === 'true'
          };
        }
      }],
      toDOM(mark) {
        return ['span', {
          class: 'insertion-mark',
          style: 'background-color: #E3FCEF; text-decoration: underline; color: #20A779;',
          'data-author': mark.attrs[TRACK_CHANGE_ATTRIBUTES.AUTHOR],
          'data-timestamp': mark.attrs[TRACK_CHANGE_ATTRIBUTES.TIMESTAMP],
          'data-id': mark.attrs[TRACK_CHANGE_ATTRIBUTES.ID],
          'data-resolved': mark.attrs[TRACK_CHANGE_ATTRIBUTES.RESOLVED]
        }, 0];
      }
    },
    // Mark for commented content
    comment_mark: {
      attrs: {
        [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.ID]: { default: null },
        [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: { default: false },
        text: { default: '' }
      },
      inclusive: true,
      parseDOM: [{
        tag: 'span.comment-mark',
        getAttrs(dom: HTMLElement) {
          return {
            [TRACK_CHANGE_ATTRIBUTES.AUTHOR]: dom.getAttribute('data-author'),
            [TRACK_CHANGE_ATTRIBUTES.TIMESTAMP]: dom.getAttribute('data-timestamp'),
            [TRACK_CHANGE_ATTRIBUTES.ID]: dom.getAttribute('data-id'),
            [TRACK_CHANGE_ATTRIBUTES.RESOLVED]: dom.getAttribute('data-resolved') === 'true',
            text: dom.getAttribute('data-text') || ''
          };
        }
      }],
      toDOM(mark) {
        return ['span', {
          class: 'comment-mark',
          style: 'background-color: #FFF8E1; border-bottom: 1px dotted #F9A826;',
          'data-author': mark.attrs[TRACK_CHANGE_ATTRIBUTES.AUTHOR],
          'data-timestamp': mark.attrs[TRACK_CHANGE_ATTRIBUTES.TIMESTAMP],
          'data-id': mark.attrs[TRACK_CHANGE_ATTRIBUTES.ID],
          'data-resolved': mark.attrs[TRACK_CHANGE_ATTRIBUTES.RESOLVED],
          'data-text': mark.attrs.text,
          title: mark.attrs.text
        }, 0];
      }
    }
  };
}

/**
 * Creates the complete node specifications for the editor
 * @returns Complete node specifications
 */
function createNodes(): Record<string, NodeSpec> {
  // Start with base nodes from prosemirror-schema-basic
  const extendedNodes = extendNodesWithList(baseNodes);
  
  // Add custom nodes for our editor
  const customNodes: Record<string, NodeSpec> = {
    // Overriding the base image node to add more attributes
    image: {
      inline: true,
      attrs: {
        src: {},
        alt: { default: null },
        title: { default: null },
        width: { default: null },
        height: { default: null }
      },
      group: 'inline',
      draggable: true,
      parseDOM: [{
        tag: 'img[src]',
        getAttrs(dom: HTMLElement) {
          return {
            src: dom.getAttribute('src'),
            alt: dom.getAttribute('alt'),
            title: dom.getAttribute('title'),
            width: dom.getAttribute('width'),
            height: dom.getAttribute('height')
          };
        }
      }],
      toDOM(node) {
        return ['img', node.attrs];
      }
    }
  };

  // Add track changes nodes
  const trackChangesNodes = createTrackChangesNodes();

  // Merge all nodes
  return {
    ...extendedNodes,
    ...customNodes,
    ...trackChangesNodes
  };
}

/**
 * Creates the complete mark specifications for the editor
 * @returns Complete mark specifications
 */
function createMarks(): Record<string, MarkSpec> {
  // Start with base marks from prosemirror-schema-basic
  const basicMarks = { ...baseMarks };
  
  // Add custom marks for our editor
  const customMarks: Record<string, MarkSpec> = {
    // Override the link mark to add more functionality
    link: {
      attrs: {
        href: {},
        title: { default: null },
        target: { default: '_blank' }
      },
      inclusive: false,
      parseDOM: [{
        tag: 'a[href]',
        getAttrs(dom: HTMLElement) {
          return {
            href: dom.getAttribute('href'),
            title: dom.getAttribute('title'),
            target: dom.getAttribute('target')
          };
        }
      }],
      toDOM(mark) {
        return ['a', mark.attrs, 0];
      }
    }
  };

  // Add track changes marks
  const trackChangesMarks = createTrackChangesMarks();

  // Merge all marks
  return {
    ...basicMarks,
    ...customMarks,
    ...trackChangesMarks
  };
}

/**
 * Creates the final ProseMirror schema with all nodes and marks
 * @returns Complete ProseMirror schema for the editor
 */
function createSchema(): Schema {
  const nodes = createNodes();
  const marks = createMarks();
  
  return new Schema({ nodes, marks });
}

// Create and export the node specifications
export const nodeSpecs = createNodes();

// Create and export the mark specifications
export const markSpecs = createMarks();

// Create and export the schema
export const schema = createSchema();