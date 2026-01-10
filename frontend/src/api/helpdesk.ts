export interface QueryRequest {
  query: string;
  department?: 'IT' | 'HR' | 'Accounting';
  trace_id?: string;
}

export interface TicketTemplate {
  department: string;
  subject: string;
  contact_email: string;
  message_template: string;
  priority: 'low' | 'medium' | 'high';
}

export interface HelpdeskResponse {
  query: string;
  action: 'answer' | 'escalate';
  answer?: string;
  confidence: number;
  citations: string[];
  ticket?: TicketTemplate;
  processing_time_ms: number;
  trace_id: string;
}

class HelpdeskAPI {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
    this.timeout = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');
  }

  async query(request: QueryRequest): Promise<HelpdeskResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseURL}/api/internal-helpdesk/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timeout - please try again');
        }
        throw error;
      }
      throw new Error('Unknown error occurred');
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      return await response.json();
    } catch {
      return { status: 'error', message: 'Cannot reach backend' };
    }
  }
}

export const helpdeskAPI = new HelpdeskAPI();