import { TestBed } from '@angular/core/testing';
import { JokeGeneratorService } from './joke-generator.service';
import { Api } from '../../../api/generated/api';
import { createJokeRequest } from '../../../api/generated/fn/instructor-tools/create-joke-request';
import { listJokeRequests } from '../../../api/generated/fn/instructor-tools/list-joke-requests';
import { getJokeRequest } from '../../../api/generated/fn/instructor-tools/get-joke-request';
import { deleteJokeRequest } from '../../../api/generated/fn/instructor-tools/delete-joke-request';

describe('JokeGeneratorService', () => {
  let service: JokeGeneratorService;
  let api: { invoke: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    api = { invoke: vi.fn() };
    TestBed.configureTestingModule({
      providers: [{ provide: Api, useValue: api }],
    });
    service = TestBed.inject(JokeGeneratorService);
  });

  it('creates a joke request', async () => {
    const created = { id: 1, status: 'pending', prompt: 'test' };
    api.invoke.mockResolvedValue(created);

    const result = await service.create(5, 'test prompt');

    expect(result).toEqual(created);
    expect(api.invoke).toHaveBeenCalledWith(createJokeRequest, {
      course_id: 5,
      body: { prompt: 'test prompt' },
    });
  });

  it('lists joke requests', async () => {
    const items = [{ id: 1 }];
    api.invoke.mockResolvedValue(items);

    const result = await service.list(5);

    expect(result).toEqual(items);
    expect(api.invoke).toHaveBeenCalledWith(listJokeRequests, { course_id: 5 });
  });

  it('gets a single joke request', async () => {
    const item = { id: 1 };
    api.invoke.mockResolvedValue(item);

    const result = await service.get(5, 1);

    expect(result).toEqual(item);
    expect(api.invoke).toHaveBeenCalledWith(getJokeRequest, { course_id: 5, job_id: 1 });
  });

  it('deletes a joke request', async () => {
    api.invoke.mockResolvedValue(undefined);

    await service.delete(5, 1);

    expect(api.invoke).toHaveBeenCalledWith(deleteJokeRequest, { course_id: 5, job_id: 1 });
  });
});
