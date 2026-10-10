import { describe, it, expect } from 'vitest';
import {
  formatPercent,
  formatDate,
  getNodeStateBadgeColor,
  getVerificationStateBadge,
  getMilestoneStateBadge,
} from './formatters';

/**
 * formatters.ts — unit tests.
 *
 * These are pure, deterministic functions, so tests assert exact return
 * values rather than snapshots, and cover:
 *   - positive cases (documented, expected inputs)
 *   - negative cases (unknown / invalid inputs that fall through to defaults)
 *   - edge cases (empty strings, boundary numbers, casing, whitespace)
 */

describe('formatPercent', () => {
  describe('positive cases', () => {
    it('formats a whole number with a percent sign', () => {
      expect(formatPercent(50)).toBe('50%');
    });

    it('formats zero', () => {
      expect(formatPercent(0)).toBe('0%');
    });

    it('appends % to 100', () => {
      expect(formatPercent(100)).toBe('100%');
    });
  });

  describe('rounding', () => {
    it('rounds down when the fraction is below .5', () => {
      expect(formatPercent(49.4)).toBe('49%');
    });

    it('rounds up when the fraction is .5 or above', () => {
      expect(formatPercent(49.5)).toBe('50%');
    });

    it('rounds a typical decimal', () => {
      // 33.333... -> nearest integer is 33
      expect(formatPercent(100 / 3)).toBe('33%');
    });

    it('rounds 66.666... up to 67', () => {
      expect(formatPercent(200 / 3)).toBe('67%');
    });
  });

  describe('edge cases', () => {
    it('handles negative values', () => {
      expect(formatPercent(-25)).toBe('-25%');
    });

    it('handles negative values that round toward zero', () => {
      // Math.round(-0.5) === -0 in JS, which stringifies as "0"
      expect(formatPercent(-0.4)).toBe('0%');
    });

    it('handles values greater than 100', () => {
      expect(formatPercent(150)).toBe('150%');
    });

    it('handles very large values', () => {
      expect(formatPercent(1_000_000)).toBe('1000000%');
    });

    it('handles small fractional values that round to zero', () => {
      expect(formatPercent(0.4)).toBe('0%');
    });

    it('returns "NaN%" for NaN (documents current behaviour)', () => {
      // Math.round(NaN) is NaN; template interpolation yields "NaN"
      expect(formatPercent(NaN)).toBe('NaN%');
    });

    it('returns "Infinity%" for Infinity (documents current behaviour)', () => {
      expect(formatPercent(Infinity)).toBe('Infinity%');
    });

    it('returns "-Infinity%" for -Infinity (documents current behaviour)', () => {
      expect(formatPercent(-Infinity)).toBe('-Infinity%');
    });
  });
});

