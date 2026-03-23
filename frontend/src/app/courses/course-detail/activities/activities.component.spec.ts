import { TestBed } from '@angular/core/testing';
import { Activities } from './activities.component';
import { PageTitleService } from '../../../page-title.service';

describe('Activities', () => {
  it('should set the page title and show student activities copy', () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Activities],
      providers: [{ provide: PageTitleService, useValue: mockPageTitle }],
    });

    const fixture = TestBed.createComponent(Activities);
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Student Activities');
    expect(fixture.nativeElement.textContent).toContain('Student Activities');
  });
});
