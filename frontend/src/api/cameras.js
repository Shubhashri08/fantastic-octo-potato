import { request } from './client';

export async function getCameras() {
  return request('/api/cameras');
}

export async function startDetection(cameraId, source, sourceType) {
  return request('/api/start_detection', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      camera_id: cameraId,
      source: source,
      source_type: sourceType
    })
  });
}

export async function stopDetection(cameraId) {
  return request(`/api/stop_detection?camera_id=${cameraId}`, {
    method: 'POST'
  });
}
