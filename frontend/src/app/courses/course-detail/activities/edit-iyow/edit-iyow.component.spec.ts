import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute, Router } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { EditIyow } from './edit-iyow.component';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

const baseActivity = {
  id: 10,
  title: 'Test IYOW',
  prompt: 'Explain X',
  rubric: 'Must be clear',
  type: 'iyow',
  release_date: '2025-01-01T00:00:00Z',
  due_date: '2025-06-01T00:00:00Z',
  late_date: null as string | null,
  course_id: 1,
  created_at: '2025-01-01T00:00:00Z',
};

describe('EditIyow', () => {
  function setup(overrides: { activityService?: object } = {}) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockSnackbar = { open: vi.fn() };
    const mockActivityService = overrides.activityService ?? {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      updateIyow: vi.fn(() => Promise.resolve({ ...baseActivity })),
    };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
      snapshot: { paramMap: new Map([['activityId', '10']]) },
    };
    const mockLayoutNavigation = { setSection: vi.fn(), clear: vi.fn() };

    TestBed.configureTestingModule({
      imports: [EditIyow],
      providers: [
        provideRouter([]),
        provideNoopAnimations(),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: SuccessSnackbarService, useValue: mockSnackbar },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(EditIyow);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockSnackbar, mockActivityService, mockLayoutNavigation };
  }

  it('should load activity, populate form, and set title', async () => {
    const { fixture, mockPageTitle } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Edit: Test IYOW');

    const comp = fixture.componentInstance as unknown as {
      form: { getRawValue: () => Record<string, string> };
    };
    const values = comp.form.getRawValue();
    expect(values['title']).toBe('Test IYOW');
    expect(values['prompt']).toBe('Explain X');
    expect(values['rubric']).toBe('Must be clear');
  });

  it('should show error on load failure', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load activity.');
  });

  it('should submit the form and navigate on success', async () => {
    const { fixture, mockActivityService, mockSnackbar } = setup();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    await flush();
    fixture.detectChanges();

    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    await flush();
    fixture.detectChanges();

    expect(
      (mockActivityService as { updateIyow: ReturnType<typeof vi.fn> }).updateIyow,
    ).toHaveBeenCalledOnce();
    expect(mockSnackbar.open).toHaveBeenCalledWith('Activity updated!');
    expect(router.navigate).toHaveBeenCalledWith(['courses', 1, 'activities', 10]);
  });

  it('should show error on submit failure', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      updateIyow: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as { onSubmit: () => Promise<void> };
    await comp.onSubmit();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to update activity.');
  });

  it('should not submit if form is invalid', async () => {
    const { fixture, mockActivityService } = setup();
    await flush();
    fixture.detectChanges();

    // Clear a required field
    const comp = fixture.componentInstance as unknown as {
      form: { patchValue: (v: object) => void };
      onSubmit: () => Promise<void>;
    };
    comp.form.patchValue({ title: '' });
    await comp.onSubmit();
    await flush();

    expect(
      (mockActivityService as { updateIyow: ReturnType<typeof vi.fn> }).updateIyow,
    ).not.toHaveBeenCalled();
  });

  it('should show spinner while submitting', async () => {
    let resolveUpdate!: (v: unknown) => void;
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      updateIyow: vi.fn(
        () =>
          new Promise((resolve) => {
            resolveUpdate = resolve;
          }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      onSubmit: () => Promise<void>;
      submitting: () => boolean;
    };
    const submitPromise = comp.onSubmit();
    fixture.detectChanges();

    expect(comp.submitting()).toBe(true);
    expect(fixture.nativeElement.querySelector('mat-spinner')).toBeTruthy();

    resolveUpdate({ ...baseActivity });
    await submitPromise;
    fixture.detectChanges();

    expect(comp.submitting()).toBe(false);
  });

  it('should set layout navigation with back link', async () => {
    const { fixture, mockLayoutNavigation } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockLayoutNavigation.setSection).toHaveBeenCalledWith(
      expect.objectContaining({
        label: 'Edit: Test IYOW',
        items: expect.arrayContaining([
          expect.objectContaining({ label: 'Back to Activity' }),
        ]),
      }),
    );
  });

  it('should handle late_date in form population', async () => {
    const mockActivityService = {
      get: vi.fn(() =>
        Promise.resolve({ ...baseActivity, late_date: '2025-07-01T12:30:00Z' }),
      ),
      updateIyow: vi.fn(() => Promise.resolve({ ...baseActivity })),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      form: { getRawValue: () => Record<string, string> };
    };
    const values = comp.form.getRawValue();
    expect(values['late_date']).toBeTruthy();
    expect(values['late_date']).toContain('2025-07-01');
  });
});
