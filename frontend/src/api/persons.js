import { request } from './client';

export async function getVideoEvidenceSources() {
  return request('/api/person/videos');
}

export async function uploadVideoEvidence(file, sourceName = '', camera_id = 'CAM-01', location = '') {
  const formData = new FormData();
  formData.append('file', file);

  const query = new URLSearchParams();
  if (sourceName) query.append('source_name', sourceName);
  if (camera_id) query.append('camera_id', camera_id);
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

export async function searchPersonEvidence(imageFile, minSimilarity = 0.50, camera_id = 'ALL', timeWindow = 'all', limit = 10) {
  const formData = new FormData();
  formData.append('file', imageFile);

  const query = new URLSearchParams({
    min_similarity: minSimilarity.toString(),
    limit: limit.toString()
  });

  if (camera_id && camera_id !== 'ALL' && camera_id !== 'All') {
    query.append('camera_id', camera_id);
  }
  if (timeWindow && timeWindow !== 'all' && timeWindow !== 'ALL') {
    query.append('time_window', timeWindow);
  }

  const res = await fetch(`/api/person/search?${query.toString()}`, {
    method: 'POST',
    body: formData
  });

  const data = await res.json().catch(() => ({ status: 'error', message: 'Search network response failed.' }));

  if (!res.ok || data.status === 'error') {
    const errorMsg = data.message || data.detail || 'Person ReID search failed.';
    const err = new Error(errorMsg);
    err.errorCode = data.error_code || 'SEARCH_ERROR';
    throw err;
  }

  return data;
}
