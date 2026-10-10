// Test file for design system integration
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { Brand } from './Brand';

describe('Design System Integration', () => {
  it('renders brand component with premium styling', () => {
    render(<Brand />);
    const brandElement = screen.getByRole('img', { name: /NexVora/i });
    expect(brandElement).toBeInTheDocument();
    expect(brandElement).toHaveClass('brand-premium');
  });
  
  it('renders compact brand variant', () => {
    render(<Brand compact />);
    const brandElement = screen.getByRole('img', { name: /NexVora/i });
    expect(brandElement).toHaveClass('nexvora-brand--compact');
  });

  it('renders symbol-only brand variant', () => {
    render(<Brand symbolOnly />);
    const brandElement = screen.getByRole('img', { name: /NexVora/i });
    expect(brandElement).toHaveClass('nexvora-brand--symbol');
  });
});
