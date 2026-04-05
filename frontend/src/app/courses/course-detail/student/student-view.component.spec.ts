import { TestBed } from '@angular/core/testing';
import { StudentView } from './student-view.component';
import { PageTitleService } from '../../../page-title.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';

describe('StudentView', () => {
  it('should set the page title and show student dashboard copy', () => {
    const mockPageTitle = {
      setTitle: vi.fn(),
    };
    const mockLayoutNavigation = { clearContext: vi.fn() };

    TestBed.configureTestingModule({
      imports: [StudentView],
      providers: [
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(StudentView);
    fixture.detectChanges();
    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Student Dashboard');
    expect(fixture.nativeElement.textContent).toContain('Student Dashboard');
  });
});
