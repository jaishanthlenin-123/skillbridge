import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { FAQPage } from '../features/faq/FAQPage';
import { SupportPage } from '../features/support/SupportPage';
import { NotFoundPage } from '../features/errors/NotFoundPage';
import { ServerErrorPage } from '../features/errors/ServerErrorPage';
import { ChatWidget } from '../components/Chat/ChatWidget';
import { api } from '../services/api';

// Mock api service
vi.mock('../services/api', () => ({
  api: {
    getFAQs: vi.fn().mockResolvedValue([
      {
        id: 'faq-1',
        question: 'What is SkillBridge?',
        answer: 'SkillBridge is an explainable resume intelligence platform.',
        category_name: 'General',
        order_index: 1,
        is_active: true,
      },
      {
        id: 'faq-2',
        question: 'How do I upload a resume?',
        answer: 'Navigate to My Resumes and select your PDF file.',
        category_name: 'Resumes',
        order_index: 2,
        is_active: true,
      },
    ]),
    getFAQCategories: vi.fn().mockResolvedValue([
      { id: 'cat-1', name: 'General', slug: 'general', order_index: 1, faq_count: 1 },
      { id: 'cat-2', name: 'Resumes', slug: 'resumes', order_index: 2, faq_count: 1 },
    ]),
    createSupportTicket: vi.fn().mockResolvedValue({
      id: 'ticket-1',
      ticket_number: 'SB-2026-99999',
      contact_email: 'test@example.com',
      subject: 'Help required',
      description: 'Issue description',
      category: 'general',
      priority: 'normal',
      status: 'open',
      created_at: new Date().toISOString(),
    }),
    lookupSupportTicket: vi.fn().mockResolvedValue({
      id: 'ticket-1',
      ticket_number: 'SB-2026-99999',
      contact_email: 'test@example.com',
      subject: 'Help required',
      description: 'Issue description',
      status: 'open',
      created_at: new Date().toISOString(),
    }),
    getSupportTickets: vi.fn().mockResolvedValue([]),
    sendAssistantChat: vi.fn().mockResolvedValue({
      conversation_id: 'test_conv',
      answer: 'This is an explainable matching answer.',
      mode: 'deterministic_sql_faq',
      can_create_ticket: false,
    }),
    sendAssistantFeedback: vi.fn().mockResolvedValue({ message: 'Saved' }),
  },
}));

