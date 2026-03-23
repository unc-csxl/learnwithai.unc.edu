import { TestBed } from '@angular/core/testing';
import { StudentView } from './student-view.component';
import { PageTitleService } from '../../../page-title.service';

describe('StudentView', () => {
  it('should set the page title and show student tools copy', () => {
    const mockPageTitle = {
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [StudentView],
      providers: [{ provide: PageTitleService, useValue: mockPageTitle }],
    });

    const fixture = TestBed.createComponent(StudentView);
    fixture.detectChanges();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Student Tools');
    expect(fixture.nativeElement.textContent).toContain('Student Tools');
  });
});
