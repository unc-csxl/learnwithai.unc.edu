/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { By } from '@angular/platform-browser';
import { signal, WritableSignal } from '@angular/core';
import { Roster } from './roster.component';
import { AuthService } from '../../../auth.service';
import { CourseService } from '../../course.service';
import {
  Course,
  PaginatedRoster,
  RosterMember,
  RosterUploadStatus,
  User,
} from '../../../api/models';
import { PageTitleService } from '../../../page-title.service';
import { JobUpdateService, JobUpdate } from '../../../job-update.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';
import { RosterUploadResultDialog } from './roster-upload-result-dialog.component';
import { SuccessSnackbarService } from '../../../success-snackbar.service';

const fakeMembers: RosterMember[] = [
  {
    user_pid: 111,
    course_id: 1,
    type: 'instructor',
    state: 'enrolled',
    given_name: 'Alice',
    family_name: 'Alpha',
    email: 'alice@unc.edu',
  },
  {
    user_pid: 222,
    course_id: 1,
    type: 'student',
    state: 'enrolled',
    given_name: 'Bob',
    family_name: 'Bravo',
    email: 'bob@unc.edu',
  },
];

const fakeResponse: PaginatedRoster = {
  items: fakeMembers,
  total: 2,
  page: 1,
  page_size: 25,
};

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('Roster', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  let jobUpdateSignal: WritableSignal<JobUpdate | null>;

  async function setup(
    options: {
      response?: PaginatedRoster;
      currentUser?: User | null;
      error?: { status: number };
      viewerCourseMissing?: boolean;
      currentUserPid?: number;
      viewerRoleError?: boolean;
      viewerRole?: Course['membership']['type'];
    } = {},
  ) {
    jobUpdateSignal = signal<JobUpdate | null>(null);
    const currentUserPid = options.currentUserPid ?? 100;
    const viewerRole = options.viewerRole ?? 'instructor';

    const mockCourses: Course[] = [
      {
        id: options.viewerCourseMissing ? 2 : 1,
        course_number: 'COMP101',
        name: 'Intro to CS',
        description: '',
        term: 'fall',
        year: 2026,
        membership: { type: viewerRole, state: 'enrolled' },
      },
    ];

    const mockService = {
      getMyCourses: options.viewerRoleError
        ? vi.fn(() => Promise.reject(new Error('viewer role failed')))
        : vi.fn(() => Promise.resolve(mockCourses)),
      getRoster: options.error
        ? vi.fn(() => Promise.reject(options.error))
        : vi.fn(() => Promise.resolve(options.response ?? fakeResponse)),
      updateMemberRole: vi.fn(
        (courseId: number, pid: number, body: { type: RosterMember['type'] }) =>
          Promise.resolve({
            course_id: courseId,
            user_pid: pid,
            type: body.type,
            state: 'enrolled',
          }),
      ),
      uploadRoster: vi.fn(() => Promise.resolve({ id: 42, status: 'pending' })),
      getRosterUploadStatus: vi.fn(),
    };

    const mockJobUpdateService = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn(() => jobUpdateSignal.asReadonly()),
    };
    const mockLayoutNavigation = { clearContext: vi.fn() };
    const mockSuccessSnackbar = { open: vi.fn() };
    const currentUser =
      'currentUser' in options
        ? options.currentUser
        : {
            pid: currentUserPid,
            onyen: 'testuser',
            name: 'Test User',
            given_name: 'Test',
            family_name: 'User',
            email: 'test@unc.edu',
          };
    const mockAuthService = {
      user: signal<User | null>(currentUser ?? null).asReadonly(),
    };

    const mockRoute = {
      parent: { snapshot: { paramMap: new Map([['id', '1']]) } },
    };

    TestBed.configureTestingModule({
      imports: [Roster, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: CourseService, useValue: mockService },
        { provide: JobUpdateService, useValue: mockJobUpdateService },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: AuthService, useValue: mockAuthService },
        { provide: SuccessSnackbarService, useValue: mockSuccessSnackbar },
        {
          provide: PageTitleService,
          useValue: {
            title: vi.fn(),
            setTitle: vi.fn(),
          },
        },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(Roster);
    const component = fixture.componentInstance;
    const snackBarOpen = vi.spyOn(component['snackBar'], 'open');
    const snackBarDismiss = vi.spyOn(component['snackBar'], 'dismiss');
    const dialogOpen = vi.spyOn(component['dialog'], 'open').mockReturnValue({
      afterClosed: () => ({ subscribe: vi.fn() }),
    } as never);

    fixture.detectChanges();
    await flush();
    fixture.detectChanges();
    return {
      fixture,
      mockService,
      mockJobUpdateService,
      mockLayoutNavigation,
      mockSuccessSnackbar,
      snackBarOpen,
      snackBarDismiss,
      dialogOpen,
    };
  }

  it('should display roster members with name columns', async () => {
    const { fixture, mockLayoutNavigation } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tr[mat-row]');
    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('Alice');
    expect(rows[0].textContent).toContain('Alpha');
    expect(rows[0].textContent).toContain('111');
    expect(rows[0].textContent).toContain('alice@unc.edu');
  });

  it('should show add member link', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const link = el.querySelector('a');
    expect(link?.textContent).toContain('Add Member');
  });

  it('should show search input', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const input = el.querySelector('input[matInput]');
    expect(input).toBeTruthy();
  });

  it('should show role column header', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Role');
  });

  it('should show paginator', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const paginator = el.querySelector('mat-paginator');
    expect(paginator).toBeTruthy();
  });

  it('should gray out non-enrolled members', async () => {
    const droppedMember: RosterMember = {
      user_pid: 333,
      course_id: 1,
      type: 'student',
      state: 'dropped',
      given_name: 'Charlie',
      family_name: 'Charlie',
      email: 'charlie@unc.edu',
    };
    const response: PaginatedRoster = {
      items: [droppedMember],
      total: 1,
      page: 1,
      page_size: 25,
    };
    const { fixture } = await setup({ response });
    const el: HTMLElement = fixture.nativeElement;
    const row = el.querySelector('tr[mat-row]');
    expect(row?.classList.contains('inactive-row')).toBe(true);
  });

  it('should render editable role selects for instructor viewers', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(2);
    expect(el.querySelectorAll('.role-readonly').length).toBe(0);
  });

  it('should render self row role as read-only', async () => {
    const { fixture } = await setup({ currentUserPid: 111 });
    const el: HTMLElement = fixture.nativeElement;
    const readonlyRole = el.querySelector('.role-readonly');
    expect(readonlyRole?.textContent).toContain('Instructor');
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(1);
  });

  it('should render all role cells as read-only for non-instructor viewers', async () => {
    const { fixture } = await setup({ viewerRole: 'ta' });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(0);
    expect(el.querySelectorAll('.role-readonly').length).toBe(2);
  });

  it('should render dropped members as read-only even for instructors', async () => {
    const response: PaginatedRoster = {
      items: [
        {
          user_pid: 333,
          course_id: 1,
          type: 'student',
          state: 'dropped',
          given_name: 'Charlie',
          family_name: 'Charlie',
          email: 'charlie@unc.edu',
        },
      ],
      total: 1,
      page: 1,
      page_size: 25,
    };
    const { fixture } = await setup({ response });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(0);
    expect(el.querySelector('.role-readonly')?.textContent).toContain('Student');
  });

  it('should fall back to read-only roles when viewer role lookup fails', async () => {
    const { fixture } = await setup({ viewerRoleError: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(0);
    expect(el.querySelectorAll('.role-readonly').length).toBe(2);
  });

  it('should fall back to read-only roles when the course membership is missing', async () => {
    const { fixture } = await setup({ viewerCourseMissing: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(0);
    expect(el.querySelectorAll('.role-readonly').length).toBe(2);
  });

  it('should fall back to read-only roles when the current user profile is unavailable', async () => {
    const { fixture } = await setup({ currentUser: null });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('.role-select-field mat-select').length).toBe(0);
    expect(el.querySelectorAll('.role-readonly').length).toBe(2);
  });

  it('should show 403 error message', async () => {
    const { fixture } = await setup({ error: { status: 403 } });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('do not have permission');
  });

  it('should show generic error message', async () => {
    const { fixture } = await setup({ error: { status: 500 } });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load roster');
  });

  it('should show empty message when roster is empty', async () => {
    const response: PaginatedRoster = { items: [], total: 0, page: 1, page_size: 25 };
    const { fixture } = await setup({ response });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No members found');
  });

  it('should call getRoster with pagination on page event', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;
    mockService.getRoster.mockResolvedValue({ items: [], total: 0, page: 2, page_size: 10 });
    component['onPage']({ pageIndex: 1, pageSize: 10, length: 2 });
    await flush();
    fixture.detectChanges();
    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 2,
      pageSize: 10,
      query: undefined,
    });
  });

  it('should debounce search input and call getRoster with query', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;
    mockService.getRoster.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });

    vi.useFakeTimers();
    component['onSearchInput']('ali');
    vi.advanceTimersByTime(300);
    vi.useRealTimers();

    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 1,
      pageSize: 10,
      query: 'ali',
    });
  });

  it('should cancel previous debounce when typing again', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;
    mockService.getRoster.mockResolvedValue({
      items: fakeMembers,
      total: 2,
      page: 1,
      page_size: 10,
    });

    vi.useFakeTimers();
    component['onSearchInput']('ali');
    // Type again before first fires
    component['onSearchInput']('alice');
    vi.advanceTimersByTime(300);
    vi.useRealTimers();

    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 1,
      pageSize: 10,
      query: 'alice',
    });
  });

  it('should trigger search via DOM input event', async () => {
    const { fixture, mockService } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const input = el.querySelector('input[matInput]') as HTMLInputElement;
    mockService.getRoster.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 });

    vi.useFakeTimers();
    input.value = 'bob';
    input.dispatchEvent(new Event('input'));
    vi.advanceTimersByTime(300);
    vi.useRealTimers();

    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 1,
      pageSize: 10,
      query: 'bob',
    });
  });

  it('should trigger pagination via paginator', async () => {
    // Set up with many items so navigation is active
    const manyResponse: PaginatedRoster = {
      items: fakeMembers,
      total: 50,
      page: 1,
      page_size: 10,
    };
    const { fixture, mockService } = await setup({ response: manyResponse });
    const el: HTMLElement = fixture.nativeElement;
    mockService.getRoster.mockResolvedValue({
      items: fakeMembers,
      total: 50,
      page: 2,
      page_size: 10,
    });

    // Click "next page" button on the paginator
    const nextBtn = el.querySelector('button.mat-mdc-paginator-navigation-next') as HTMLElement;
    expect(nextBtn).toBeTruthy();
    nextBtn.click();
    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 2,
      pageSize: 10,
      query: undefined,
    });
  });

  it('should ignore search input shorter than 3 characters', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;
    const initialCallCount = mockService.getRoster.mock.calls.length;

    vi.useFakeTimers();
    component['onSearchInput']('ab');
    vi.advanceTimersByTime(300);
    vi.useRealTimers();

    await flush();

    // The query is '' which matches the initial searchQuery, so no new call
    expect(mockService.getRoster.mock.calls.length).toBe(initialCallCount);
  });

  it('should update a member role and show a success snackbar', async () => {
    const { fixture, mockService, mockSuccessSnackbar } = await setup();
    const component = fixture.componentInstance;

    mockService.updateMemberRole.mockResolvedValue({
      user_pid: 222,
      course_id: 1,
      type: 'ta',
      state: 'enrolled',
    });

    await component['onRoleChange'](component['roster']()[1], 'ta');
    fixture.detectChanges();

    expect(mockService.updateMemberRole).toHaveBeenCalledWith(1, 222, { type: 'ta' });
    expect(component['roster']()[1].type).toBe('ta');
    expect(mockSuccessSnackbar.open).toHaveBeenCalledWith('Updated Bob Bravo to TA.');
  });

  it('should trigger role updates from the mat-select selectionChange binding', async () => {
    const { fixture, mockService } = await setup();
    mockService.updateMemberRole.mockResolvedValue({
      user_pid: 222,
      course_id: 1,
      type: 'ta',
      state: 'enrolled',
    });

    const roleSelect = fixture.debugElement.queryAll(By.css('.role-select-field mat-select'))[1];
    roleSelect.triggerEventHandler('selectionChange', { value: 'ta' });
    await flush();
    fixture.detectChanges();

    expect(mockService.updateMemberRole).toHaveBeenCalledWith(1, 222, { type: 'ta' });
  });

  it('should revert the role and show an error snackbar when update fails', async () => {
    const { fixture, mockService, snackBarOpen } = await setup();
    const component = fixture.componentInstance;

    mockService.updateMemberRole.mockRejectedValue(new Error('fail'));

    await component['onRoleChange'](component['roster']()[1], 'ta');
    fixture.detectChanges();

    expect(component['roster']()[1].type).toBe('student');
    expect(snackBarOpen).toHaveBeenCalledWith('Failed to update member role.', 'Dismiss', {
      duration: 5000,
    });
  });

  it('should track row-level saving state while a role update is in flight', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    let resolveUpdate!: (value: {
      user_pid: number;
      course_id: number;
      type: RosterMember['type'];
      state: 'enrolled';
    }) => void;
    mockService.updateMemberRole.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveUpdate = resolve;
        }),
    );

    const updatePromise = component['onRoleChange'](component['roster']()[1], 'ta');
    fixture.detectChanges();

    expect(component['isSavingRole'](222)).toBe(true);
    expect(component['isSavingRole'](111)).toBe(false);

    resolveUpdate({ user_pid: 222, course_id: 1, type: 'ta', state: 'enrolled' });
    await updatePromise;

    expect(component['isSavingRole'](222)).toBe(false);
  });

  it('should ignore redundant role changes', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    await component['onRoleChange'](component['roster']()[1], 'student');

    expect(mockService.updateMemberRole).not.toHaveBeenCalled();
  });

  it('should clear debounce timer on destroy', async () => {
    const { fixture } = await setup();
    const component = fixture.componentInstance;
    // Start a pending debounce, then destroy — should not throw
    component['onSearchInput']('alice');
    fixture.destroy();
  });

  it('should show upload CSV button', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const buttons = Array.from(el.querySelectorAll('button'));
    const uploadBtn = buttons.find((b) => b.textContent?.includes('Upload CSV'));
    expect(uploadBtn).toBeTruthy();
  });

  it('should click hidden file input when upload button is clicked', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const fileInput = el.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(fileInput, 'click');
    const buttons = Array.from(el.querySelectorAll('button'));
    const uploadBtn = buttons.find((b) => b.textContent?.includes('Upload CSV'))!;
    uploadBtn.click();
    expect(clickSpy).toHaveBeenCalled();
  });

  it('should call onFileSelected when file input change event fires', async () => {
    const { fixture, mockService, snackBarOpen } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const fileInput = el.querySelector('input[type="file"]') as HTMLInputElement;

    // Simulate a file being added by spying, then dispatching the DOM change event
    const file = new File(['csv'], 'roster.csv', { type: 'text/csv' });
    Object.defineProperty(fileInput, 'files', { value: [file], writable: false });

    fileInput.dispatchEvent(new Event('change'));
    await flush();
    fixture.detectChanges();

    expect(mockService.uploadRoster).toHaveBeenCalledWith(1, file);
    expect(snackBarOpen).toHaveBeenCalledWith('Roster upload processing\u2026', undefined, {
      duration: 0,
    });
  });

  it('should upload file and show snackbar on file selection', async () => {
    const { fixture, mockService, snackBarOpen } = await setup();
    const component = fixture.componentInstance;

    const file = new File(['csv'], 'roster.csv', { type: 'text/csv' });
    const event = { target: { files: [file], value: 'C:\\roster.csv' } } as unknown as Event;

    await component['onFileSelected'](event);
    fixture.detectChanges();

    expect(mockService.uploadRoster).toHaveBeenCalledWith(1, file);
    expect(snackBarOpen).toHaveBeenCalledWith('Roster upload processing…', undefined, {
      duration: 0,
    });
  });

  it('should show error snackbar when upload fails', async () => {
    const { fixture, mockService, snackBarOpen } = await setup();
    const component = fixture.componentInstance;
    mockService.uploadRoster.mockRejectedValue(new Error('fail'));

    const file = new File(['csv'], 'roster.csv', { type: 'text/csv' });
    const event = { target: { files: [file], value: '' } } as unknown as Event;

    await component['onFileSelected'](event);
    fixture.detectChanges();

    expect(snackBarOpen).toHaveBeenCalledWith('Failed to upload roster CSV.', 'Dismiss', {
      duration: 5000,
    });
  });

  it('should show dialog when WebSocket signals job completed', async () => {
    const { fixture, mockService, snackBarDismiss, dialogOpen, mockJobUpdateService } =
      await setup();
    const component = fixture.componentInstance;

    const completedStatus: RosterUploadStatus = {
      id: 42,
      status: 'completed',
      created_count: 5,
      updated_count: 2,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    };
    mockService.getRosterUploadStatus.mockResolvedValue(completedStatus);

    // Trigger file upload to start watching
    const file = new File(['csv'], 'roster.csv', { type: 'text/csv' });
    const event = { target: { files: [file], value: '' } } as unknown as Event;
    await component['onFileSelected'](event);
    fixture.detectChanges();

    expect(mockJobUpdateService.updateForJob).toHaveBeenCalledWith(42);

    // Simulate WebSocket delivering a completed update
    jobUpdateSignal.set({
      job_id: 42,
      course_id: 1,
      user_id: 100,
      kind: 'roster_upload',
      status: 'completed',
    });
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();

    expect(mockService.getRosterUploadStatus).toHaveBeenCalledWith(1, 42);
    expect(snackBarDismiss).toHaveBeenCalled();
    expect(dialogOpen).toHaveBeenCalledWith(RosterUploadResultDialog, {
      data: completedStatus,
      width: '400px',
    });
  });

  it('should ignore processing status updates from WebSocket', async () => {
    const { fixture, mockService, snackBarDismiss } = await setup();
    const component = fixture.componentInstance;

    // Trigger file upload to start watching
    const file = new File(['csv'], 'roster.csv', { type: 'text/csv' });
    const event = { target: { files: [file], value: '' } } as unknown as Event;
    await component['onFileSelected'](event);
    fixture.detectChanges();

    // Simulate WebSocket delivering a processing update — should not trigger fetch
    jobUpdateSignal.set({
      job_id: 42,
      course_id: 1,
      user_id: 100,
      kind: 'roster_upload',
      status: 'processing',
    });
    fixture.detectChanges();
    await flush();

    expect(snackBarDismiss).not.toHaveBeenCalled();
    expect(mockService.getRosterUploadStatus).not.toHaveBeenCalled();
  });

  it('should show error snackbar when status fetch fails after WS notification', async () => {
    const { fixture, mockService, snackBarOpen } = await setup();
    const component = fixture.componentInstance;

    mockService.getRosterUploadStatus.mockRejectedValue(new Error('network'));

    // Trigger file upload
    const file = new File(['csv'], 'roster.csv', { type: 'text/csv' });
    const event = { target: { files: [file], value: '' } } as unknown as Event;
    await component['onFileSelected'](event);
    fixture.detectChanges();

    // Simulate completed WS update
    jobUpdateSignal.set({
      job_id: 42,
      course_id: 1,
      user_id: 100,
      kind: 'roster_upload',
      status: 'completed',
    });
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();

    expect(snackBarOpen).toHaveBeenCalledWith('Failed to check upload status.', 'Dismiss', {
      duration: 5000,
    });
  });

  it('should not call upload when no file is selected', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;
    const event = { target: { files: [] } } as unknown as Event;
    await component['onFileSelected'](event);
    expect(mockService.uploadRoster).not.toHaveBeenCalled();
  });

  it('should subscribe and unsubscribe to job updates', async () => {
    const { fixture, mockJobUpdateService } = await setup();

    expect(mockJobUpdateService.subscribe).toHaveBeenCalledWith(1);

    fixture.destroy();

    expect(mockJobUpdateService.unsubscribe).toHaveBeenCalledWith(1);
  });

  it('should clean up debounce timer on destroy', async () => {
    const { fixture } = await setup();
    const component = fixture.componentInstance;
    // Start a pending debounce, then destroy — should not throw
    component['onSearchInput']('alice');
    fixture.destroy();
  });
});
