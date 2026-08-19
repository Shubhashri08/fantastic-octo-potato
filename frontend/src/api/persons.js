import { request } from './client';

export async function getVideoEvidenceSources() {
  return request('/api/person/videos');
}

export async function uploadVideoEvidence(file, sourceName = '', location = '') {
  const formData = new FormData();
  formData.append('file', file);

  const query = new URLSearchParams();
  if (sourceName) query.append('source_name', sourceName);
  if (location) query.append('location', location);

  const res = await fetch(`/api/person/videos/upload?${query.toString()}`, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errData.detail || 'Failed to upload video evidence.');
  }

  return res.json();
}

export async function deleteVideoEvidence(sourceId) {
  return request(`/api/person/videos/${sourceId}`, {
    method: 'DELETE'
  });
}

export async function searchPersonEvidence(imageFile, minSimilarity = 0.50, sourceId = 'ALL', timeWindow = 'all', limit = 5) {
  const formData = new FormData();
  formData.append('file', imageFile);

  const query = new URLSearchParams({
    min_similarity: minSimilarity.toString(),
    limit: limit.toString()
  });

  if (sourceId && sourceId !== 'ALL' && sourceId !== 'All') {
    query.append('location', sourceId);
  }
  if (timeWindow && timeWindow !== 'all' && timeWindow !== 'ALL') {
    query.append('time_window', timeWindow);
  }

  const res = await fetch(`/api/person/search?${query.toString()}`, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Search failed' }));
    throw new Error(errData.detail || 'Person ReID search failed.');
  }

  return res.json();
}
