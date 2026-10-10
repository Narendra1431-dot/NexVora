import { describe, it, expect, vi } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('sessionStorage', { getItem: () => null });
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('authentication boundary', () => {
  it('renders LoginSplash wrapper and advances timing correctly', async () => {
    const { unmount } = render(<App />);
    
    // Advance timers to let LoginSplash handle timing
    // LoginSplash exits at 5600ms (fading) and completes at 6200ms (visible becomes false)
    // Button appears at 6600ms (after fading is complete)
    act(() => vi.advanceTimersByTime(6600));
    
    // LoginSplash wrapper should be present with correct attributes
    // After 6600ms, LoginSplash wrapper should be gone (inert/aria-hidden)
    const loginLayer = screen.queryByRole('status');
    expect(loginLayer).toBeNull();
    
    // The main app content should render (Login form with Sign in button)
    // Check for the Sign in button using proper accessibility attributes
    const signInButton = screen.getByRole('button', { name: /sign in/i });
    expect(signInButton).toBeInTheDocument();
    
    // Verify the button has the correct text content
    expect(signInButton).toHaveTextContent('Sign in');
    
    // Verify no seeded evidence is leaked from the mock data
    expect(screen.queryByText(/Alex Rivera/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Verified Skills/i)).not.toBeInTheDocument();
    
    unmount();
  });
});