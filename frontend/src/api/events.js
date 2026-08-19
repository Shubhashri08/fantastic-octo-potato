import { request } from './client';

export async function getEvents() {
  return request('/api/events');
}

export async function getEventReconstruction(eventId) {
  return request(`/api/events/${eventId}/reconstruction`);
}

export async function analyzeReconstruction(eventId) {
  return request('/api/reconstruction/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_id: parseInt(eventId, 10) })
  });
}
