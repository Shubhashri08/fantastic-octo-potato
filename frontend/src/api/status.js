import { request } from './client';

export async function getSystemStatus() {
  return request('/api/status', {}, 5000);
}
