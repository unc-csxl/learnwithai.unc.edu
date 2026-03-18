import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { CreateCourse } from './create-course';
import { CourseService } from '../course.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CreateCourse', () => {
  function setup() {
    const mockService = {
      createCourse: vi.fn(() =>
        Promise.resolve({ id: 5, name: 'Algo', term: 'Fall 2026', section: '001' }),
      ),
    };

    TestBed.configureTestingModule({
      imports: [CreateCourse],
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
    expect(el.querySelector('input#name')).toBeTruthy();
    expect(el.querySelector('input#term')).toBeTruthy();
    expect(el.querySelector('input#section')).toBeTruthy();
  });

  it('should disable submit when form is empty', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should submit the form and navigate on success', async () => {
    const { fixture, mockService, router } = setup();
    const component = fixture.componentInstance;
    component['form'].setValue({
      name: 'Algo',
      term: 'Fall 2026',
      section: '001',
    });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(false);

    button.click();
    await flush();

    expect(mockService.createCourse).toHaveBeenCalledWith({
      name: 'Algo',
      term: 'Fall 2026',
      section: '001',
    });
    expect(router.navigate).toHaveBeenCalledWith(['/courses', 5]);
  });

  it('should not submit when form is invalid', () => {
    const { fixture, mockService } = setup();
    const component = fixture.componentInstance;
    component['onSubmit']();
    expect(mockService.createCourse).not.toHaveBeenCalled();
  });
});
