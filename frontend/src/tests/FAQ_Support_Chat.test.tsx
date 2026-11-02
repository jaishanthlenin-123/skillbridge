import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { FAQPage } from '../features/faq/FAQPage';
import { SupportPage } from '../features/support/SupportPage';
import { NotFoundPage } from '../features/errors/NotFoundPage';
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
});