describe('Phase 2 Frontend Upgrades', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders FAQPage with question accordion', async () => {
    render(
      <BrowserRouter>
        <FAQPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Frequently Asked Questions/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search question keywords/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('What is SkillBridge?')).toBeInTheDocument();
    });
  });

  it('renders SupportPage and allows ticket submission form interaction', async () => {
    render(
      <BrowserRouter>
        <SupportPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Support Desk/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument();
    expect(screen.getByText(/Submit Support Ticket/i)).toBeInTheDocument();
  });

  it('renders ChatWidget launcher and opens interactive window', async () => {
    render(
      <BrowserRouter>
        <ChatWidget />
      </BrowserRouter>
    );

    const launcher = screen.getByLabelText(/Open AI Assistant/i);
    expect(launcher).toBeInTheDocument();

    fireEvent.click(launcher);

    expect(screen.getAllByText(/Career Assistant/i)[0]).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about career planning, skills/i)).toBeInTheDocument();
  });

  it('renders NotFoundPage with 404 message and recovery links', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Error 404 — Page Not Found/i)).toBeInTheDocument();
    expect(screen.getByText(/Return to Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Ask the Assistant/i)).toBeInTheDocument();
  });

  it('submits thumbs-up feedback and allows changing to thumbs-down', async () => {
    vi.mocked(api.sendAssistantFeedback).mockResolvedValue({
      message: 'Feedback received. Thank you!',
      conversation_id: 'test_conv',
      persisted_to_mongo: true,
    });

    render(
      <BrowserRouter>
        <ChatWidget />
      </BrowserRouter>
    );

    // Open chat widget
    const launcher = screen.getByLabelText(/Open AI Assistant/i);
    fireEvent.click(launcher);

    // Initial assistant welcome message has thumbs-up and thumbs-down buttons
    const thumbsUpBtn = screen.getAllByRole('button', { name: /Helpful response/i })[0];
    const thumbsDownBtn = screen.getAllByRole('button', { name: /Not helpful response/i })[0];

    expect(thumbsUpBtn).toBeInTheDocument();
    expect(thumbsDownBtn).toBeInTheDocument();

    // Click thumbs-up
    fireEvent.click(thumbsUpBtn);

    await waitFor(() => {
      expect(api.sendAssistantFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          rating: 5,
          comment: 'thumbs_up',
        })
      );
    });

    // Clicking thumbs-up again should NOT send duplicate API call
    fireEvent.click(thumbsUpBtn);
    expect(vi.mocked(api.sendAssistantFeedback)).toHaveBeenCalledTimes(1);

    // Click thumbs-down to change rating safely
    fireEvent.click(thumbsDownBtn);

    await waitFor(() => {
      expect(api.sendAssistantFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          rating: 1,
          comment: 'thumbs_down',
        })
      );
    });
    expect(vi.mocked(api.sendAssistantFeedback)).toHaveBeenCalledTimes(2);
  });

  it('automatically opens Career Assistant and submits 404 contextual question when visiting NotFoundPage', async () => {
    vi.mocked(api.sendAssistantChat).mockResolvedValue({
      conversation_id: 'conv_404_test',
      answer: 'Error 404 means the requested page or resource could not be found.',
      mode: 'grounded_error_404',
      can_create_ticket: false,
    });

    render(
      <BrowserRouter>
        <div>
          <NotFoundPage />
          <ChatWidget />
        </div>
      </BrowserRouter>
    );

    await waitFor(
      () => {
        expect(api.sendAssistantChat).toHaveBeenCalledWith(
          expect.objectContaining({
            message: 'What does error 404 mean and what should I do?',
          })
        );
      },
      { timeout: 3000 }
    );

    // Verify exactly one submission
    expect(vi.mocked(api.sendAssistantChat)).toHaveBeenCalledTimes(1);

    // Verify ChatWidget is open and displaying the assistant response
    await waitFor(() => {
      expect(screen.getByText('Error 404 means the requested page or resource could not be found.')).toBeInTheDocument();
    });
  });

  it('automatically opens Career Assistant and submits 500 contextual question when visiting ServerErrorPage', async () => {
    vi.mocked(api.sendAssistantChat).mockResolvedValue({
      conversation_id: 'conv_500_test',
      answer: 'Error 500 means an unexpected internal server error occurred.',
      mode: 'grounded_error_500',
      can_create_ticket: true,
    });

    render(
      <BrowserRouter>
        <div>
          <ServerErrorPage />
          <ChatWidget />
        </div>
      </BrowserRouter>
    );

    await waitFor(
      () => {
        expect(api.sendAssistantChat).toHaveBeenCalledWith(
          expect.objectContaining({
            message: 'What does error 500 mean and what should I do?',
          })
        );
      },
      { timeout: 3000 }
    );

    // Verify exactly one submission
    expect(vi.mocked(api.sendAssistantChat)).toHaveBeenCalledTimes(1);

    // Verify ChatWidget is open and displaying the response
    await waitFor(() => {
      expect(screen.getByText('Error 500 means an unexpected internal server error occurred.')).toBeInTheDocument();
    });
  });

  it('allows user to close the assistant on 404 page and keeps it closed', async () => {
    vi.mocked(api.sendAssistantChat).mockResolvedValue({
      conversation_id: 'conv_close_test',
      answer: '404 explanation message.',
      mode: 'grounded_error_404',
      can_create_ticket: false,
    });

    render(
      <BrowserRouter>
        <div>
          <NotFoundPage />
          <ChatWidget />
        </div>
      </BrowserRouter>
    );

    // Wait until the chat is open with the response
    await waitFor(() => {
      expect(screen.getByText('404 explanation message.')).toBeInTheDocument();
    });

    // Close the assistant
    const closeBtn = screen.getByTitle(/Close Assistant/i);
    fireEvent.click(closeBtn);

    // Verify chat window is closed and launcher button is visible
    await waitFor(() => {
      expect(screen.getByLabelText(/Open AI Assistant/i)).toBeInTheDocument();
      expect(screen.queryByTitle(/Close Assistant/i)).not.toBeInTheDocument();
    });
  });
});
