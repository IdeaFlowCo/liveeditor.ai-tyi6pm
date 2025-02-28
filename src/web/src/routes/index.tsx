import React from 'react'; // react ^18.2.0
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'; // react-router-dom ^6.15.0

import PrivateRoute from './PrivateRoute';
import PublicRoute from './PublicRoute';
import { ROUTES } from '../constants/routes';
import Landing from '../pages/Landing';
import Login from '../pages/Login';
import Register from '../pages/Register';
import ForgotPassword from '../pages/ForgotPassword';
import ResetPassword from '../pages/ResetPassword';
import Dashboard from '../pages/Dashboard';
import Documents from '../pages/Documents';
import Settings from '../pages/Settings';
import Editor from '../pages/Editor';
import NotFound from '../pages/NotFound';

/**
 * Main routing component that defines the application's route structure using React Router v6.
 * @returns Router component tree with all application routes
 */
function AppRoutes() {
  // Define the router structure with BrowserRouter as the root component
  return (
    <BrowserRouter>
      {/* Configure Routes component to contain all route definitions */}
      <Routes>
        {/* Set up public routes for unauthenticated access: */}
        {/* - Root path (/) redirects to editor for immediate usage */}
        <Route path="/" element={<Navigate to={ROUTES.EDITOR} />} />
        {/* - Landing page route at /landing */}
        <Route path={ROUTES.LANDING} element={<Landing />} />
        
        {/* Authentication routes (/login, /register, /forgot-password, /reset-password) */}
        <Route element={<PublicRoute restrictAuthenticated />}>
          <Route path={ROUTES.LOGIN} element={<Login />} />
          <Route path={ROUTES.REGISTER} element={<Register />} />
          <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPassword />} />
          <Route path={ROUTES.RESET_PASSWORD} element={<ResetPassword />} />
        </Route>
        
        {/* - Editor route (/editor) accessible to all users */}
        <Route path={ROUTES.EDITOR} element={<Editor />} />

        {/* Set up private routes for authenticated access: */}
        <Route element={<PrivateRoute />}>
          {/* - Dashboard route (/dashboard) as user home */}
          <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
          {/* - Documents management route (/documents) */}
          <Route path={ROUTES.DOCUMENTS} element={<Documents />} />
          {/* - User settings route (/settings) */}
          <Route path={ROUTES.SETTINGS} element={<Settings />} />
          {/* - Individual document route with ID parameter (/editor/:id) */}
          <Route path={`${ROUTES.EDITOR}/:documentId`} element={<Editor />} />
        </Route>

        {/* Add catch-all route (*) for 404 handling with NotFound component */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

// Default export of the AppRoutes component for use in the main App component
export default AppRoutes;