/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { PageTitleService } from '../../../../page-title.service';
import { CreateActivity } from './create-activity.component';

describe('CreateActivity', () => {
  function setup() {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockLayoutNavigation = { setContextSection: vi.fn(), clearContext: vi.fn() };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
    };

    TestBed.configureTestingModule({
      imports: [CreateActivity],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(CreateActivity);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockLayoutNavigation };
  }

  it('should set title and render activity type options', () => {
    const { fixture, mockPageTitle, mockLayoutNavigation } = setup();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Create Activity');
    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        visibleBaseRoutes: ['/courses/1/dashboard', '/courses/1/activities'],
      }),
    );
    expect(fixture.nativeElement.textContent).toContain('Create In Your Own Words');
  });
});
