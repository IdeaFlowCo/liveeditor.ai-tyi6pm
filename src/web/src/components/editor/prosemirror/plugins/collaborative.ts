import { Plugin, PluginKey } from 'prosemirror-state'; // version ^1.4.1

/**
 * Unique key for the collaborative plugin to allow external access.
 * This will be important for future collaborative editing features
 * to identify this plugin in the editor state.
 */
export const collaborativePluginKey = new PluginKey('collaborative');

/**
 * Interface for future collaborative plugin options.
 * This is a placeholder for future configuration options.
 */
interface CollaborativePluginOptions {
  // Placeholder for future options such as:
  // - collaboration server URL
  // - user identification/roles
  // - synchronization strategies
  // - conflict resolution settings
  // - presence indication configuration
}

/**
 * Creates a minimal placeholder ProseMirror plugin for future collaborative editing functionality.
 * 
 * NOTE: This is a placeholder implementation as real-time collaborative editing
 * is explicitly out of scope for the initial release. This plugin provides the 
 * foundation for adding collaborative features in future versions.
 * 
 * Future implementation would likely include:
 * - Connection to a dedicated collaboration backend
 * - Operational Transformation (OT) or Conflict-free Replicated Data Type (CRDT)
 * - User presence and cursor/selection sharing
 * - Real-time change synchronization
 * - Conflict resolution strategies
 * - Connection state management
 * 
 * @param options Configuration options for collaborative editing (unused in this placeholder)
 * @returns A ProseMirror plugin instance with placeholder for future collaborative features
 */
export function createCollaborativePlugin(options: Partial<CollaborativePluginOptions> = {}) {
  // Return a minimal plugin that doesn't affect current editor behavior
  return new Plugin({
    key: collaborativePluginKey,
    
    // Minimal state placeholder that doesn't affect current functionality
    state: {
      init() {
        // In a future implementation, this would initialize collaboration state
        return {
          connected: false,
          users: [],
          // Other collaborative state would be initialized here
        };
      },
      
      apply(tr, state) {
        // In a future implementation, this would process transactions
        // and synchronize with remote collaborative sessions
        return state;
      }
    },
    
    // Empty view placeholder for future implementation
    view() {
      return {
        update: () => {
          // Future: Update view based on collaborative changes
        },
        destroy: () => {
          // Future: Clean up connections and resources
        }
      };
    }
    
    // Other potential hooks for future implementation:
    // - props: For decorations showing remote user selections
    // - appendTransaction: For handling incoming collaborative changes
    // - filterTransaction: For collaborative permission checks
  });
}