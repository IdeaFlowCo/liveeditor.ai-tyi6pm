import React from 'react'; // react ^18.2.0
import { LoginForm } from '../../../components/auth/LoginForm';
import { renderWithProviders, screen, waitFor, userEvent, fireEvent } from '../../utils/test-utils';
import { server } from '../../mocks/server';
import { rest } from 'msw'; // msw ^1.0.0
import { API_ROUTES } from '../../../constants/api';
import { LoginCredentials } from '../../../types/auth';

// Define mock user and login response for testing
const mockUser = { id: '1', email: 'test@example.com', firstName: 'Test', lastName: 'User', createdAt: '2023-01-01T00:00:00Z' };
const mockLoginResponse = { user: mockUser, accessToken: 'mock-access-token', refreshToken: 'mock-refresh-token', expiresIn: 3600 };

describe('LoginForm', () => {
  // Setup function run before each test to ensure a clean test environment
  beforeEach(() => {
    server.resetHandlers(); // Reset any server handlers to restore default behavior
  });

  test('renders login form with all required elements', async () => {
    // Render the LoginForm component with providers
    renderWithProviders(<LoginForm />);

    // Check for presence of login form title
    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument();

    // Check for presence of email input field
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();

    // Check for presence of password input field
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();

    // Check for presence of 'Remember me' checkbox
    expect(screen.getByLabelText(/Remember me/i)).toBeInTheDocument();

    // Check for presence of login button
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument();

    // Check for presence of 'Forgot Password' link
    expect(screen.getByText(/Forgot password?/i)).toBeInTheDocument();

    // Check for presence of 'Register' link
    expect(screen.getByText(/register here/i)).toBeInTheDocument();
  });

  test('shows validation errors when submitting empty form', async () => {
    // Render the LoginForm component
    renderWithProviders(<LoginForm />);

    // Click the submit button without filling any fields
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Verify validation error messages appear for email field
    await waitFor(() => {
      expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
    });

    // Verify validation error messages appear for password field
    await waitFor(() => {
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });
  });

  test('shows validation error for invalid email format', async () => {
    // Render the LoginForm component
    renderWithProviders(<LoginForm />);

    // Type an invalid email (e.g., 'notanemail')
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'notanemail');

    // Type a valid password
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Verify email validation error is displayed
    await waitFor(() => {
      expect(screen.getByText(/Invalid email format/i)).toBeInTheDocument();
    });
  });

  test('successfully submits form with valid credentials', async () => {
    // Set up mock server to respond to login requests
    const mockLoginHandler = rest.post(API_ROUTES.AUTH.LOGIN, (req, res, ctx) => {
      const { email, password } = req.body as LoginCredentials;
      if (email === 'test@example.com' && password === 'ValidPassword123!') {
        return res(ctx.status(200), ctx.json(mockLoginResponse));
      } else {
        return res(ctx.status(401), ctx.json({ message: 'Invalid credentials' }));
      }
    });
    server.use(mockLoginHandler);

    // Render the LoginForm component
    const { store } = renderWithProviders(<LoginForm />);

    // Fill in valid email and password
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'test@example.com');
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Verify login API call was made with correct credentials
    await waitFor(() => {
      expect(mockLoginHandler).toHaveBeenCalled();
    });

    // Verify successful login behavior (no errors shown)
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  test('shows loading state during form submission', async () => {
    // Set up mock server to respond with delay
    server.use(
      rest.post(API_ROUTES.AUTH.LOGIN, async (req, res, ctx) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return res(ctx.status(200), ctx.json(mockLoginResponse));
      })
    );

    // Render the LoginForm component
    renderWithProviders(<LoginForm />);

    // Fill in valid credentials
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'test@example.com');
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Verify loading indicator is displayed
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Sign in/i })).toHaveAttribute('aria-busy', 'true');
    });

    // Wait for response to complete
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Sign in/i })).not.toHaveAttribute('aria-busy', 'true');
    });
  });

  test('displays error message when authentication fails', async () => {
    // Set up mock server to respond with error status
    server.use(
      rest.post(API_ROUTES.AUTH.LOGIN, (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ message: 'Invalid credentials' })
        );
      })
    );

    // Render the LoginForm component
    renderWithProviders(<LoginForm />);

    // Fill in credentials
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'test@example.com');
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Wait for response to complete
    await waitFor(() => {
      expect(screen.getByRole('alert', {name: /error/i})).toBeInTheDocument();
    });

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  test('includes remember me value when checked', async () => {
    // Set up mock server to respond to login requests
    const mockLoginHandler = rest.post(API_ROUTES.AUTH.LOGIN, async (req, res, ctx) => {
      const { email, password, rememberMe } = req.body as any;
      if (email === 'test@example.com' && password === 'ValidPassword123!' && rememberMe === true) {
        return res(ctx.status(200), ctx.json(mockLoginResponse));
      } else {
        return res(ctx.status(400), ctx.json({ message: 'Invalid request' }));
      }
    });
    server.use(mockLoginHandler);

    // Render the LoginForm component
    renderWithProviders(<LoginForm />);

    // Fill in valid email and password
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'test@example.com');
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Check the remember me checkbox
    const rememberMeCheckbox = screen.getByLabelText(/Remember me/i);
    userEvent.click(rememberMeCheckbox);

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Verify login API call included rememberMe set to true
    await waitFor(() => {
      expect(mockLoginHandler).toHaveBeenCalled();
    });
  });

  test('clears error message when form values change', async () => {
    // Set up mock server to respond with error status
    server.use(
      rest.post(API_ROUTES.AUTH.LOGIN, (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ message: 'Invalid credentials' })
        );
      })
    );

    // Render the LoginForm component
    renderWithProviders(<LoginForm />);

    // Fill in credentials
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'test@example.com');
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Submit the form to trigger an error
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByRole('alert', {name: /error/i})).toBeInTheDocument();
    });

    // Modify the email field
    userEvent.type(emailInput, 'a');

    // Verify error message is cleared
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  test('navigates to register page when register link is clicked', async () => {
    // Render the LoginForm component with router provider
    const { container } = renderWithProviders(<LoginForm />, {
      routerOptions: {
        initialEntries: ['/login'],
        routes: [
          <Route path="/login" element={<LoginForm />} />,
          <Route path="/register" element={<div data-testid="register-page">Register Page</div>} />,
        ],
      },
    });

    // Find and click on the register link
    const registerLink = screen.getByText(/register here/i);
    userEvent.click(registerLink);

    // Verify navigation to register page occurs
    await waitFor(() => {
      expect(screen.getByTestId('register-page')).toBeInTheDocument();
    });
  });

  test('navigates to forgot password page when forgot password link is clicked', async () => {
    // Render the LoginForm component with router provider
    const { container } = renderWithProviders(<LoginForm />, {
      routerOptions: {
        initialEntries: ['/login'],
        routes: [
          <Route path="/login" element={<LoginForm />} />,
          <Route path="/forgot-password" element={<div data-testid="forgot-password-page">Forgot Password Page</div>} />,
        ],
      },
    });

    // Find and click on the forgot password link
    const forgotPasswordLink = screen.getByText(/Forgot password?/i);
    userEvent.click(forgotPasswordLink);

    // Verify navigation to forgot password page occurs
    await waitFor(() => {
      expect(screen.getByTestId('forgot-password-page')).toBeInTheDocument();
    });
  });

  test('calls onSuccess callback when login succeeds', async () => {
    // Set up mock server to respond successfully
    server.use(
      rest.post(API_ROUTES.AUTH.LOGIN, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockLoginResponse));
      })
    );

    // Create mock onSuccess callback function
    const onSuccess = jest.fn();

    // Render the LoginForm with onSuccess prop
    renderWithProviders(<LoginForm onSuccess={onSuccess} />);

    // Fill in valid credentials
    const emailInput = screen.getByLabelText(/Email address/i);
    userEvent.type(emailInput, 'test@example.com');
    const passwordInput = screen.getByLabelText(/Password/i);
    userEvent.type(passwordInput, 'ValidPassword123!');

    // Complete successful login flow
    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    userEvent.click(submitButton);

    // Verify onSuccess callback was called
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });
});