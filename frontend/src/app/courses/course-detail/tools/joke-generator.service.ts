import { Injectable, inject } from '@angular/core';
import { Api } from '../../../api/generated/api';
import { createJokeRequest } from '../../../api/generated/fn/instructor-tools/create-joke-request';
import { listJokeRequests } from '../../../api/generated/fn/instructor-tools/list-joke-requests';
import { getJokeRequest } from '../../../api/generated/fn/instructor-tools/get-joke-request';
import { deleteJokeRequest } from '../../../api/generated/fn/instructor-tools/delete-joke-request';
import { JokeRequest } from '../../../api/models';

/** Handles HTTP communication with the joke generation API. */
@Injectable({ providedIn: 'root' })
export class JokeGeneratorService {
  private api = inject(Api);

  /** Submits a joke generation request for a course. */
  create(courseId: number, prompt: string): Promise<JokeRequest> {
    return this.api.invoke(createJokeRequest, {
      course_id: courseId,
      body: { prompt },
    });
  }

  /** Lists all joke generation requests for a course. */
  list(courseId: number): Promise<JokeRequest[]> {
    return this.api.invoke(listJokeRequests, { course_id: courseId });
  }

  /** Gets a single joke generation request. */
  get(courseId: number, jobId: number): Promise<JokeRequest> {
    return this.api.invoke(getJokeRequest, {
      course_id: courseId,
      job_id: jobId,
    });
  }

  /** Deletes a joke generation request. */
  delete(courseId: number, jobId: number): Promise<void> {
    return this.api.invoke(deleteJokeRequest, {
      course_id: courseId,
      job_id: jobId,
    });
  }
}
