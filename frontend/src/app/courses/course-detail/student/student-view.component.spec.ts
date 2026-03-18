import { TestBed } from '@angular/core/testing';
import { StudentView } from './student-view.component';

describe('StudentView', () => {
  it('should show coming soon message', () => {
    TestBed.configureTestingModule({ imports: [StudentView] });
    const fixture = TestBed.createComponent(StudentView);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('coming soon');
  });
});
