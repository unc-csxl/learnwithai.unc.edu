import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthTokenService } from './auth-token.service';
import { JobUpdateService, JobUpdate } from './job-update.service';

describe('JobUpdateService', () => {
  let service: JobUpdateService;
  let mockWebSocket: MockWebSocket;

  // Capture the WebSocket constructor calls
  let originalWebSocket: typeof WebSocket;

  class MockWebSocket {
    static instance: MockWebSocket | null = null;

    url: string;
    readyState = WebSocket.CONNECTING;
    onopen: ((ev: Event) => void) | null = null;
    onmessage: ((ev: MessageEvent) => void) | null = null;
    onclose: ((ev: CloseEvent) => void) | null = null;
    onerror: ((ev: Event) => void) | null = null;
    sentMessages: string[] = [];

    constructor(url: string) {
      this.url = url;
      MockWebSocket.instance = this;
    }

    send(data: string): void {
      this.sentMessages.push(data);
    }

    close(): void {
      this.readyState = WebSocket.CLOSED;
    }

    // Test helpers
    simulateOpen(): void {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }

    simulateMessage(data: unknown): void {
      this.onmessage?.(
        new MessageEvent('message', { data: JSON.stringify(data) }),
      );
    }

    simulateClose(): void {
      this.readyState = WebSocket.CLOSED;
      this.onclose?.(new CloseEvent('close'));
    }
  }

  beforeEach(() => {
    originalWebSocket = globalThis.WebSocket;
    (globalThis as Record<string, unknown>)['WebSocket'] =
      MockWebSocket as unknown as typeof WebSocket;
    MockWebSocket.instance = null;

    TestBed.configureTestingModule({
      providers: [
        JobUpdateService,
        {
          provide: AuthTokenService,
          useValue: {
            getToken: vi.fn(() => 'test-jwt-token'),
            hasToken: vi.fn(() => true),
          },
        },
      ],
    });

    service = TestBed.inject(JobUpdateService);
  });

  afterEach(() => {
    service.ngOnDestroy();
    (globalThis as Record<string, unknown>)['WebSocket'] = originalWebSocket;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start with empty updates', () => {
    expect(service.updates().size).toBe(0);
  });

  describe('subscribe', () => {
    it('should open a WebSocket on first subscribe', () => {
      service.subscribe(10);
      expect(MockWebSocket.instance).toBeTruthy();
      expect(MockWebSocket.instance!.url).toContain('/api/ws/jobs?token=');
    });

    it('should include the JWT token in the URL', () => {
      service.subscribe(10);
      expect(MockWebSocket.instance!.url).toContain('token=test-jwt-token');
    });

    it('should send subscribe message after connection opens', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      expect(mockWebSocket.sentMessages).toContain(
        JSON.stringify({ action: 'subscribe', course_id: 10 }),
      );
    });

    it('should not open WebSocket without a token', () => {
      // Override with null token
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({
        providers: [
          JobUpdateService,
          {
            provide: AuthTokenService,
            useValue: {
              getToken: vi.fn(() => null),
              hasToken: vi.fn(() => false),
            },
          },
        ],
      });
      const svcNoToken = TestBed.inject(JobUpdateService);
      MockWebSocket.instance = null;

      svcNoToken.subscribe(10);
      expect(MockWebSocket.instance).toBeNull();
    });
  });

  describe('unsubscribe', () => {
    it('should send unsubscribe message', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      service.unsubscribe(10);

      const messages = mockWebSocket.sentMessages.map((m) => JSON.parse(m));
      const unsubMsg = messages.find(
        (m: Record<string, unknown>) => m['action'] === 'unsubscribe',
      );
      expect(unsubMsg).toBeTruthy();
      expect(unsubMsg['course_id']).toBe(10);
    });

    it('should close WebSocket when no subscriptions remain', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      service.unsubscribe(10);

      expect(mockWebSocket.readyState).toBe(WebSocket.CLOSED);
    });
  });

  describe('message handling', () => {
    beforeEach(() => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();
    });

    it('should store job updates in the signal', () => {
      const update: JobUpdate = {
        job_id: 1,
        course_id: 10,
        kind: 'roster_upload',
        status: 'completed',
      };
      mockWebSocket.simulateMessage(update);

      expect(service.updates().size).toBe(1);
      expect(service.updates().get(1)).toEqual(update);
    });

    it('should ignore subscribe confirmations', () => {
      mockWebSocket.simulateMessage({
        status: 'subscribed',
        course_id: 10,
      });
      expect(service.updates().size).toBe(0);
    });

    it('should ignore error messages', () => {
      mockWebSocket.simulateMessage({ error: 'Unknown action.' });
      expect(service.updates().size).toBe(0);
    });

    it('should ignore invalid messages', () => {
      mockWebSocket.simulateMessage({ something: 'else' });
      expect(service.updates().size).toBe(0);
    });
  });

  describe('updatesForCourse', () => {
    it('should filter updates by course', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      mockWebSocket.simulateMessage({
        job_id: 1,
        course_id: 10,
        kind: 'a',
        status: 'completed',
      });
      mockWebSocket.simulateMessage({
        job_id: 2,
        course_id: 20,
        kind: 'b',
        status: 'pending',
      });

      const course10 = service.updatesForCourse(10);
      expect(course10().size).toBe(1);
      expect(course10().has(1)).toBe(true);
    });
  });

  describe('updateForJob', () => {
    it('should return the latest update for a specific job', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      mockWebSocket.simulateMessage({
        job_id: 42,
        course_id: 10,
        kind: 'test',
        status: 'processing',
      });

      const jobSignal = service.updateForJob(42);
      expect(jobSignal()).toEqual(
        expect.objectContaining({ job_id: 42, status: 'processing' }),
      );
    });

    it('should return null for unknown job', () => {
      expect(service.updateForJob(999)()).toBeNull();
    });
  });
});
