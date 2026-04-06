import { TestBed } from '@angular/core/testing';
import { Dashboard } from './dashboard.component';
import { PageTitleService } from '../../../page-title.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';

describe('Dashboard', () => {
  it('should set the page title and show overview copy', () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };
    const mockLayoutNavigation = { clearContext: vi.fn() };

    TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(Dashboard);
    fixture.detectChanges();

    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Dashboard');
    expect(fixture.nativeElement.textContent).toContain('Course dashboard');
  });
});
