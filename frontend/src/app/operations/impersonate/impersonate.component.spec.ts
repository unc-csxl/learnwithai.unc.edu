/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ImpersonateComponent } from './impersonate.component';
import { OperationsService } from '../operations.service';
import { PageTitleService } from '../../page-title.service';
import { UserSearchResult } from '../../api/models';

const STUB_RESULTS: UserSearchResult[] = [
  { pid: 111, name: 'Alice Student', email: 'alice@unc.edu' },
  { pid: 222, name: 'Bob Teacher', email: 'bob@unc.edu' },
];

function setup() {
  const mockOps = {
    searchUsers: vi.fn().mockResolvedValue(STUB_RESULTS),
    impersonate: vi.fn().mockResolvedValue(undefined),
  };
  const mockSnackBar = { open: vi.fn() };
  const mockTitle = { setTitle: vi.fn() };

  TestBed.configureTestingModule({
    imports: [NoopAnimationsModule],
    providers: [
      { provide: OperationsService, useValue: mockOps },
      { provide: MatSnackBar, useValue: mockSnackBar },
      { provide: PageTitleService, useValue: mockTitle },
    ],
  });

  const fixture = TestBed.createComponent(ImpersonateComponent);
  fixture.detectChanges();

  return { fixture, component: fixture.componentInstance, mockOps, mockSnackBar, mockTitle };
}

describe('ImpersonateComponent', () => {
  it('should create and set page title', () => {
    const { component, mockTitle } = setup();
    expect(component).toBeTruthy();
    expect(mockTitle.setTitle).toHaveBeenCalledWith('Impersonate User');
  });

  it('should search users via performSearch', async () => {
    const { fixture, component, mockOps } = setup();
    await component['performSearch']('alice');
    expect(mockOps.searchUsers).toHaveBeenCalledWith('alice');
    fixture.destroy();
  });

  it('should display results table after search', async () => {
    const { fixture, component, mockOps } = setup();
    await component['performSearch']('alice');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('table')).toBeTruthy();
    expect(mockOps.searchUsers).toHaveBeenCalledWith('alice');
    fixture.destroy();
  });

  it('should show no results message when search returns empty', async () => {
    const { fixture, component, mockOps } = setup();
    mockOps.searchUsers.mockResolvedValue([]);
    await component['performSearch']('zzzz');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.no-results')?.textContent).toContain('No users found');
    fixture.destroy();
  });

  it('should impersonate on button click', async () => {
    const { fixture, component, mockOps } = setup();
    const user: UserSearchResult = { pid: 111, name: 'Alice', email: 'a@unc.edu' };
    await component['onImpersonate'](user);
    expect(mockOps.impersonate).toHaveBeenCalledWith(111);
    fixture.destroy();
  });

  it('should show error snackbar when impersonation fails', async () => {
    const { fixture, component, mockOps, mockSnackBar } = setup();
    mockOps.impersonate.mockRejectedValue(new Error('fail'));
    const user: UserSearchResult = { pid: 111, name: 'Alice', email: 'a@unc.edu' };
    await component['onImpersonate'](user);
    expect(mockSnackBar.open).toHaveBeenCalledWith('Failed to start impersonation', undefined, {
      duration: 5000,
    });
    fixture.destroy();
  });

  it('should show error snackbar when search fails', async () => {
    const { fixture, component, mockOps, mockSnackBar } = setup();
    mockOps.searchUsers.mockRejectedValue(new Error('network'));
    await component['performSearch']('test');
    expect(mockSnackBar.open).toHaveBeenCalledWith('Search failed', undefined, { duration: 5000 });
    fixture.destroy();
  });

  it('should unsubscribe on destroy', () => {
    const { fixture, component } = setup();
    const sub = component['searchSub'];
    expect(sub.closed).toBe(false);
    fixture.destroy();
    expect(sub.closed).toBe(true);
  });

  it('should set hasSearched after search', async () => {
    const { fixture, component } = setup();
    expect(component['hasSearched']()).toBe(false);
    await component['performSearch']('test');
    expect(component['hasSearched']()).toBe(true);
    fixture.destroy();
  });

  it('should show spinner when searching', async () => {
    const { fixture, component, mockOps } = setup();
    let resolveSearch!: (v: UserSearchResult[]) => void;
    mockOps.searchUsers.mockReturnValue(
      new Promise<UserSearchResult[]>((r) => {
        resolveSearch = r;
      }),
    );
    const searchPromise = component['performSearch']('alice');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('mat-spinner')).toBeTruthy();
    resolveSearch(STUB_RESULTS);
    await searchPromise;
    fixture.detectChanges();
    expect(el.querySelector('mat-spinner')).toBeFalsy();
    fixture.destroy();
  });

  it('should trigger search through debounced pipeline', async () => {
    const { fixture, component, mockOps } = setup();
    const ctrl = component['searchControl'];
    ctrl.setValue('alice');
    // Wait for debounce (300ms) and search to complete
    await vi.waitFor(
      () => {
        expect(mockOps.searchUsers).toHaveBeenCalledWith('alice');
      },
      { timeout: 1000 },
    );
    fixture.destroy();
  });

  it('should impersonate via table button click', async () => {
    const { fixture, component, mockOps } = setup();
    await component['performSearch']('alice');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('.results-table button') as HTMLButtonElement;
    expect(button).toBeTruthy();
    button.click();
    await vi.waitFor(() => {
      expect(mockOps.impersonate).toHaveBeenCalledWith(111);
    });
    fixture.destroy();
  });
});
