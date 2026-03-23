import { TestBed } from '@angular/core/testing';
import { Tools } from './tools.component';
import { PageTitleService } from '../../../page-title.service';

describe('Tools', () => {
  it('should set the page title and show instructor tools copy', () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Tools],
      providers: [{ provide: PageTitleService, useValue: mockPageTitle }],
    });

    const fixture = TestBed.createComponent(Tools);
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Instructor Tools');
    expect(fixture.nativeElement.textContent).toContain('Instructor Tools');
  });
});
