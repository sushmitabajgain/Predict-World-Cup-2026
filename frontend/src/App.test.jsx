import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import App from './App.jsx';

vi.mock('./services/api.js', () => ({
  getTeams: () => Promise.resolve([]),
  getPredictions: () => Promise.resolve([]),
  predictMatch: () => Promise.resolve({}),
  getTournament: () => Promise.resolve({ stages: ['Group Stage'], groups: ['Group A'] }),
  getNextMatch: () => Promise.resolve(null),
  getMatches: () => Promise.resolve([]),
  getStandings: () => Promise.resolve([]),
  getMatchDetail: () => Promise.resolve(null),
}));

test('renders loading state', () => {
  render(<App />);
  expect(screen.getByText(/Loading teams/i)).toBeTruthy();
});
