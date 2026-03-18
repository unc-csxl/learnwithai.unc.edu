import { TestBed } from '@angular/core/testing';
import { Tools } from './tools.component';

describe('Tools', () => {
  it('should show coming soon message', () => {
    TestBed.configureTestingModule({ imports: [Tools] });
    const fixture = TestBed.createComponent(Tools);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('coming soon');
  });
});
