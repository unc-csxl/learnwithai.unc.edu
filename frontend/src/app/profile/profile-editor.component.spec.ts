/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ProfileEditor } from './profile-editor.component';
import { AuthService } from '../auth.service';
import { PageTitleService } from '../page-title.service';
import { SuccessSnackbarService } from '../success-snackbar.service';
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

    const mockRouter = { navigate: vi.fn(() => Promise.resolve(true)) };
    const mockSuccessSnackbar = { open: vi.fn() };

    TestBed.configureTestingModule({
      imports: [ProfileEditor, NoopAnimationsModule],
      providers: [
        { provide: AuthService, useValue: mockAuth },
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: Router, useValue: mockRouter },
        { provide: SuccessSnackbarService, useValue: mockSuccessSnackbar },
      ],
    });

    const fixture = TestBed.createComponent(ProfileEditor);
    fixture.detectChanges();
    return { fixture, mockAuth, mockPageTitle, mockRouter, mockSuccessSnackbar };
  }

  it('should create', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should set the page title to Profile', () => {
    const { mockPageTitle } = setup();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Profile');
  });

  it('should display account info (PID, onyen, email, name) as text', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('999999999');
    expect(el.textContent).toContain('testuser');
    expect(el.textContent).toContain('test@example.com');
    expect(el.textContent).toContain('Test User');
  });

  it('should not render readonly form inputs for non-editable fields', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelectorAll('input[readonly]').length).toBe(0);
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

  it('should not submit when form is invalid', () => {
    const { fixture, mockAuth } = setup();
    const component = fixture.componentInstance;
    component['form'].patchValue({ given_name: '' });
    component['onSubmit']();
    expect(mockAuth.updateProfile).not.toHaveBeenCalled();
  });

  it('should submit form, show snackbar, and navigate to /courses', async () => {
    const { fixture, mockAuth, mockRouter, mockSuccessSnackbar } = setup();
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
    expect(mockSuccessSnackbar.open).toHaveBeenCalledWith('Profile updated.');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses']);
  });

  it('should show error message when save fails', async () => {
    const { fixture, mockAuth } = setup();
    mockAuth.updateProfile.mockRejectedValueOnce(new Error('fail'));

    const component = fixture.componentInstance;
    component['form'].setValue({ given_name: 'Updated', family_name: 'Name' });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    await flush();
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Failed to save profile');
  });

  it('should show saving state during submission', async () => {
    let resolveUpdate!: (value: User) => void;
    const { fixture, mockAuth, mockRouter, mockSuccessSnackbar } = setup();
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
    await flush();

    expect(mockSuccessSnackbar.open).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalled();
  });

  it('should render with null user without crashing', () => {
    const { fixture } = setup(null);
    const el: HTMLElement = fixture.nativeElement;
    // No crash; account info rows just show empty values
    expect(el.querySelector('input[formControlName="given_name"]')).toBeTruthy();
  });
});
