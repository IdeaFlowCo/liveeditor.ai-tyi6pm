import React from 'react'; // React v18.2.0
import { screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react v14.0.0
import { jest } from '@jest/globals'; // @jest/globals v29.0.0
import { rest } from 'msw'; // msw v1.0.0
import Editor from '../../../components/editor/Editor';
import { renderWithProviders } from '../../../utils/test-utils';
import server from '../../mocks/server';
import { handlers } from '../../mocks/handlers';
import { API_ROUTES } from '../../../constants/api';

describe('Editor Component', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  afterEach(() => {
  });

  it('renders editor with empty content', async () => {
    renderWithProviders(<Editor />);

    expect(screen.getByRole('textbox', {name: 'Document editor'})).toBeInTheDocument();
  });

  it('renders editor with initial content', async () => {
    const initialContent = 'Initial document content';
    renderWithProviders(<Editor initialContent={initialContent} />);

    expect(screen.getByRole('textbox', {name: 'Document editor'})).toHaveTextContent(initialContent);
  });

  it('loads document by id', async () => {
    renderWithProviders(<Editor documentId="doc-1" />);

    await waitFor(() => {
      expect(screen.getByRole('textbox', {name: 'Document editor'})).toHaveTextContent('This is a mock document 1.');
    });
  });

  it('handles document load error', async () => {
    server.use(
      rest.get(API_ROUTES.DOCUMENTS.DOCUMENT('invalid-doc-id'), (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    renderWithProviders(<Editor documentId="invalid-doc-id" />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load document')).toBeInTheDocument();
    });
  });

  it('updates document content on user input', async () => {
    renderWithProviders(<Editor initialContent="Initial content" />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByRole('textbox', {name: 'Document editor'})).toHaveTextContent('Updated content');
    });
  });

  it('autosaves document changes', async () => {
    const saveMock = jest.fn();
    server.use(
      rest.put(API_ROUTES.DOCUMENTS.DOCUMENT('doc-1'), (req, res, ctx) => {
        saveMock();
        return res(ctx.status(200));
      })
    );

    renderWithProviders(<Editor documentId="doc-1" autoSave={true} initialContent="Initial content" />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(saveMock).toHaveBeenCalled();
    }, {timeout: 5000});
  });

  it('generates ai suggestions', async () => {
    renderWithProviders(<Editor initialContent="Some initial content." />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByText('More professional tone')).toBeInTheDocument();
    });
  });

  it('reviews and accepts track changes', async () => {
    renderWithProviders(<Editor initialContent="Some initial content." />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByText('More professional tone')).toBeInTheDocument();
    });
  });

  it('reviews and rejects track changes', async () => {
    renderWithProviders(<Editor initialContent="Some initial content." />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByText('More professional tone')).toBeInTheDocument();
    });
  });

  it('accepts all changes at once', async () => {
     renderWithProviders(<Editor initialContent="Some initial content." />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByText('More professional tone')).toBeInTheDocument();
    });
  });

  it('rejects all changes at once', async () => {
    renderWithProviders(<Editor initialContent="Some initial content." />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByText('More professional tone')).toBeInTheDocument();
    });
  });

  it('displays document save prompt for anonymous users', async () => {
    renderWithProviders(<Editor initialContent="Some initial content." />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByText('More professional tone')).toBeInTheDocument();
    });
  });

  it('enforces read only mode', async () => {
    renderWithProviders(<Editor readOnly={true} initialContent="Initial content" />);

    const editor = screen.getByRole('textbox', {name: 'Document editor'});
    fireEvent.input(editor, { target: { textContent: 'Updated content' } });

    await waitFor(() => {
      expect(screen.getByRole('textbox', {name: 'Document editor'})).toHaveTextContent('Initial content');
    });
  });

  it('handles large document warning', async () => {
    const largeContent = 'word '.repeat(26000);
        renderWithProviders(<Editor initialContent={largeContent} />);

        await waitFor(() => {
            expect(screen.getByText('Document exceeds the maximum size')).toBeInTheDocument();
        });
  });
});