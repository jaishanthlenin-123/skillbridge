import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { ChatWidget } from '../components/Chat/ChatWidget';
import { Navbar } from '../components/Layout/Navbar';
import { SupportPage } from '../features/support/SupportPage';
import { api } from '../services/api';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../services/api', () => ({
  api: {
    sendAssistantChat: vi.fn(),
    sendAssistantFeedback: vi.fn().mockResolvedValue({ message: 'Saved' }),
    createSupportTicket: vi.fn(),
    lookupSupportTicket: vi.fn(),
    getSupportTickets: vi.fn().mockResolvedValue([]),
  },
}));

describe('Minimal UI Fixes: AI Support Button & Auth Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('CHANGE 1: Support Ticket Button in ChatWidget', () => {
    it('shows "Raise Support Ticket" button when user asks to raise a ticket', async () => {
      vi.mocked(api.sendAssistantChat).mockResolvedValueOnce({
        conversation_id: 'test_ticket_conv',
        answer: 'You can create a support ticket with our team by clicking the button below.',
        mode: 'deterministic_support',
        can_create_ticket: true,
      });

      render(
        <BrowserRouter>
          <ChatWidget />
        </BrowserRouter>
      );

      // Open widget
      const launcher = screen.getByLabelText(/Open AI Assistant/i);
      fireEvent.click(launcher);

      // Type ticket request
      const input = screen.getByPlaceholderText(/Ask about career planning, skills/i);
      fireEvent.change(input, { target: { value: 'I want to raise a ticket' } });
      fireEvent.submit(input.closest('form')!);

      // Wait for response and button
      await waitFor(() => {
        expect(screen.getByText(/You can create a support ticket/i)).toBeInTheDocument();
      });

      const raiseButton = screen.getByRole('button', { name: /Raise Support Ticket/i });
      expect(raiseButton).toBeInTheDocument();

      // Click button and verify navigation to /support?tab=submit
      fireEvent.click(raiseButton);
      expect(mockNavigate).toHaveBeenCalledWith('/support?tab=submit');
    });

    it('does NOT show "Raise Support Ticket" button on normal career questions', async () => {
      vi.mocked(api.sendAssistantChat).mockResolvedValueOnce({
        conversation_id: 'test_career_conv',
        answer: 'SkillBridge analyzes your resume and matches relevant software engineer jobs.',
        mode: 'deterministic_sql_faq',
        can_create_ticket: false,
      });

      render(
        <BrowserRouter>
          <ChatWidget />
        </BrowserRouter>
      );

      // Open widget
      const launcher = screen.getByLabelText(/Open AI Assistant/i);
      fireEvent.click(launcher);

      // Ask ordinary question
      const input = screen.getByPlaceholderText(/Ask about career planning, skills/i);
      fireEvent.change(input, { target: { value: 'What jobs match a React developer?' } });
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(screen.getByText(/SkillBridge analyzes your resume/i)).toBeInTheDocument();
      });

      // Confirm no "Raise Support Ticket" button is rendered
      expect(screen.queryByRole('button', { name: /Raise Support Ticket/i })).not.toBeInTheDocument();
    });
  });

  describe('CHANGE 2: Sign In and Sign Up in Top-Right Account Area', () => {
    it('displays visible Sign In and Sign Up controls when logged out (no token)', () => {
      localStorage.clear();

      render(
        <BrowserRouter>
          <Navbar />
        </BrowserRouter>
      );

      const signInLink = screen.getByRole('link', { name: /Sign In/i });
      const signUpLink = screen.getByRole('link', { name: /Sign Up/i });

      expect(signInLink).toBeInTheDocument();
      expect(signInLink).toHaveAttribute('href', '/login');

      expect(signUpLink).toBeInTheDocument();
      expect(signUpLink).toHaveAttribute('href', '/register');
    });

    it('displays visible Sign In and Sign Up controls when in guest session mode', () => {
      localStorage.setItem('skillbridge_token', 'guest-uuid-token');
      localStorage.setItem('skillbridge_is_guest', 'true');
      localStorage.setItem('skillbridge_user', JSON.stringify({ email: 'Guest Session' }));

      render(
        <BrowserRouter>
          <Navbar />
        </BrowserRouter>
      );

      const signInLink = screen.getByRole('link', { name: /Sign In/i });
      const signUpLink = screen.getByRole('link', { name: /Sign Up/i });

      expect(signInLink).toBeInTheDocument();
      expect(signUpLink).toBeInTheDocument();
    });

    it('displays user profile initials and Sign Out button when authenticated', () => {
      localStorage.setItem('skillbridge_token', 'jwt-real-user-token');
      localStorage.removeItem('skillbridge_is_guest');
      localStorage.setItem(
        'skillbridge_user',
        JSON.stringify({ first_name: 'Alex', last_name: 'Developer', email: 'alex@example.com' })
      );

      render(
        <BrowserRouter>
          <Navbar />
        </BrowserRouter>
      );

      // Profile name/initials should be visible
      expect(screen.getByText('Alex Developer')).toBeInTheDocument();
      expect(screen.getByText('A')).toBeInTheDocument(); // initial badge

      // Sign Out button should be present
      expect(screen.getByTitle(/Sign Out/i)).toBeInTheDocument();

      // Sign In / Sign Up should NOT be displayed
      expect(screen.queryByRole('link', { name: /Sign In/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Sign Up/i })).not.toBeInTheDocument();
    });
  });

  describe('SupportPage URL tab param sync', () => {
    it('opens the Submit Ticket tab by default or when ?tab=submit is present', () => {
      render(
        <MemoryRouter initialEntries={['/support?tab=submit']}>
          <SupportPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/Submit Support Ticket/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument();
    });

    it('opens the Track Ticket Status tab when ?tab=lookup is present', () => {
      render(
        <MemoryRouter initialEntries={['/support?tab=lookup']}>
          <SupportPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/e\.g\. SB-2026-12345/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Find Ticket/i })).toBeInTheDocument();
    });
  });
});
