/**
 * API service for REST endpoints.
 */

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

class ApiService {
  /**
   * Create a new room
   * @param {string} language - Programming language for the room
   * @returns {Promise<object>} Room data
   */
  async createRoom(language = 'python') {
    const response = await fetch(`${API_URL}/api/rooms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ language }),
    });

    if (!response.ok) {
      throw new Error('Failed to create room');
    }

    return response.json();
  }

  /**
   * Get room information
   * @param {string} roomId - Room identifier
   * @returns {Promise<object>} Room data
   */
  async getRoom(roomId) {
    const response = await fetch(`${API_URL}/api/rooms/${roomId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Room not found');
      }
      throw new Error('Failed to fetch room');
    }

    return response.json();
  }

  /**
   * List all rooms
   * @returns {Promise<Array>} List of rooms
   */
  async listRooms() {
    const response = await fetch(`${API_URL}/api/rooms`);

    if (!response.ok) {
      throw new Error('Failed to list rooms');
    }

    return response.json();
  }

  /**
   * Delete a room
   * @param {string} roomId - Room identifier
   * @returns {Promise<object>} Deletion result
   */
  async deleteRoom(roomId) {
    const response = await fetch(`${API_URL}/api/rooms/${roomId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete room');
    }

    return response.json();
  }
}

export default new ApiService();
