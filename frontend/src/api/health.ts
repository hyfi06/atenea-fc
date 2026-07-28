import { apiGet } from './client'

export interface HealthResponse {
  status: string
}

export const getHealth = () => apiGet<HealthResponse>('/api/health/')
