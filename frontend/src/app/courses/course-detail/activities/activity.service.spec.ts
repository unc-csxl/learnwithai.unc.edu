import { TestBed } from '@angular/core/testing';
import { Api } from '../../../api/generated/api';
import { ActivityService } from './activity.service';

describe('ActivityService', () => {
  let service: ActivityService;
  let mockApi: { invoke: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockApi = { invoke: vi.fn() };
    TestBed.configureTestingModule({
      providers: [ActivityService, { provide: Api, useValue: mockApi }],
    });
    service = TestBed.inject(ActivityService);
  });

  it('should list activities for a course', async () => {
    const activities = [{ id: 1, title: 'A' }];
    mockApi.invoke.mockResolvedValue(activities);

    const result = await service.list(1);

    expect(result).toBe(activities);
    expect(mockApi.invoke).toHaveBeenCalledOnce();
  });

  it('should get a single activity', async () => {
    const activity = { id: 10, title: 'A', prompt: 'P' };
    mockApi.invoke.mockResolvedValue(activity);

    const result = await service.get(1, 10);

    expect(result).toBe(activity);
  });

  it('should create an IYOW activity', async () => {
    const created = { id: 10 };
    mockApi.invoke.mockResolvedValue(created);

    const result = await service.createIyow(1, {
      title: 'T',
      prompt: 'P',
      rubric: 'R',
      release_date: '2025-01-01',
      due_date: '2025-02-01',
    });

    expect(result).toBe(created);
  });

  it('should update an IYOW activity', async () => {
    const updated = { id: 10 };
    mockApi.invoke.mockResolvedValue(updated);

    const result = await service.updateIyow(1, 10, {
      title: 'T2',
      prompt: 'P2',
      rubric: 'R2',
      release_date: '2025-01-01',
      due_date: '2025-02-01',
    });

    expect(result).toBe(updated);
  });

  it('should delete an activity', async () => {
    mockApi.invoke.mockResolvedValue(undefined);

    await service.delete(1, 10);

    expect(mockApi.invoke).toHaveBeenCalledOnce();
  });

  it('should submit an IYOW response', async () => {
    const submission = { id: 100, response_text: 'My text' };
    mockApi.invoke.mockResolvedValue(submission);

    const result = await service.submitIyow(1, 10, 'My text');

    expect(result).toBe(submission);
  });

  it('should list submissions', async () => {
    const submissions = [{ id: 100 }];
    mockApi.invoke.mockResolvedValue(submissions);

    const result = await service.listSubmissions(1, 10);

    expect(result).toBe(submissions);
  });

  it('should list submissions roster', async () => {
    const roster = [{ student_pid: 111, given_name: 'A', family_name: 'B', submission: null }];
    mockApi.invoke.mockResolvedValue(roster);

    const result = await service.listSubmissionsRoster(1, 10);

    expect(result).toBe(roster);
    expect(mockApi.invoke).toHaveBeenCalledOnce();
  });

  it('should get the active submission', async () => {
    const active = { id: 100, is_active: true };
    mockApi.invoke.mockResolvedValue(active);

    const result = await service.getActiveSubmission(1, 10);

    expect(result).toBe(active);
  });

  it('should get student submission history', async () => {
    const history = [{ id: 100 }, { id: 101 }];
    mockApi.invoke.mockResolvedValue(history);

    const result = await service.getStudentHistory(1, 10, 111111111);

    expect(result).toBe(history);
    expect(mockApi.invoke).toHaveBeenCalledOnce();
  });
});
