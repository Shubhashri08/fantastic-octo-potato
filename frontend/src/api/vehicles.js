import { request, uploadRequest } from './client';

/**
 * Searches vehicles by plate number or visual descriptors (type, model, color, location).
 */
export async function searchVehicle(params = {}) {
  const query = new URLSearchParams();
  if (params.plate || params.plate_number) {
    query.append('plate_number', (params.plate || params.plate_number).trim());
  }
  if (params.vehicle_type && params.vehicle_type !== 'All') {
    query.append('vehicle_type', params.vehicle_type);
  }
  if (params.vehicle_model && params.vehicle_model.trim()) {
    query.append('vehicle_model', params.vehicle_model.trim());
  }
  if (params.color && params.color !== 'All') {
    query.append('color', params.color);
  }
  if (params.location && params.location !== 'All') {
    query.append('location', params.location);
  }
  if (params.start_time) {
    query.append('start_time', params.start_time);
  }
  if (params.end_time) {
    query.append('end_time', params.end_time);
  }
  if (params.time_range && params.time_range !== 'all') {
    query.append('time_range', params.time_range);
  }
  if (params.only_stolen) {
    query.append('only_stolen', 'true');
  }

  const queryString = query.toString();
  const endpoint = queryString ? `/api/vehicles/search?${queryString}` : '/api/vehicles/search';
  return request(endpoint);
}

/**
 * Uploads a plate crop or full vehicle photograph for OCR & Re-ID matching.
 */
export async function searchVehicleByImage(file, location = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (location && location !== 'All') {
    formData.append('location', location);
  }
  return uploadRequest('/api/vehicles/search/image', formData);
}

/**
 * Retrieves paginated logged vehicles from the database.
 */
export async function getVehicles(page = 1, limit = 25) {
  return request(`/api/vehicles?page=${page}&limit=${limit}`);
}

/**
 * Retrieves a single vehicle dossier by ID.
 */
export async function getVehicle(vehicleId) {
  return request(`/api/vehicles/${encodeURIComponent(vehicleId)}`);
}

/**
 * Retrieves historical movement sightings for a specific vehicle.
 */
export async function getVehicleSightings(vehicleId) {
  return request(`/api/vehicles/${encodeURIComponent(vehicleId)}/sightings`);
}

/**
 * Flags or unflags a vehicle with reason and investigator note.
 */
export async function flagVehicle(vehicleId, isFlagged, reason = 'Stolen Vehicle', note = '') {
  return request(`/api/vehicles/${encodeURIComponent(vehicleId)}/flag`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      vehicle_id: vehicleId,
      is_flagged: isFlagged,
      reason: reason,
      note: note
    })
  });
}
