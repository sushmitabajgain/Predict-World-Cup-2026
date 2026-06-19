import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import App from './App.jsx';

vi.mock('./services/api.js', () => ({
  getTeams: () => Promise.resolve([]),
  getPredictions: () => Promise.resolve([]),
  predictMatch: () => Promise.resolve({}),
}));

test('renders loading state', () => {
  render(<App />);
  expect(screen.getByText(/Loading teams/i)).toBeTruthy();
});
