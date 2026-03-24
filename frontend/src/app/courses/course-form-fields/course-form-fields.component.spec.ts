import { TestBed } from '@angular/core/testing';
import { FormGroup, FormControl, ReactiveFormsModule } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CourseFormFields } from './course-form-fields.component';

describe('CourseFormFields', () => {
  it('should render all five course form fields', () => {
    TestBed.configureTestingModule({
      imports: [CourseFormFields, ReactiveFormsModule, NoopAnimationsModule],
    });

    const fixture = TestBed.createComponent(CourseFormFields);
    fixture.componentRef.setInput(
      'formGroup',
      new FormGroup({
        course_number: new FormControl(''),
        name: new FormControl(''),
        description: new FormControl(''),
        term: new FormControl(''),
        year: new FormControl(2026),
      }),
    );
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('input[formControlName="course_number"]')).toBeTruthy();
    expect(el.querySelector('input[formControlName="name"]')).toBeTruthy();
    expect(el.querySelector('textarea[formControlName="description"]')).toBeTruthy();
    expect(el.querySelector('mat-select[formControlName="term"]')).toBeTruthy();
    expect(el.querySelector('input[formControlName="year"]')).toBeTruthy();
  });
});
