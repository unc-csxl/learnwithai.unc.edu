/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute, Router } from '@angular/router';
import { CreateIyow } from './create-iyow.component';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CreateIyow', () => {
  function setup(overrides: { activityService?: object } = {}) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockSnackbar = { open: vi.fn() };
    const mockActivityService = overrides.activityService ?? {
      createIyow: vi.fn(() => Promise.resolve({ id: 10 })),
    };
    const mockLayoutNavigation = { setContextSection: vi.fn(), clearContext: vi.fn() };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
    };

    TestBed.configureTestingModule({
      imports: [CreateIyow],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: SuccessSnackbarService, useValue: mockSnackbar },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(CreateIyow);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockSnackbar, mockActivityService, mockLayoutNavigation };
  }

  it('should set the page title', () => {
    const { mockPageTitle, mockLayoutNavigation } = setup();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Create IYOW Activity');
    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        visibleBaseRoutes: ['/courses/1/dashboard', '/courses/1/activities'],
      }),
    );
  });

  it('should submit the form via template and navigate', async () => {
    const { fixture, mockActivityService, mockSnackbar } = setup();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      title: 'My Title',
      prompt: 'My Prompt',
      rubric: 'My Rubric',
      release_date: '2025-01-01',
      due_date: '2025-02-01',
    });
    fixture.detectChanges();

    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    await flush();
    fixture.detectChanges();

    expect(
      (mockActivityService as { createIyow: ReturnType<typeof vi.fn> }).createIyow,
    ).toHaveBeenCalledOnce();
    expect(mockSnackbar.open).toHaveBeenCalledWith('IYOW activity created!');
    expect(router.navigate).toHaveBeenCalled();
  });

  it('should show error on failure', async () => {
    const mockActivityService = {
      createIyow: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    const component = fixture.componentInstance;

    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      title: 'T',
      prompt: 'P',
      rubric: 'R',
      release_date: '2025-01-01',
      due_date: '2025-02-01',
    });

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to create activity.');
  });

  it('should not submit if form is invalid', async () => {
    const { fixture, mockActivityService } = setup();
    const component = fixture.componentInstance;

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    await flush();

    expect(
      (mockActivityService as { createIyow: ReturnType<typeof vi.fn> }).createIyow,
    ).not.toHaveBeenCalled();
  });

  it('should show spinner while submitting', async () => {
    let resolveCreate!: (v: unknown) => void;
    const mockActivityService = {
      createIyow: vi.fn(
        () =>
          new Promise((resolve) => {
            resolveCreate = resolve;
          }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      title: 'T',
      prompt: 'P',
      rubric: 'R',
      release_date: '2025-01-01',
      due_date: '2025-02-01',
    });

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    fixture.detectChanges();

    // While submitting, button should be disabled
    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    resolveCreate({ id: 10 });
    await flush();
    fixture.detectChanges();
  });
});
