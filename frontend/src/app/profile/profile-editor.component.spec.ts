import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ProfileEditor } from './profile-editor.component';
import { AuthService } from '../auth.service';
import { PageTitleService } from '../page-title.service';
import { User } from '../api/models';

const flush = () => new Promise((resolve) => setTimeout(resolve));

const fakeUser: User = {
  pid: 999999999,
  name: 'Test User',
  given_name: 'Test',
  family_name: 'User',
  email: 'test@example.com',
  onyen: 'testuser',
};

describe('ProfileEditor', () => {
  function setup(user: User | null = fakeUser) {
    const mockAuth = {
      user: signal(user).asReadonly(),
      updateProfile: vi.fn(() =>
        Promise.resolve({
          ...fakeUser,
          given_name: 'Updated',
          family_name: 'Name',
          name: 'Updated Name',
        }),
      ),
    };

    const mockPageTitle = {
      title: signal('Profile'),
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [ProfileEditor, NoopAnimationsModule],
      providers: [
        { provide: AuthService, useValue: mockAuth },
        { provide: PageTitleService, useValue: mockPageTitle },
      ],
    });

    const fixture = TestBed.createComponent(ProfileEditor);
    fixture.detectChanges();
    return { fixture, mockAuth, mockPageTitle };
  }

  it('should create', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should render with null user', () => {
    const { fixture } = setup(null);
    const el: HTMLElement = fixture.nativeElement;
    const readonlyInputs = el.querySelectorAll('input[readonly]');
    expect(readonlyInputs.length).toBe(4);
  });

  it('should set the page title to Profile', () => {
    const { mockPageTitle } = setup();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Profile');
  });

  it('should render readonly fields for PID, Onyen, Email, and Full Name', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const readonlyInputs = el.querySelectorAll('input[readonly]');
    expect(readonlyInputs.length).toBe(4);
  });

  it('should render editable fields for given name and family name', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('input[formControlName="given_name"]')).toBeTruthy();
    expect(el.querySelector('input[formControlName="family_name"]')).toBeTruthy();
  });

  it('should populate form with user data', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance;
    expect(component['form'].value).toEqual({
      given_name: 'Test',
      family_name: 'User',
    });
  });

  it('should disable submit when form is invalid', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance;
    component['form'].patchValue({ given_name: '', family_name: '' });
    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should submit the form and call updateProfile', async () => {
    const { fixture, mockAuth } = setup();
    const component = fixture.componentInstance;
    component['form'].setValue({ given_name: 'Updated', family_name: 'Name' });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    await flush();
    fixture.detectChanges();

    expect(mockAuth.updateProfile).toHaveBeenCalledWith({
      given_name: 'Updated',
      family_name: 'Name',
    });
  });

  it('should show saved message after successful submit', async () => {
    const { fixture } = setup();
    const component = fixture.componentInstance;
    component['form'].setValue({ given_name: 'Updated', family_name: 'Name' });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    await flush();
    fixture.detectChanges();

    const status = fixture.nativeElement.querySelector('[role="status"]');
    expect(status?.textContent).toContain('Profile updated');
  });

  it('should not submit when form is invalid', () => {
    const { fixture, mockAuth } = setup();
    const component = fixture.componentInstance;
    component['form'].patchValue({ given_name: '' });
    component['onSubmit']();
    expect(mockAuth.updateProfile).not.toHaveBeenCalled();
  });

  it('should show saving state during submission', async () => {
    let resolveUpdate!: (value: User) => void;
    const { fixture, mockAuth } = setup();
    mockAuth.updateProfile.mockReturnValue(
      new Promise<User>((r) => {
        resolveUpdate = r;
      }),
    );
    const component = fixture.componentInstance;
    component['form'].setValue({ given_name: 'Updated', family_name: 'Name' });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(button.textContent).toContain('Saving');
    expect(button.disabled).toBe(true);

    resolveUpdate({
      ...fakeUser,
      given_name: 'Updated',
      family_name: 'Name',
      name: 'Updated Name',
    });
    await new Promise((r) => setTimeout(r));
    fixture.detectChanges();

    expect(button.textContent).toContain('Save');
  });
});
