import { TestBed } from '@angular/core/testing';
import { Activities } from './activities.component';

describe('Activities', () => {
  it('should show coming soon message', () => {
    TestBed.configureTestingModule({ imports: [Activities] });
    const fixture = TestBed.createComponent(Activities);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('coming soon');
  });
});
