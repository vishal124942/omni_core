import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
    async processVideo(videoUrl: string, clientId: string, toneProfile: string) {
        try {
            const response = await axios.post(`${API_BASE_URL}/process-video`, {
                video_url: videoUrl,
                client_id: clientId,
                tone_profile: toneProfile,
            });
            return response.data;
        } catch (error: any) {
            console.error("API Error:", error.response?.data || error.message);
            throw error.response?.data?.detail || "Neural link failed. Backend unreachable.";
        }
    },

    async processVideoStream(videoUrl: string, clientId: string, toneProfile: string, platforms: string[]) {
        try {
            const response = await fetch(`${API_BASE_URL}/process-video-stream`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    client_id: clientId,
                    tone_profile: toneProfile,
                    platforms: platforms,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response;
        } catch (error: any) {
            console.error("API Stream Error:", error);
            throw error.message || "Neural link failed. Backend unreachable.";
        }
    },

    async checkHealth() {
        try {
            const response = await axios.get(`${API_BASE_URL}/health`);
            return response.data;
        } catch (error) {
            return { status: "offline" };
        }
    }
};
