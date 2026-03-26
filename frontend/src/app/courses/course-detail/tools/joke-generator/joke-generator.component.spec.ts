import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { signal, WritableSignal } from '@angular/core';
import { JokeGenerator } from './joke-generator.component';
import { JokeGeneratorService } from '../joke-generator.service';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { JobUpdateService, JobUpdate } from '../../../../job-update.service';
import { JokeRequest } from '../../../../api/models';

const fakeRequest: JokeRequest = {
  id: 1,
  status: 'completed',
  prompt: 'Tell me jokes about recursion',
  jokes: ['Why do recursive functions never finish? Because they keep calling themselves!'],
  created_at: '2025-01-01T00:00:00Z',
  completed_at: '2025-01-01T00:01:00Z',
};

const fakePendingRequest: JokeRequest = {
  id: 2,
  status: 'pending',
  prompt: 'Jokes about algorithms',
  jokes: [],
  created_at: '2025-01-01T00:02:00Z',
  completed_at: null,
};

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('JokeGenerator', () => {
  let jobUpdateSignal: WritableSignal<JobUpdate | null>;

  async function setup(options: { requests?: JokeRequest[]; listError?: boolean } = {}) {
    jobUpdateSignal = signal<JobUpdate | null>(null);

    const mockService = {
      list: options.listError
        ? vi.fn(() => Promise.reject(new Error('fail')))
        : vi.fn(() => Promise.resolve(options.requests ?? [fakeRequest])),
      create: vi.fn(() => Promise.resolve(fakePendingRequest)),
      get: vi.fn(() =>
        Promise.resolve({ ...fakePendingRequest, status: 'completed' as const, jokes: ['Ha!'] }),
      ),
      delete: vi.fn(() => Promise.resolve()),
    };

    const mockJobUpdate = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn(() => jobUpdateSignal.asReadonly()),
    };

    const mockSnackbar = { open: vi.fn() };

    const mockRoute = {
      parent: {
        parent: { snapshot: { paramMap: new Map([['id', '1']]) } },
      },
    };

    TestBed.configureTestingModule({
      imports: [JokeGenerator, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: JokeGeneratorService, useValue: mockService },
        { provide: JobUpdateService, useValue: mockJobUpdate },
        { provide: SuccessSnackbarService, useValue: mockSnackbar },
        {
          provide: PageTitleService,
          useValue: { title: vi.fn(), setTitle: vi.fn() },
        },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(JokeGenerator);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();

    return { fixture, mockService, mockJobUpdate, mockSnackbar };
  }

  it('should set the page title', async () => {
    await setup();
    const titleService = TestBed.inject(PageTitleService);
    expect(titleService.setTitle).toHaveBeenCalledWith('Joke Generator');
  });

  it('should subscribe to job updates for the course', async () => {
    const { mockJobUpdate } = await setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);
  });

  it('should load and display joke requests', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Tell me jokes about recursion');
    expect(el.textContent).toContain(
      'Why do recursive functions never finish? Because they keep calling themselves!',
    );
  });

  it('should show empty state when no requests exist', async () => {
    const { fixture } = await setup({ requests: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No joke requests yet');
  });

  it('should show error when list fails to load', async () => {
    const { fixture } = await setup({ listError: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load joke requests');
  });

  it('should submit a joke request and prepend it to the list', async () => {
    const { fixture, mockService, mockSnackbar } = await setup({ requests: [fakeRequest] });
    const component = fixture.componentInstance;

    component['form'].setValue({ prompt: 'Tell me puns' });
    fixture.detectChanges();

    const formEl = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    formEl.dispatchEvent(new Event('submit'));
    await flush();
    fixture.detectChanges();

    expect(mockService.create).toHaveBeenCalledWith(1, 'Tell me puns');
    expect(mockSnackbar.open).toHaveBeenCalledWith('Joke request submitted!');

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Jokes about algorithms');
  });

  it('should delete a joke request and remove it from the list', async () => {
    const { fixture, mockService, mockSnackbar } = await setup({ requests: [fakeRequest] });

    const deleteBtn = fixture.nativeElement.querySelector(
      'button[aria-label="Delete joke request"]',
    ) as HTMLButtonElement;
    deleteBtn.click();
    await flush();
    fixture.detectChanges();

    expect(mockService.delete).toHaveBeenCalledWith(1, 1);
    expect(mockSnackbar.open).toHaveBeenCalledWith('Joke request deleted.');

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).not.toContain('Tell me jokes about recursion');
  });

  it('should show pending indicator for in-progress requests', async () => {
    const { fixture } = await setup({ requests: [fakePendingRequest] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Generating jokes');
  });

  it('should watch pending jobs and refresh when completed', async () => {
    const { fixture, mockService, mockJobUpdate } = await setup({
      requests: [fakeRequest, fakePendingRequest],
    });

    expect(mockJobUpdate.updateForJob).toHaveBeenCalledWith(2);

    // Simulate intermediate status that should be ignored
    jobUpdateSignal.set({
      job_id: 2,
      course_id: 1,
      user_id: 1,
      kind: 'joke_generation',
      status: 'processing',
    });
    await flush();
    fixture.detectChanges();
    expect(mockService.get).not.toHaveBeenCalled();

    // Simulate job completion via WebSocket
    jobUpdateSignal.set({
      job_id: 2,
      course_id: 1,
      user_id: 1,
      kind: 'joke_generation',
      status: 'completed',
    });

    await flush();
    fixture.detectChanges();

    expect(mockService.get).toHaveBeenCalledWith(1, 2);
  });

  it('should not submit when form is invalid', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    // Form starts empty, which is invalid
    component['form'].setValue({ prompt: '' });
    await component['onSubmit']();

    expect(mockService.create).not.toHaveBeenCalled();
  });

  it('should show error when submission fails', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    mockService.create.mockRejectedValueOnce(new Error('fail'));
    component['form'].setValue({ prompt: 'Tell me jokes' });
    await component['onSubmit']();
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to submit joke request');
  });

  it('should show error when delete fails', async () => {
    const { fixture, mockService } = await setup({ requests: [fakeRequest] });
    const component = fixture.componentInstance;

    mockService.delete.mockRejectedValueOnce(new Error('fail'));
    await component['onDelete'](1);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to delete joke request');
  });

  it('should show spinner while submitting', async () => {
    let resolveCreate!: (value: JokeRequest) => void;
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    mockService.create.mockReturnValueOnce(
      new Promise<JokeRequest>((res) => {
        resolveCreate = res;
      }),
    );

    component['form'].setValue({ prompt: 'Tell me jokes' });
    const submitPromise = component['onSubmit']();
    fixture.detectChanges();

    expect(component['submitting']()).toBe(true);

    resolveCreate(fakePendingRequest);
    await submitPromise;
    fixture.detectChanges();

    expect(component['submitting']()).toBe(false);
  });

  it('should unsubscribe from job updates on destroy', async () => {
    const { fixture, mockJobUpdate } = await setup({ requests: [fakePendingRequest] });
    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
  });

  it('should return fallback labels for unknown status', async () => {
    const { fixture } = await setup();
    const component = fixture.componentInstance;
    expect(component['statusLabel']('unknown')).toBe('unknown');
    expect(component['statusIcon']('unknown')).toBe('help');
  });

  it('should silently handle refreshJob errors', async () => {
    const { fixture, mockService } = await setup({
      requests: [fakePendingRequest],
    });

    mockService.get.mockRejectedValueOnce(new Error('fail'));

    jobUpdateSignal.set({
      job_id: 2,
      course_id: 1,
      user_id: 1,
      kind: 'joke_generation',
      status: 'completed',
    });

    await flush();
    fixture.detectChanges();

    expect(mockService.get).toHaveBeenCalledWith(1, 2);
    // The list should still contain the old request
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Jokes about algorithms');
  });
});
