import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import App from '../App';

describe('SkillBridge Frontend Application Shell', () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.pushState({}, 'Test', '/login');
  });

  it('renders login page when unauthenticated', () => {
    render(<App />);
    expect(screen.getByText(/Welcome back to SkillBridge/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/name@company.com/i)).toBeInTheDocument();
  });

  it('renders navigation shell and dashboard when authenticated', () => {
    localStorage.setItem('skillbridge_token', 'test-token-123');
    localStorage.setItem(
      'skillbridge_user',
      JSON.stringify({
        id: '123',
        email: 'test@example.com',
        full_name: 'Test Candidate',
      })
    );
    window.history.pushState({}, 'Test', '/dashboard');

    render(<App />);
    expect(screen.getByText(/SkillBridge/i)).toBeInTheDocument();
    expect(screen.getByText(/Resume/i)).toBeInTheDocument();
    expect(screen.getByText(/Jobs/i)).toBeInTheDocument();
  });
});
