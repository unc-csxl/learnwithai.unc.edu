/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CreateCourse } from './create-course.component';
import { CourseService } from '../course.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CreateCourse', () => {
  function setup() {
    const mockService = {
      createCourse: vi.fn(() =>
        Promise.resolve({
          id: 5,
          course_number: 'COMP301',
          name: 'Algo',
          description: '',
          term: 'fall',
          year: 2026,
        }),
      ),
    };

    TestBed.configureTestingModule({
      imports: [CreateCourse, NoopAnimationsModule],
      providers: [provideRouter([]), { provide: CourseService, useValue: mockService }],
    });

    const fixture = TestBed.createComponent(CreateCourse);
    fixture.detectChanges();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    return { fixture, mockService, router };
  }

  it('should render the form', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('input[formControlName="course_number"]')).toBeTruthy();
    expect(el.querySelector('input[formControlName="name"]')).toBeTruthy();
    expect(el.querySelector('textarea[formControlName="description"]')).toBeTruthy();
    expect(el.querySelector('mat-select[formControlName="term"]')).toBeTruthy();
    expect(el.querySelector('input[formControlName="year"]')).toBeTruthy();
  });

  it('should disable submit when form is empty', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance;
    component['form'].patchValue({
      course_number: '',
      name: '',
      term: '',
      year: null as unknown as number,
    });
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should submit the form and navigate on success', async () => {
    const { fixture, mockService, router } = setup();
    const component = fixture.componentInstance;
    component['form'].setValue({
      course_number: 'COMP301',
      name: 'Algo',
      description: '',
      term: 'fall',
      year: 2026,
    });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(false);

    button.click();
    await flush();

    expect(mockService.createCourse).toHaveBeenCalledWith({
      course_number: 'COMP301',
      name: 'Algo',
      description: '',
      term: 'fall',
      year: 2026,
    });
    expect(router.navigate).toHaveBeenCalledWith(['/courses', 5]);
  });

  it('should not submit when form is invalid', () => {
    const { fixture, mockService } = setup();
    const component = fixture.componentInstance;
    component['form'].patchValue({
      course_number: '',
      name: '',
      term: '',
      year: null as unknown as number,
    });
    component['onSubmit']();
    expect(mockService.createCourse).not.toHaveBeenCalled();
  });
});
