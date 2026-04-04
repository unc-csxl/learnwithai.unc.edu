import { TestBed } from '@angular/core/testing';
import { StudentView } from './student-view.component';
import { PageTitleService } from '../../../page-title.service';

describe('StudentView', () => {
  it('should set the page title and show student dashboard copy', () => {
    const mockPageTitle = {
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [StudentView],
      providers: [{ provide: PageTitleService, useValue: mockPageTitle }],
    });

    const fixture = TestBed.createComponent(StudentView);
    fixture.detectChanges();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Student Dashboard');
    expect(fixture.nativeElement.textContent).toContain('Student Dashboard');
  });
});
