import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Tools } from './tools.component';
import { PageTitleService } from '../../../page-title.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';

describe('Tools', () => {
  it('should set the page title and render a Joke Generator card', () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };
    const mockLayoutNavigation = { clearContext: vi.fn() };

    TestBed.configureTestingModule({
      imports: [Tools],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(Tools);
    fixture.detectChanges();

    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Instructor Tools');
    expect(fixture.nativeElement.textContent).toContain('Joke Generator');
  });
});
