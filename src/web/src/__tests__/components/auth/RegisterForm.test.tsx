import React from 'react'; // react v18.2.0
import { screen, userEvent, waitFor } from '@testing-library/react'; // @testing-library/react v13.0.0
import { rest } from 'msw'; // msw v0.44.0
import { RegisterForm } from '../../../components/auth/RegisterForm';
import { renderWithProviders } from '../../utils/test-utils';
import { server } from '../../mocks/server';

describe('RegisterForm', () => {
  // Test suite for the RegisterForm component
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    // Setup before each test
    user = userEvent.setup();
    server.resetHandlers(); // Reset any mocks or handlers
  });

  it('renders the registration form with all required fields', async () => {
    // Test that the registration form renders with all required input fields and buttons
    renderWithProviders(<RegisterForm />);

    expect(screen.getByText(/Register/i)).toBeInTheDocument(); // Verify form title or heading exists
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument(); // Verify email input field exists
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument(); // Verify password input field exists
    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument(); // Verify name fields exist (first name, last name)
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Register/i })).toBeInTheDocument(); // Verify register/submit button exists
    expect(screen.getByText(/Already have an account?/i)).toBeInTheDocument(); // Verify link to login page exists
  });

  it('displays validation errors for empty required fields', async () => {
    // Test form validation for empty required fields
    renderWithProviders(<RegisterForm />);

    const registerButton = screen.getByRole('button', { name: /Register/i });
    await user.click(registerButton); // Click submit without filling any fields

    expect(await screen.findByText(/First Name is required/i)).toBeInTheDocument(); // Verify validation error for email field
    expect(screen.getByText(/Last Name is required/i)).toBeInTheDocument(); // Verify validation error for password field
    expect(screen.getByText(/Email is required/i)).toBeInTheDocument(); // Verify validation error for name fields
    expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    expect(screen.getByText(/You must agree to the terms and conditions/i)).toBeInTheDocument();
  });

  it('validates email format', async () => {
    // Test email format validation
    renderWithProviders(<RegisterForm />);

    const emailInput = screen.getByLabelText(/Email/i);
    await user.type(emailInput, 'notanemail'); // Type invalid email format (e.g., 'notanemail')

    expect(await screen.findByText(/Invalid email format/i)).toBeInTheDocument(); // Verify email validation error appears

    await user.clear(emailInput);
    await user.type(emailInput, 'test@example.com'); // Clear and type valid email

    await waitFor(() => {
      expect(screen.queryByText(/Invalid email format/i)).not.toBeInTheDocument(); // Verify validation error disappears
    });
  });

  it('validates password requirements', async () => {
    // Test password validation against requirements
    renderWithProviders(<RegisterForm />);

    const passwordInput = screen.getByLabelText(/Password/i);

    await user.type(passwordInput, 'short'); // Type password that's too short
    expect(await screen.findByText(/at least 10 characters long/i)).toBeInTheDocument(); // Verify password length validation error

    await user.clear(passwordInput);
    await user.type(passwordInput, 'alllowercase'); // Type password without required character types
    expect(await screen.findByText(/one uppercase letter/i)).toBeInTheDocument(); // Verify character type validation errors
    expect(screen.getByText(/one number/i)).toBeInTheDocument();
    expect(screen.getByText(/one special character/i)).toBeInTheDocument();

    await user.clear(passwordInput);
    await user.type(passwordInput, 'ValidPassword1!'); // Type valid password

    await waitFor(() => {
      expect(screen.queryByText(/at least 10 characters long/i)).not.toBeInTheDocument(); // Verify validation errors disappear
      expect(screen.queryByText(/one uppercase letter/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/one number/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/one special character/i)).not.toBeInTheDocument();
    });
  });

  it('toggles password visibility', async () => {
    // Test password visibility toggle functionality
    renderWithProviders(<RegisterForm />);

    const passwordInput = screen.getByLabelText(/Password/i);
    expect(passwordInput).toHaveAttribute('type', 'password'); // Confirm password field is of type 'password'

    const toggleButton = (await screen.findByTestId('toggle-password-visibility'));
    await user.click(toggleButton); // Click visibility toggle icon/button

    expect(passwordInput).toHaveAttribute('type', 'text'); // Confirm password field changes to type 'text'

    await user.click(toggleButton); // Click toggle again
    expect(passwordInput).toHaveAttribute('type', 'password'); // Confirm password field returns to type 'password'
  });

  it('submits form with valid data and shows success', async () => {
    // Test successful form submission with valid data
    const mockOnSuccess = jest.fn();
    renderWithProviders(<RegisterForm onSuccess={mockOnSuccess} />);

    // Mock successful API registration response
    server.use(
      rest.post(API_ROUTES.AUTH.REGISTER, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            user: {
              id: 'test-user',
              email: 'test@example.com',
              firstName: 'Test',
              lastName: 'User',
              profileImage: null,
              role: 'user',
              emailVerified: true,
              createdAt: new Date().toISOString(),
              lastLoginAt: null,
              preferences: null,
              isAnonymous: false,
            },
            token: 'test-token',
            refreshToken: 'test-refresh-token',
            expiresIn: 3600,
          })
        );
      })
    );

    const firstNameInput = screen.getByLabelText(/First Name/i);
    const lastNameInput = screen.getByLabelText(/Last Name/i);
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const agreeTermsCheckbox = screen.getByRole('checkbox', { name: /I agree to the terms and conditions/i });
    const registerButton = screen.getByRole('button', { name: /Register/i });

    await user.type(firstNameInput, 'Test'); // Fill in valid email
    await user.type(lastNameInput, 'User'); // Fill in valid password
    await user.type(emailInput, 'test@example.com'); // Fill in valid email
    await user.type(passwordInput, 'ValidPassword1!'); // Fill in valid password
    await user.click(agreeTermsCheckbox);

    await user.click(registerButton); // Click submit button

    expect(screen.getByText(/Loading/i)).toBeInTheDocument(); // Verify loading state is shown

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled(); // Verify success message appears
    });
  });

  it('handles API errors during registration', async () => {
    // Test display of API error messages during registration
    renderWithProviders(<RegisterForm />);

    // Mock API registration error response
    server.use(
      rest.post(API_ROUTES.AUTH.REGISTER, (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Internal server error' })
        );
      })
    );

    const firstNameInput = screen.getByLabelText(/First Name/i);
    const lastNameInput = screen.getByLabelText(/Last Name/i);
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const agreeTermsCheckbox = screen.getByRole('checkbox', { name: /I agree to the terms and conditions/i });
    const registerButton = screen.getByRole('button', { name: /Register/i });

    await user.type(firstNameInput, 'Test'); // Fill in all form fields with valid data
    await user.type(lastNameInput, 'User');
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'ValidPassword1!');
    await user.click(agreeTermsCheckbox);

    await user.click(registerButton); // Click submit button

    expect(await screen.findByText(/Internal server error/i)).toBeInTheDocument(); // Verify generic error message is displayed
  });

  it('handles specific error for email already in use', async () => {
    // Test handling of duplicate email error message
    renderWithProviders(<RegisterForm />);

    // Mock API 'email already exists' error response
    server.use(
      rest.post(API_ROUTES.AUTH.REGISTER, (req, res, ctx) => {
        return res(
          ctx.status(400),
          ctx.json({ message: 'Email already exists', code: 'EMAIL_EXISTS' })
        );
      })
    );

    const firstNameInput = screen.getByLabelText(/First Name/i);
    const lastNameInput = screen.getByLabelText(/Last Name/i);
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const agreeTermsCheckbox = screen.getByRole('checkbox', { name: /I agree to the terms and conditions/i });
    const registerButton = screen.getByRole('button', { name: /Register/i });

    await user.type(firstNameInput, 'Test'); // Fill in form with an email that already exists
    await user.type(lastNameInput, 'User');
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'ValidPassword1!');
    await user.click(agreeTermsCheckbox);

    await user.click(registerButton); // Click submit button

    expect(await screen.findByText(/Email already exists/i)).toBeInTheDocument(); // Verify specific error about existing email is displayed
  });

  it('navigates to login page when clicking the login link', async () => {
    // Test navigation to login page
    const mockNavigate = jest.fn();
    const routes = [
      <Route path="/register" element={<RegisterForm showLoginLink />} />,
      <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />,
    ];

    renderWithProviders(<RegisterForm showLoginLink />, {
      routerOptions: {
        routes,
        initialEntries: ['/register'],
      },
    });

    const loginLink = screen.getByText(/Login/i);
    await user.click(loginLink); // Click the link

    expect(screen.getByTestId('login-page')).toBeInTheDocument(); // Verify navigation to login page is triggered
  });
});