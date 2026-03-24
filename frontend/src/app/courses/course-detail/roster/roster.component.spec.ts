import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Roster } from './roster.component';
import { CourseService } from '../../course.service';
import { PaginatedRoster, RosterMember, RosterUploadStatus } from '../../../api/models';
import { PageTitleService } from '../../../page-title.service';
import { RosterUploadResultDialog } from './roster-upload-result-dialog.component';

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

  async function setup(options: { response?: PaginatedRoster; error?: { status: number } } = {}) {
    const mockService = {
      getRoster: options.error
        ? vi.fn(() => Promise.reject(options.error))
        : vi.fn(() => Promise.resolve(options.response ?? fakeResponse)),
      uploadRoster: vi.fn(() => Promise.resolve({ id: 42, status: 'pending' })),
      getRosterUploadStatus: vi.fn(),
    };

    const mockRoute = {
      parent: { snapshot: { paramMap: new Map([['id', '1']]) } },
    };

    TestBed.configureTestingModule({
      imports: [Roster, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: CourseService, useValue: mockService },
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
    return { fixture, mockService, snackBarOpen, snackBarDismiss, dialogOpen };
  }

  it('should display roster members with name columns', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tr[mat-row]');
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
    mockService.getRoster.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 25 });

    vi.useFakeTimers();
    component['onSearchInput']('ali');
    vi.advanceTimersByTime(300);
    vi.useRealTimers();

    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 1,
      pageSize: 25,
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
      page_size: 25,
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
      pageSize: 25,
      query: 'alice',
    });
  });

  it('should trigger search via DOM input event', async () => {
    const { fixture, mockService } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const input = el.querySelector('input[matInput]') as HTMLInputElement;
    mockService.getRoster.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 25 });

    vi.useFakeTimers();
    input.value = 'bob';
    input.dispatchEvent(new Event('input'));
    vi.advanceTimersByTime(300);
    vi.useRealTimers();

    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 1,
      pageSize: 25,
      query: 'bob',
    });
  });

  it('should trigger pagination via paginator', async () => {
    // Set up with many items so navigation is active
    const manyResponse: PaginatedRoster = {
      items: fakeMembers,
      total: 50,
      page: 1,
      page_size: 25,
    };
    const { fixture, mockService } = await setup({ response: manyResponse });
    const el: HTMLElement = fixture.nativeElement;
    mockService.getRoster.mockResolvedValue({
      items: fakeMembers,
      total: 50,
      page: 2,
      page_size: 25,
    });

    // Click "next page" button on the paginator
    const nextBtn = el.querySelector('button.mat-mdc-paginator-navigation-next') as HTMLElement;
    expect(nextBtn).toBeTruthy();
    nextBtn.click();
    await flush();
    fixture.detectChanges();

    expect(mockService.getRoster).toHaveBeenCalledWith(1, {
      page: 2,
      pageSize: 25,
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
    mockService.getRosterUploadStatus.mockResolvedValue({
      id: 42,
      status: 'processing',
    });

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

  it('should poll and show dialog when upload completes', async () => {
    const { fixture, mockService, snackBarDismiss, dialogOpen } = await setup();
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

    vi.useFakeTimers();
    component['pollUploadStatus'](42);
    await vi.advanceTimersByTimeAsync(2000);
    vi.useRealTimers();
    fixture.detectChanges();

    expect(mockService.getRosterUploadStatus).toHaveBeenCalledWith(1, 42);
    expect(snackBarDismiss).toHaveBeenCalled();
    expect(dialogOpen).toHaveBeenCalledWith(RosterUploadResultDialog, {
      data: completedStatus,
      width: '400px',
    });
  });

  it('should continue polling when status is processing', async () => {
    const { fixture, mockService, snackBarDismiss } = await setup();
    const component = fixture.componentInstance;

    const processingStatus = { id: 42, status: 'processing' as const };
    const completedStatus: RosterUploadStatus = {
      id: 42,
      status: 'completed',
      created_count: 3,
      updated_count: 1,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    };
    mockService.getRosterUploadStatus
      .mockResolvedValueOnce(processingStatus)
      .mockResolvedValueOnce(completedStatus);

    // First poll returns processing, which schedules another poll
    vi.useFakeTimers();
    component['pollUploadStatus'](42);
    await vi.advanceTimersByTimeAsync(2000);

    expect(mockService.getRosterUploadStatus).toHaveBeenCalledTimes(1);
    expect(snackBarDismiss).not.toHaveBeenCalled();

    // Second poll returns completed
    await vi.advanceTimersByTimeAsync(2000);
    vi.useRealTimers();
    fixture.detectChanges();

    expect(mockService.getRosterUploadStatus).toHaveBeenCalledTimes(2);
    expect(snackBarDismiss).toHaveBeenCalled();
  });

  it('should show error snackbar when polling fails', async () => {
    const { fixture, mockService, snackBarOpen } = await setup();
    const component = fixture.componentInstance;

    mockService.getRosterUploadStatus.mockRejectedValue(new Error('network'));

    vi.useFakeTimers();
    component['pollUploadStatus'](42);
    await vi.advanceTimersByTimeAsync(2000);
    vi.useRealTimers();
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

  it('should clean up poll timer on destroy', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;
    mockService.getRosterUploadStatus.mockResolvedValue({ id: 42, status: 'processing' });

    vi.useFakeTimers();
    component['pollUploadStatus'](42);
    fixture.destroy();
    // Advance time — should not throw after destroy
    vi.advanceTimersByTime(5000);
    vi.useRealTimers();
  });
});
