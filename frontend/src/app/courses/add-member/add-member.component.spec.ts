/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, ActivatedRoute } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { AddMember } from './add-member.component';
import { CourseService } from '../course.service';
import { LayoutNavigationService } from '../../layout/layout-navigation.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('AddMember', () => {
  function setup() {
    const mockService = {
      addMember: vi.fn(() =>
        Promise.resolve({
          user_pid: 999,
          course_id: 1,
          type: 'student' as const,
          state: 'pending' as const,
        }),
      ),
    };

    const mockRoute = {
      parent: { snapshot: { paramMap: new Map([['id', '1']]) } },
    };
    const mockLayoutNavigation = { clearContext: vi.fn() };

    TestBed.configureTestingModule({
      imports: [AddMember, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: CourseService, useValue: mockService },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(AddMember);
    fixture.detectChanges();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    return { fixture, mockService, router, mockLayoutNavigation };
  }

  it('should render the form', () => {
    const { fixture, mockLayoutNavigation } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(el.querySelector('input[formControlName="pid"]')).toBeTruthy();
    expect(el.querySelector('mat-select')).toBeTruthy();
  });

  it('should disable submit when pid is invalid', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should submit the form and navigate on success', async () => {
    const { fixture, mockService, router } = setup();
    const component = fixture.componentInstance;
    component['form'].setValue({ pid: 999, type: 'student' });
    fixture.detectChanges();

    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    await flush();

    expect(mockService.addMember).toHaveBeenCalledWith(1, {
      pid: 999,
      type: 'student',
    });
    expect(router.navigate).toHaveBeenCalledWith(['../roster'], { relativeTo: expect.anything() });
  });

  it('should not submit when form is invalid', () => {
    const { fixture, mockService } = setup();
    const component = fixture.componentInstance;
    component['onSubmit']();
    expect(mockService.addMember).not.toHaveBeenCalled();
  });
});