describe('formatDate', () => {
  describe('relative / passthrough strings', () => {
    it('returns a string containing "ago" unchanged', () => {
      expect(formatDate('2 days ago')).toBe('2 days ago');
    });

    it('returns "ago" strings unchanged regardless of position', () => {
      expect(formatDate('ago')).toBe('ago');
    });

    it('returns "yesterday" unchanged (lowercase)', () => {
      expect(formatDate('yesterday')).toBe('yesterday');
    });

    it('returns "Yesterday" unchanged (mixed case)', () => {
      expect(formatDate('Yesterday')).toBe('Yesterday');
    });

    it('returns "YESTERDAY" unchanged (uppercase)', () => {
      expect(formatDate('YESTERDAY')).toBe('YESTERDAY');
    });

    it('returns "never" unchanged (lowercase)', () => {
      expect(formatDate('never')).toBe('never');
    });

    it('returns "Never" unchanged (mixed case)', () => {
      expect(formatDate('Never')).toBe('Never');
    });

    it('matches only lowercase "ago" — uppercase "AGO" is NOT passed through', () => {
      // The guard uses a case-sensitive includes('ago'), so "AGO" falls through
      // to date parsing and becomes an Invalid Date. Documented current behaviour.
      expect(formatDate('3 hours AGO')).toBe('Invalid Date');
    });
  });

  describe('ISO / parseable date strings', () => {
    // NOTE: ISO date-only strings (e.g. "2024-03-15") are parsed as UTC midnight
    // and then rendered in the machine's LOCAL timezone, so the rendered day can
    // differ by one across timezones. Expectations below derive the expected
    // value from same Date the source builds, keeping the suite deterministic
    // on any machine / CI.
    const localRender = (input: string): string =>
      new Date(input).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    it('formats an ISO date in "Mon D, YYYY" shape', () => {
      expect(formatDate('2024-03-15')).toMatch(/^[A-Z][a-z]{2} \d{1,2}, \d{4}$/);
    });

    it('matches the locale rendering of the equivalent Date', () => {
      expect(formatDate('2024-03-15')).toBe(localRender('2024-03-15'));
    });

    it('formats a full ISO timestamp consistently with the equivalent Date', () => {
      expect(formatDate('2024-01-01T00:00:00.000Z')).toBe(localRender('2024-01-01T00:00:00.000Z'));
    });

    it('does not zero-pad single-digit days', () => {
      // The rendered day may shift by TZ, but it must never be zero-padded.
      expect(formatDate('2024-05-05')).toMatch(/^[A-Z][a-z]{2} \d, \d{4}$/);
    });
  });

  describe('edge cases', () => {
    it('parses a year-only string into a valid month/day/year rendering', () => {
      // "2024" parses to a real date rather than throwing. The rendered year can
      // shift by one across timezones (UTC parse -> local render), so assert the
      // shape and consistency with the equivalent Date rather than a fixed year.
      expect(formatDate('2024')).toMatch(/^[A-Z][a-z]{2} \d{1,2}, \d{4}$/);
      expect(formatDate('2024')).toBe(new Date('2024').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }));
    });

    it('does NOT throw on an invalid date string (documents the try/catch is unreachable for parsing)', () => {
      // new Date('not a date') does not throw; it yields an Invalid Date and
      // toLocaleDateString() returns "Invalid Date".
      const result = formatDate('not a date');
      expect(() => formatDate('not a date')).not.toThrow();
      expect(typeof result).toBe('string');
    });

    it('passes through a string containing "ago" even if it looks like a date', () => {
      expect(formatDate('ago 2024-01-01')).toBe('ago 2024-01-01');
    });

    it('handles an empty string without throwing', () => {
      expect(() => formatDate('')).not.toThrow();
      expect(typeof formatDate('')).toBe('string');
    });
  });
});

