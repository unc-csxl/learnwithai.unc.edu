import { Injectable, inject, signal, computed, OnDestroy, NgZone } from '@angular/core';
import { AuthTokenService } from './auth-token.service';

/** Shape of a job update message received over the WebSocket. */
export interface JobUpdate {
  job_id: number;
  course_id: number;
  user_id: number;
  kind: string;
  status: string;
}

/**
 * Singleton service that manages a WebSocket connection to `/api/ws/jobs`
 * for receiving real-time job status updates.
 *
 * Connections are opened lazily on the first `subscribe()` call and closed
 * automatically when no subscriptions remain.
 */
@Injectable({ providedIn: 'root' })
export class JobUpdateService implements OnDestroy {
  private authToken = inject(AuthTokenService);
  private ngZone = inject(NgZone);

  private ws: WebSocket | null = null;
  private subscribedCourses = new Set<number>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  /** Most recent update per job_id. Cleared when relevant subscription ends. */
  private _updates = signal<ReadonlyMap<number, JobUpdate>>(new Map());
  readonly updates = this._updates.asReadonly();

  /**
   * Returns a computed signal that filters updates for a specific course.
   *
   * @param courseId The course to filter updates for.
   */
  updatesForCourse(courseId: number) {
    return computed(() => {
      const all = this._updates();
      const filtered = new Map<number, JobUpdate>();
      for (const [jobId, update] of all) {
        if (update.course_id === courseId) {
          filtered.set(jobId, update);
        }
      }
      return filtered as ReadonlyMap<number, JobUpdate>;
    });
  }

  /**
   * Returns a computed signal that provides the latest update for a single job.
   *
   * @param jobId The job to track.
   */
  updateForJob(jobId: number) {
    return computed(() => this._updates().get(jobId) ?? null);
  }

  /**
   * Subscribes to job updates for a course. Opens the WebSocket if needed.
   *
   * @param courseId The course to subscribe to.
   */
  subscribe(courseId: number): void {
    this.subscribedCourses.add(courseId);
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.connect();
    } else {
      this.sendSubscribe(courseId);
    }
  }

  /**
   * Unsubscribes from a course's job updates. Closes the WebSocket when
   * no subscriptions remain.
   *
   * @param courseId The course to unsubscribe from.
   */
  unsubscribe(courseId: number): void {
    this.subscribedCourses.delete(courseId);
    this.clearUpdatesForCourse(courseId);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'unsubscribe', course_id: courseId }));
    }

    if (this.subscribedCourses.size === 0) {
      this.disconnect();
    }
  }

  ngOnDestroy(): void {
    this.disconnect();
  }

  private connect(): void {
    this.disconnect();

    const token = this.authToken.getToken();
    if (!token) {
      return;
    }

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/api/ws/jobs?token=${encodeURIComponent(token)}`;

    this.ngZone.runOutsideAngular(() => {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        for (const courseId of this.subscribedCourses) {
          this.sendSubscribe(courseId);
        }
      };

      this.ws.onmessage = (event: MessageEvent) => {
        this.ngZone.run(() => {
          this.handleMessage(event.data);
        });
      };

      this.ws.onclose = () => {
        this.ws = null;
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        // onclose will fire after onerror, no action needed here.
      };
    });
  }

  private disconnect(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      this.ws.close();
      this.ws = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.subscribedCourses.size > 0) {
        this.connect();
      }
    }, 5000);
  }

  private sendSubscribe(courseId: number): void {
    this.ws!.send(JSON.stringify({ action: 'subscribe', course_id: courseId }));
  }

  private handleMessage(data: string): void {
    try {
      const parsed = JSON.parse(data);
      // Skip ack messages (status: 'subscribed' / 'unsubscribed') and errors
      if (parsed.status === 'subscribed' || parsed.status === 'unsubscribed' || parsed.error) {
        return;
      }
      const update = parsed as JobUpdate;
      if (typeof update.job_id !== 'number' || typeof update.course_id !== 'number') {
        return;
      }
      this._updates.update((current) => {
        const next = new Map(current);
        next.set(update.job_id, update);
        return next;
      });
    } catch {
      // Ignore unparseable messages.
    }
  }

  private clearUpdatesForCourse(courseId: number): void {
    this._updates.update((current) => {
      const next = new Map<number, JobUpdate>();
      for (const [jobId, update] of current) {
        if (update.course_id !== courseId) {
          next.set(jobId, update);
        }
      }
      return next;
    });
  }
}
