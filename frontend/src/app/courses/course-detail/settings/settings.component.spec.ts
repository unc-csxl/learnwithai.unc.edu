import { TestBed } from '@angular/core/testing';
import { Settings } from './settings.component';
import { PageTitleService } from '../../../page-title.service';

describe('Settings', () => {
  it('should set the page title and show settings copy', () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Settings],
      providers: [{ provide: PageTitleService, useValue: mockPageTitle }],
    });

    const fixture = TestBed.createComponent(Settings);
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Course Settings');
    expect(fixture.nativeElement.textContent).toContain('Course Settings');
  });
});
