// API utility functions for the Personal Ticket Assistant

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Starts a new session and fetches initial ticket data
 * @returns {Promise<Object>} Session data including tickets
 */
export const startSession = async () => {
  const response = await fetch(`${API_BASE_URL}/api/session/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to start session: ${response.status}`);
  }
  
  return response.json();
};

/**
 * Analyzes a specific ticket
 * @param {string} ticketKey - The ticket identifier
 * @returns {Promise<Object>} Analysis data
 */
export const analyzeTicket = async (ticketKey) => {
  const response = await fetch(`${API_BASE_URL}/api/ticket/${ticketKey}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to analyze ticket: ${response.status}`);
  }
  
  return response.json();
};

/**
 * Gets the Jira URL for a ticket
 * @param {string} ticketKey - The ticket identifier
 * @returns {Promise<Object>} Object containing the ticket URL
 */
export const getTicketUrl = async (ticketKey) => {
  const response = await fetch(`${API_BASE_URL}/api/ticket/${ticketKey}/url`);
  
  if (!response.ok) {
    throw new Error(`Failed to get ticket URL: ${response.status}`);
  }
  
  return response.json();
};

export default {
  startSession,
  analyzeTicket,
  getTicketUrl
};
