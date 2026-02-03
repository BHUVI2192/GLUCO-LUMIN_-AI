import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface PatientData {
    patient_id: string;
    name: string;
    age: number;
    sex: string;
    bmi: number;
    skin_tone: string;
}

export const registerPatient = async (data: PatientData) => {
    const response = await api.post('/api/start_scan', data);
    return response.data;
};

export const uploadRawData = async (lines: string[]) => {
    const response = await api.post('/api/upload_raw', { lines });
    return response.data;
};

export const getResult = async (visitId: string) => {
    const response = await api.get(`/api/get_result/${visitId}`);
    return response.data;
};
