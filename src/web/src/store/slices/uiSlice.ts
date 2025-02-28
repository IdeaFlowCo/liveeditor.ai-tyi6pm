import { createSlice, PayloadAction } from '@reduxjs/toolkit'; // v1.9.5

/**
 * Interface defining the shape of the UI state
 */
export interface UIState {
  sidebar: {
    isOpen: boolean;
    mode: string; // 'templates', 'chat', 'review', etc.
  };
  theme: string; // 'light', 'dark'
  modals: Record<string, { isOpen: boolean; props?: any }>;
  notification: {
    message: string;
    type: string; // 'success', 'error', 'warning', 'info'
    isVisible: boolean;
  };
  isMobile: boolean;
}

/**
 * Initial UI state
 */
const initialState: UIState = {
  sidebar: {
    isOpen: true,
    mode: 'templates',
  },
  theme: 'light',
  modals: {},
  notification: {
    message: '',
    type: 'info',
    isVisible: false,
  },
  isMobile: false,
};

/**
 * UI slice for Redux store that manages all UI-related state including
 * sidebar visibility, active mode, modals, theme, notifications, and responsive layout
 */
const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Sidebar reducers
    toggleSidebar: (state) => {
      state.sidebar.isOpen = !state.sidebar.isOpen;
    },
    setSidebarOpen: (state) => {
      state.sidebar.isOpen = true;
    },
    setSidebarClosed: (state) => {
      state.sidebar.isOpen = false;
    },
    setSidebarMode: (state, action: PayloadAction<string>) => {
      state.sidebar.mode = action.payload;
    },
    
    // Theme reducer
    setTheme: (state, action: PayloadAction<string>) => {
      state.theme = action.payload;
    },
    
    // Modal reducers
    openModal: (state, action: PayloadAction<{ modalId: string; modalProps?: any }>) => {
      const { modalId, modalProps } = action.payload;
      state.modals[modalId] = { isOpen: true, props: modalProps };
    },
    closeModal: (state, action: PayloadAction<string>) => {
      const modalId = action.payload;
      if (state.modals[modalId]) {
        state.modals[modalId].isOpen = false;
      }
    },
    
    // Notification reducers
    showNotification: (state, action: PayloadAction<{ message: string; type: string }>) => {
      const { message, type } = action.payload;
      state.notification = { message, type, isVisible: true };
    },
    clearNotification: (state) => {
      state.notification.isVisible = false;
    },
    
    // Responsive layout reducers
    setMobileView: (state, action: PayloadAction<boolean>) => {
      state.isMobile = action.payload;
      // If switching to mobile view and sidebar is open, close sidebar
      if (action.payload && state.sidebar.isOpen) {
        state.sidebar.isOpen = false;
      }
    },
  },
});

// Export actions
export const {
  toggleSidebar,
  setSidebarOpen,
  setSidebarClosed,
  setSidebarMode,
  setTheme,
  openModal,
  closeModal,
  showNotification,
  clearNotification,
  setMobileView,
} = uiSlice.actions;

/**
 * Selector to get sidebar open/closed state from Redux state
 */
export const selectSidebarOpen = (state: { ui: UIState }) => state.ui.sidebar.isOpen;

/**
 * Selector to get current sidebar active mode/tab
 */
export const selectSidebarMode = (state: { ui: UIState }) => state.ui.sidebar.mode;

/**
 * Selector to get current theme setting
 */
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;

/**
 * Selector to get state of a specific modal
 */
export const selectModalState = (state: { ui: UIState }, modalId: string) => 
  state.ui.modals[modalId]?.isOpen;

/**
 * Selector to get props for a specific modal
 */
export const selectModalProps = (state: { ui: UIState }, modalId: string) => 
  state.ui.modals[modalId]?.props;

/**
 * Selector to get current notification state
 */
export const selectNotification = (state: { ui: UIState }) => state.ui.notification;

/**
 * Selector to get current mobile view state
 */
export const selectIsMobile = (state: { ui: UIState }) => state.ui.isMobile;

// Export reducer
export const uiReducer = uiSlice.reducer;
export default uiReducer;