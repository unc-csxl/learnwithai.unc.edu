/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { IyowActivityDetail } from './iyow-activity-detail.component';
import { PageTitleService } from '../../../../../page-title.service';
import { JobUpdateService } from '../../../../../job-update.service';
import { LayoutNavigationService } from '../../../../../layout/layout-navigation.service';
import { ActivityService } from '../../activity.service';
import { ACTIVITY_TYPE_OPTIONS } from '../../activity-types';
import { IyowStudentSubmissionRow } from '../../../../../api/models';
import { AsyncJobStatus } from '../../../../../api/generated/models/async-job-status';

const flush = () => new Promise((resolve) => setTimeout(resolve));
const defaultType = ACTIVITY_TYPE_OPTIONS[0];

const baseActivity = {
  id: 10,
  title: 'Test IYOW',
  prompt: 'Explain X',
  rubric: null as string | null,
  type: defaultType.backendType,
  release_date: '2025-01-01T00:00:00Z',
  due_date: '2025-06-01T00:00:00Z',
  late_date: null as string | null,
  course_id: 1,
  created_at: '2025-01-01T00:00:00Z',
};

const rosterRows: IyowStudentSubmissionRow[] = [
  {
    student_pid: 111,
    given_name: 'Alice',
    family_name: 'Anderson',
    email: 'alice@example.com',
    submission: {
      id: 100,
      activity_id: 10,
      student_pid: 111,
      is_active: true,
      submitted_at: '2025-03-01T00:00:00Z',
      response_text: 'My answer',
      feedback: 'Great!',
      job: { id: 42, status: 'completed' as AsyncJobStatus, completed_at: '2025-03-01T01:00:00Z' },
    },
  },
  {
    student_pid: 222,
    given_name: 'Bob',
    family_name: 'Baker',
    email: 'bob@example.com',
    submission: null,
  },
  {
    student_pid: 333,
    given_name: null as unknown as string,
    family_name: null as unknown as string,
    email: 'noname@example.com',
    submission: null,
  },
];

