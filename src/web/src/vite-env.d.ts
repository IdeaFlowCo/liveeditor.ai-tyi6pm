/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly MODE: string;
  readonly BASE_URL: string;
  readonly PROD: boolean;
  readonly DEV: boolean;
  readonly SSR: boolean;
  
  // Custom environment variables for the AI writing enhancement interface
  readonly VITE_API_BASE_URL: string;
  readonly VITE_OPENAI_API_KEY: string;
  readonly VITE_AUTH0_DOMAIN: string;
  readonly VITE_AUTH0_CLIENT_ID: string;
  readonly VITE_AUTH0_AUDIENCE: string;
  readonly VITE_MAX_DOCUMENT_SIZE: string;
  
  // Allow for additional custom environment variables
  readonly [key: string]: string | boolean | undefined;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Image assets declarations
declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

// CSS module declarations
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export = classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export = classes;
}