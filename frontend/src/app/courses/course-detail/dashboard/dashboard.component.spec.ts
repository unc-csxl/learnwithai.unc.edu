import { TestBed } from '@angular/core/testing';
import { Dashboard } from './dashboard.component';
import { PageTitleService } from '../../../page-title.service';

describe('Dashboard', () => {
  it('should set the page title and show overview copy', () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [{ provide: PageTitleService, useValue: mockPageTitle }],
    });

    const fixture = TestBed.createComponent(Dashboard);
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Dashboard');
    expect(fixture.nativeElement.textContent).toContain('Course dashboard');
  });
});