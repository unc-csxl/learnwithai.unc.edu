/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { AdminShell } from './admin-shell.component';
import { AuthService } from '../../auth.service';
import { PageTitleService } from '../../page-title.service';
import { LayoutNavigationService } from '../../layout/layout-navigation.service';
import { provideRouter } from '@angular/router';

describe('AdminShell', () => {
  function setup(operator: { role: string; permissions: string[] } | null) {
    const mockAuth = {
      user: signal(operator ? { name: 'Admin', pid: 123, operator } : { name: 'User', pid: 456 }),
    };
    const mockTitle = { setTitle: vi.fn() };
    const mockNav = { setSection: vi.fn(), clear: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuth },
        { provide: PageTitleService, useValue: mockTitle },
        { provide: LayoutNavigationService, useValue: mockNav },
      ],
    });

    const fixture = TestBed.createComponent(AdminShell);
    fixture.detectChanges();

    return { fixture, component: fixture.componentInstance, mockTitle, mockNav };
  }

  it('should set page title to Admin Tools', () => {
    const { mockTitle } = setup({
      role: 'superadmin',
      permissions: ['manage_operators', 'view_jobs', 'view_metrics'],
    });
    expect(mockTitle.setTitle).toHaveBeenCalledWith('Admin Tools');
  });

  it('should build navigation with all permissions', () => {
    const { mockNav } = setup({
      role: 'superadmin',
      permissions: ['manage_operators', 'view_jobs', 'view_metrics'],
    });
    expect(mockNav.setSection).toHaveBeenCalledWith(
      expect.objectContaining({
        groups: [
          expect.objectContaining({
            items: expect.arrayContaining([
              expect.objectContaining({ route: '/admin/operators' }),
              expect.objectContaining({ route: '/admin/jobs' }),
              expect.objectContaining({ route: '/admin/metrics' }),
            ]),
          }),
        ],
      }),
    );
  });

  it('should build navigation with only helpdesk permissions', () => {
    const { mockNav } = setup({
      role: 'helpdesk',
      permissions: ['view_jobs'],
    });
    const section = mockNav.setSection.mock.calls[0][0];
    expect(section.groups[0].items).toHaveLength(1);
    expect(section.groups[0].items[0].route).toBe('/admin/jobs');
  });

  it('should show error when no operator access', () => {
    const { fixture, mockNav } = setup(null);
    const errorEl = fixture.nativeElement.querySelector('.error');
    expect(errorEl?.textContent).toContain('Operator access required');
    expect(mockNav.setSection).not.toHaveBeenCalled();
  });

  it('should clear navigation on destroy', () => {
    const { fixture, mockNav } = setup({
      role: 'admin',
      permissions: ['manage_operators'],
    });
    fixture.destroy();
    expect(mockNav.clear).toHaveBeenCalled();
  });
});