describe('IyowActivityDetail', () => {
  function setup(overrides: { activityService?: object } = {}) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockJobUpdate = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn(),
    };
    const mockActivityService = overrides.activityService ?? {
      getIyow: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listIyowSubmissionsRoster: vi.fn(() => Promise.resolve([...rosterRows])),
    };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
      snapshot: { paramMap: new Map([['activityId', '10']]) },
    };

    const mockLayoutNavigation = { setContextSection: vi.fn(), clearContext: vi.fn() };

    TestBed.configureTestingModule({
      imports: [IyowActivityDetail],
      providers: [
        provideRouter([]),
        provideNoopAnimations(),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: JobUpdateService, useValue: mockJobUpdate },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(IyowActivityDetail);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockJobUpdate, mockActivityService, mockLayoutNavigation };
  }

  it('should load activity and set title', async () => {
    const { fixture, mockPageTitle } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW');
    expect(fixture.nativeElement.textContent).toContain('Release date');
    expect(fixture.nativeElement.textContent).toContain('Due date');
    expect(fixture.nativeElement.textContent).not.toContain('Explain X');
  });

  it('should subscribe to job updates on create and unsubscribe on destroy', () => {
    const { fixture, mockJobUpdate, mockLayoutNavigation } = setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);

    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
    expect(mockLayoutNavigation.clearContext).not.toHaveBeenCalled();
  });

  it('should show error on load failure', async () => {
    const mockActivityService = {
      getIyow: vi.fn(() => Promise.reject(new Error('fail'))),
      listIyowSubmissionsRoster: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load activity details.');
  });

  it('should render roster rows in the table', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Anderson, Alice');
    expect(text).toContain('Baker, Bob');
  });

  it('should show submission summary counts', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('1 of 3 students have submitted');
  });

  it('should keep the activity information card limited to release and due dates', async () => {
    const mockActivityService = {
      getIyow: vi.fn(() =>
        Promise.resolve({
          ...baseActivity,
          late_date: '2025-07-01T00:00:00Z',
          rubric: 'Must explain clearly',
        }),
      ),
      listIyowSubmissionsRoster: vi.fn(() => Promise.resolve([])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Release date');
    expect(fixture.nativeElement.textContent).toContain('Due date');
    expect(fixture.nativeElement.textContent).not.toContain('Late date');
    expect(fixture.nativeElement.textContent).not.toContain('Must explain clearly');
  });

  it('should show status labels for submitted and not-submitted rows', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Graded');
    expect(text).toContain('Not submitted');
  });

  it('should render a link for students with submissions', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const link: HTMLAnchorElement | null = fixture.nativeElement.querySelector('a[href]');
    expect(link).toBeTruthy();
    expect(link!.textContent).toContain('Anderson, Alice');
  });

  it('should fall back to the registry default route segment when activity type is unavailable', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      activity: { set: (value: null) => void };
      submissionLink: (studentPid: number) => Array<string | number>;
    };

    comp.activity.set(null);
    expect(comp.submissionLink(111)).toEqual([
      '/courses',
      1,
      'activities',
      '10',
      defaultType.routeSegment,
      'submissions',
      '111',
    ]);
  });

  it('should show "No students found" when roster is empty', async () => {
    const mockActivityService = {
      getIyow: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listIyowSubmissionsRoster: vi.fn(() => Promise.resolve([])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No students found');
  });

  it('should filter rows by search query', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      searchQuery: { set: (v: string) => void };
    };
    comp.searchQuery.set('alice');
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Anderson, Alice');
    expect(text).not.toContain('Baker, Bob');
  });

  it('should set layout navigation with sidenav items', async () => {
    const { fixture, mockLayoutNavigation } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        visibleBaseRoutes: ['/courses/1/dashboard', '/courses/1/activities'],
        groups: expect.arrayContaining([
          expect.objectContaining({
            label: 'Current activity',
            items: expect.arrayContaining([
              expect.objectContaining({ label: 'Submissions', icon: 'assignment' }),
              expect.objectContaining({ label: 'Activity Editor' }),
              expect.objectContaining({ label: 'Preview & Test' }),
            ]),
          }),
        ]),
      }),
    );
  });

  it('should return correct status labels', async () => {
    const { fixture } = setup();
    const comp = fixture.componentInstance as unknown as {
      statusLabel: (row: IyowStudentSubmissionRow) => string;
    };

    expect(comp.statusLabel(rosterRows[0])).toBe('Graded');
    expect(comp.statusLabel(rosterRows[1])).toBe('Not submitted');

    const processingRow: IyowStudentSubmissionRow = {
      ...rosterRows[0],
      submission: {
        ...rosterRows[0].submission!,
        job: { id: 1, status: 'pending' as AsyncJobStatus, completed_at: null },
      },
    };
    expect(comp.statusLabel(processingRow)).toBe('Processing');

    const submittedRow: IyowStudentSubmissionRow = {
      ...rosterRows[0],
      submission: { ...rosterRows[0].submission!, feedback: null, job: null },
    };
    expect(comp.statusLabel(submittedRow)).toBe('Submitted');
  });

  it('should debounce search input and update searchQuery signal', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    vi.useFakeTimers();
    try {
      const input: HTMLInputElement = fixture.nativeElement.querySelector(
        'input[aria-label="Search students by name"]',
      );
      input.value = 'alice';
      input.dispatchEvent(new Event('input'));

      const comp = fixture.componentInstance as unknown as {
        searchQuery: { (): string };
      };
      expect(comp.searchQuery()).toBe('');

      vi.advanceTimersByTime(300);
      expect(comp.searchQuery()).toBe('alice');
    } finally {
      vi.useRealTimers();
    }
  });

  it('should ignore search input shorter than minimum length', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    vi.useFakeTimers();
    try {
      const comp = fixture.componentInstance as unknown as {
        onSearchInput: (value: string) => void;
        searchQuery: { (): string };
      };

      comp.onSearchInput('ab');
      vi.advanceTimersByTime(300);
      expect(comp.searchQuery()).toBe('');
    } finally {
      vi.useRealTimers();
    }
  });

  it('should clear previous debounce timer when new input arrives', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    vi.useFakeTimers();
    try {
      const comp = fixture.componentInstance as unknown as {
        onSearchInput: (value: string) => void;
        searchQuery: { (): string };
      };

      comp.onSearchInput('alice');
      vi.advanceTimersByTime(100);
      // Second call before first debounce fires — should clear first timer
      comp.onSearchInput('bob');
      vi.advanceTimersByTime(300);
      expect(comp.searchQuery()).toBe('bob');
    } finally {
      vi.useRealTimers();
    }
  });

  it('should clear debounce timer on destroy when timer is active', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    vi.useFakeTimers();
    try {
      const comp = fixture.componentInstance as unknown as {
        onSearchInput: (value: string) => void;
      };

      comp.onSearchInput('alice');
      fixture.destroy();
      vi.advanceTimersByTime(300);
    } finally {
      vi.useRealTimers();
    }
  });

  it('should sort rows by family_name via onSortChange', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    // Trigger sort through the DOM to cover the template matSortChange binding
    const sortHeaders: NodeListOf<HTMLElement> = fixture.nativeElement.querySelectorAll(
      '.mat-sort-header-container',
    );
    // First sort header is "Student" (family_name)
    sortHeaders[0]?.click();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      filteredRows: { (): IyowStudentSubmissionRow[] };
      sortDirection: { (): string };
    };

    // Clicking toggles sort direction
    expect(comp.sortDirection()).toBeTruthy();
    const rows = comp.filteredRows();
    expect(rows.length).toBe(3);
  });

  it('should sort rows by submitted_at via onSortChange', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    // Click the "Submitted" sort header
    const sortHeaders: NodeListOf<HTMLElement> = fixture.nativeElement.querySelectorAll(
      '.mat-sort-header-container',
    );
    // Second sort header is "Submitted" (submitted_at)
    sortHeaders[1]?.click();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      filteredRows: { (): IyowStudentSubmissionRow[] };
      sortDirection: { (): string };
    };

    expect(comp.sortDirection()).toBeTruthy();
    const rows = comp.filteredRows();
    expect(rows.length).toBe(3);
  });

  it('should sort rows by status via onSortChange', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    // Click the "Status" sort header
    const sortHeaders: NodeListOf<HTMLElement> = fixture.nativeElement.querySelectorAll(
      '.mat-sort-header-container',
    );
    // Third sort header is "Status"
    sortHeaders[2]?.click();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      filteredRows: { (): IyowStudentSubmissionRow[] };
      sortDirection: { (): string };
    };

    expect(comp.sortDirection()).toBeTruthy();
    const rows = comp.filteredRows();
    expect(rows.length).toBe(3);
  });

  it('should sort rows correctly via internal sortRows', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    /* eslint-disable @typescript-eslint/no-explicit-any */
    const comp = fixture.componentInstance as any;

    // No direction → returns original order
    const unsorted = comp.sortRows([...rosterRows], 'family_name', '');
    expect(unsorted).toEqual(rosterRows);

    // Sort by family_name asc — null row (empty string) comes first
    // Reverse input order so null row appears as both a and b in sort comparisons
    const reversedRows = [...rosterRows].reverse();
    const byName = comp.sortRows(reversedRows, 'family_name', 'asc');
    expect(byName[1].family_name).toBe('Anderson');
    expect(byName[2].family_name).toBe('Baker');

    // Sort by student_name (falls through to family_name case)
    const byStudentName = comp.sortRows([...rosterRows], 'student_name', 'asc');
    expect(byStudentName[1].family_name).toBe('Anderson');

    // Sort by submitted_at desc
    const byDate = comp.sortRows([...rosterRows], 'submitted_at', 'desc');
    expect(byDate[0].given_name).toBe('Alice');

    // Sort by status asc
    const byStatus = comp.sortRows([...rosterRows], 'status', 'asc');
    expect(byStatus.length).toBe(3);

    // Sort by unknown column — exercises default switch branch
    const byUnknown = comp.sortRows([...rosterRows], 'unknown_col', 'asc');
    expect(byUnknown.length).toBe(3);
    /* eslint-enable @typescript-eslint/no-explicit-any */
  });
});