describe('getNodeStateBadgeColor', () => {
  describe('positive cases — every known state', () => {
    it.each([
      ['Verified', { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' }],
      ['Estimated', { bg: 'bg-teal-50', text: 'text-teal-700', border: 'border-teal-200', dot: 'bg-teal-500' }],
      ['In Progress', { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', dot: 'bg-blue-500' }],
      ['Skill Gap', { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200', dot: 'bg-amber-500' }],
      ['Prerequisite Gap', { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200', dot: 'bg-rose-500' }],
      ['Unverified Claim', { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300', dot: 'bg-slate-400' }],
    ] as const)('returns the correct palette for "%s"', (state: string, expected: object) => {
      expect(getNodeStateBadgeColor(state)).toEqual(expected);
    });
  });

  describe('negative cases — unknown states fall through to default', () => {
    const DEFAULT = { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200', dot: 'bg-slate-400' };

    it('returns the default palette for an unrecognised state', () => {
      expect(getNodeStateBadgeColor('Unknown')).toEqual(DEFAULT);
    });

    it('returns the default palette for an empty string', () => {
      expect(getNodeStateBadgeColor('')).toEqual(DEFAULT);
    });

    it('is case-sensitive and returns default for wrong casing', () => {
      expect(getNodeStateBadgeColor('verified')).toEqual(DEFAULT);
    });
  });

  describe('edge cases', () => {
    it('always returns all four colour keys', () => {
      const result = getNodeStateBadgeColor('anything');
      expect(Object.keys(result).sort()).toEqual(['bg', 'border', 'dot', 'text']);
    });

    it('returns a fresh object each call (no shared mutable default)', () => {
      const a = getNodeStateBadgeColor('Unknown');
      const b = getNodeStateBadgeColor('Unknown');
      expect(a).not.toBe(b);
      expect(a).toEqual(b);
    });
  });
});

describe('getVerificationStateBadge', () => {
  describe('positive cases — every known state', () => {
    it.each([
      ['Verified', { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' }],
      ['Estimated', { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200' }],
      ['Needs Review', { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' }],
      ['Unverified', { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300' }],
    ] as const)('returns the correct palette for "%s"', (state: string, expected: object) => {
      expect(getVerificationStateBadge(state)).toEqual(expected);
    });
  });

  describe('negative cases — unknown states fall through to default', () => {
    const DEFAULT = { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200' };

    it('returns the default palette for an unrecognised state', () => {
      expect(getVerificationStateBadge('Nonsense')).toEqual(DEFAULT);
    });

    it('returns the default palette for an empty string', () => {
      expect(getVerificationStateBadge('')).toEqual(DEFAULT);
    });

    it('returns default for a state that only exists in the node-badge set ("Skill Gap")', () => {
      // Guards against palette cross-contamination between the two functions.
      expect(getVerificationStateBadge('Skill Gap')).toEqual(DEFAULT);
    });
  });

  describe('edge cases', () => {
    it('always returns exactly the three colour keys (no dot)', () => {
      expect(Object.keys(getVerificationStateBadge('Verified')).sort()).toEqual(['bg', 'border', 'text']);
    });

    it('is case-sensitive', () => {
      expect(getVerificationStateBadge('verified').bg).toBe('bg-slate-50');
    });
  });
});


describe('getMilestoneStateBadge', () => {
  describe('positive cases — every known state', () => {
    it.each([
      ['Completed', { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' }],
      ['Active', { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' }],
      ['Locked', { bg: 'bg-slate-100', text: 'text-slate-500', border: 'border-slate-200' }],
      ['Blocked', { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' }],
      ['Needs Assessment', { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' }],
    ] as const)('returns the correct palette for "%s"', (state: string, expected: object) => {
      expect(getMilestoneStateBadge(state)).toEqual(expected);
    });
  });

  describe('negative cases — unknown states fall through to default', () => {
    const DEFAULT = { bg: 'bg-slate-100', text: 'text-slate-600', border: 'border-slate-200' };

    it('returns the default palette for an unrecognised state', () => {
      expect(getMilestoneStateBadge('???')).toEqual(DEFAULT);
    });

    it('returns the default palette for an empty string', () => {
      expect(getMilestoneStateBadge('')).toEqual(DEFAULT);
    });

    it('returns default for a similar-but-different state ("Complete", not "Completed")', () => {
      // Off-by-one-word guard: "Complete" must NOT match "Completed".
      expect(getMilestoneStateBadge('Complete')).toEqual(DEFAULT);
    });

    it('is case-sensitive', () => {
      expect(getMilestoneStateBadge('active')).toEqual(DEFAULT);
    });
  });

  describe('edge cases', () => {
    it('distinguishes "Locked" (slate-500 text) from the default (slate-600 text)', () => {
      expect(getMilestoneStateBadge('Locked').text).toBe('text-slate-500');
      expect(getMilestoneStateBadge('nope').text).toBe('text-slate-600');
    });

    it('always returns exactly the three colour keys', () => {
      expect(Object.keys(getMilestoneStateBadge('Active')).sort()).toEqual(['bg', 'border', 'text']);
    });
  });
});
