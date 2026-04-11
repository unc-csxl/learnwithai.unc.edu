/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { OperationsShell } from './operations-shell.component';
import { AuthService } from '../../auth.service';
import { PageTitleService } from '../../page-title.service';
import { LayoutNavigationService } from '../../layout/layout-navigation.service';
import { provideRouter } from '@angular/router';

describe('OperationsShell', () => {
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

    const fixture = TestBed.createComponent(OperationsShell);
    fixture.detectChanges();

    return { fixture, component: fixture.componentInstance, mockTitle, mockNav };
  }

  it('should set page title to Operations', () => {
    const { mockTitle } = setup({
      role: 'superadmin',
      permissions: ['manage_operators', 'view_jobs', 'view_metrics', 'impersonate'],
    });
    expect(mockTitle.setTitle).toHaveBeenCalledWith('Operations');
  });

  it('should build navigation with all permissions', () => {
    const { mockNav } = setup({
      role: 'superadmin',
      permissions: ['manage_operators', 'view_jobs', 'view_metrics', 'impersonate'],
    });
    expect(mockNav.setSection).toHaveBeenCalledWith(
      expect.objectContaining({
        groups: [
          expect.objectContaining({
            items: expect.arrayContaining([
              expect.objectContaining({ route: '/operations/operators' }),
              expect.objectContaining({ route: '/operations/jobs' }),
              expect.objectContaining({ route: '/operations/metrics' }),
              expect.objectContaining({ route: '/operations/impersonate' }),
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
    expect(section.groups[0].items[0].route).toBe('/operations/jobs');
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
