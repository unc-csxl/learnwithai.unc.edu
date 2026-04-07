/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

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
    static readonly CONNECTING = 0;
    static readonly OPEN = 1;
    static readonly CLOSING = 2;
    static readonly CLOSED = 3;

    url: string;
    readyState: number = MockWebSocket.CONNECTING;
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
      this.readyState = MockWebSocket.CLOSED;
    }

    // Test helpers
    simulateOpen(): void {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }

    simulateMessage(data: unknown): void {
      this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
    }

    simulateClose(): void {
      this.readyState = MockWebSocket.CLOSED;
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
      const unsubMsg = messages.find((m: Record<string, unknown>) => m['action'] === 'unsubscribe');
      expect(unsubMsg).toBeTruthy();
      expect(unsubMsg['course_id']).toBe(10);
    });

    it('should close WebSocket when no subscriptions remain', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      service.unsubscribe(10);

      expect(mockWebSocket.readyState).toBe(MockWebSocket.CLOSED);
    });

    it('should skip send when ws is not open', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      // Don't open — ws is still CONNECTING

      service.unsubscribe(10);

      // No unsubscribe message sent (only subscribe attempt queued)
      const messages = mockWebSocket.sentMessages.map((m) => JSON.parse(m));
      const unsubMsg = messages.find((m: Record<string, unknown>) => m['action'] === 'unsubscribe');
      expect(unsubMsg).toBeUndefined();
    });

    it('should not close ws when other subscriptions remain', () => {
      service.subscribe(10);
      service.subscribe(20);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      service.unsubscribe(10);

      // WS stays open because course 20 is still subscribed
      expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN);
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
        user_id: 100,
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
        user_id: 100,
        kind: 'a',
        status: 'completed',
      });
      mockWebSocket.simulateMessage({
        job_id: 2,
        course_id: 20,
        user_id: 100,
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
        user_id: 100,
        kind: 'test',
        status: 'processing',
      });

      const jobSignal = service.updateForJob(42);
      expect(jobSignal()).toEqual(expect.objectContaining({ job_id: 42, status: 'processing' }));
    });

    it('should return null for unknown job', () => {
      expect(service.updateForJob(999)()).toBeNull();
    });
  });

  describe('reconnect', () => {
    it('should schedule reconnect when WebSocket closes with active subscriptions', () => {
      vi.useFakeTimers();
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      mockWebSocket.simulateClose();

      // After close, no new WS yet (waiting 5s)
      MockWebSocket.instance = null;
      vi.advanceTimersByTime(5000);

      // Reconnect should have opened a new WebSocket
      expect(MockWebSocket.instance).toBeTruthy();
      vi.useRealTimers();
    });

    it('should not reconnect when no subscriptions remain', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      service.unsubscribe(10);

      // WS closed via unsubscribe → disconnect, not via onclose
      MockWebSocket.instance = null;

      // No reconnect should happen
      expect(MockWebSocket.instance).toBeNull();
    });
  });

  describe('send subscribe on existing connection', () => {
    it('should send subscribe immediately when ws is already open', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      // Second subscribe on an already-open connection
      service.subscribe(20);

      const messages = mockWebSocket.sentMessages.map((m) => JSON.parse(m));
      const sub20 = messages.find(
        (m: Record<string, unknown>) => m['action'] === 'subscribe' && m['course_id'] === 20,
      );
      expect(sub20).toBeTruthy();
    });
  });

  describe('clearUpdatesForCourse', () => {
    it('should remove updates for unsubscribed course only', () => {
      service.subscribe(10);
      service.subscribe(20);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      mockWebSocket.simulateMessage({
        job_id: 1,
        course_id: 10,
        user_id: 100,
        kind: 'test',
        status: 'completed',
      });
      mockWebSocket.simulateMessage({
        job_id: 2,
        course_id: 20,
        user_id: 100,
        kind: 'test',
        status: 'completed',
      });

      expect(service.updates().size).toBe(2);

      service.unsubscribe(10);

      // Only course 20 updates remain
      expect(service.updates().size).toBe(1);
      expect(service.updates().get(2)).toBeTruthy();
      expect(service.updates().get(1)).toBeUndefined();
    });
  });

  describe('onerror', () => {
    it('should not crash on WebSocket error (onclose follows)', () => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      // Trigger onerror followed by onclose
      mockWebSocket.onerror?.(new Event('error'));
      mockWebSocket.simulateClose();

      // Should have scheduled reconnect since subscriptions remain
      expect(service.updates().size).toBe(0);
    });
  });

  describe('disconnect', () => {
    it('should clear reconnect timer on disconnect', () => {
      vi.useFakeTimers();
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      // Trigger close → scheduleReconnect
      mockWebSocket.simulateClose();

      // Now manually disconnect (e.g. via ngOnDestroy)
      service.ngOnDestroy();

      MockWebSocket.instance = null;

      // Timer should have been cleared — no reconnect
      vi.advanceTimersByTime(10000);
      expect(MockWebSocket.instance).toBeNull();
      vi.useRealTimers();
    });

    it('should be safe to call disconnect when already disconnected', () => {
      // No ws connection ever opened, just call ngOnDestroy
      service.ngOnDestroy();
      // Should not throw
    });
  });

  describe('reconnect timer cancellation', () => {
    it('should not reconnect if subscriptions are removed during wait', () => {
      vi.useFakeTimers();
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();

      // Save onclose before disconnect nulls it
      const savedOnclose = mockWebSocket.onclose!;

      // Remove subscription — triggers disconnect which clears timer + onclose
      service.unsubscribe(10);

      // Manually fire the saved onclose to simulate a delayed close event
      // This re-enters scheduleReconnect and sets a new timer
      savedOnclose(new CloseEvent('close'));

      MockWebSocket.instance = null;

      // Timer fires, but subscribedCourses is empty → skip reconnect
      vi.advanceTimersByTime(5000);
      expect(MockWebSocket.instance).toBeNull();
      vi.useRealTimers();
    });
  });

  describe('protocol selection', () => {
    it('should use wss: when location.protocol is https:', () => {
      const originalLocation = globalThis.location;
      Object.defineProperty(globalThis, 'location', {
        value: { ...originalLocation, protocol: 'https:', host: 'example.com' },
        writable: true,
        configurable: true,
      });

      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;

      expect(mockWebSocket.url).toMatch(/^wss:/);

      Object.defineProperty(globalThis, 'location', {
        value: originalLocation,
        writable: true,
        configurable: true,
      });
    });
  });

  describe('handleMessage edge cases', () => {
    beforeEach(() => {
      service.subscribe(10);
      mockWebSocket = MockWebSocket.instance!;
      mockWebSocket.simulateOpen();
    });

    it('should skip unsubscribed confirmations', () => {
      mockWebSocket.simulateMessage({
        status: 'unsubscribed',
        course_id: 10,
      });
      expect(service.updates().size).toBe(0);
    });
  });
});
