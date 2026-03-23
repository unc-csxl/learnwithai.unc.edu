import { TestBed } from '@angular/core/testing';
import { LayoutNavigationService } from './layout-navigation.service';

describe('LayoutNavigationService', () => {
  it('should set and clear the active contextual section', () => {
    TestBed.configureTestingModule({});
    const service = TestBed.inject(LayoutNavigationService);

    expect(service.section()).toBeNull();

    service.setSection({
      label: 'Instructor view',
      title: 'COMP423',
      subtitle: 'Spring 2026 - Section 001',
      items: [
        {
          route: '/courses/1/dashboard',
          label: 'Dashboard',
          description: 'Course overview and quick links',
          icon: 'dashboard',
        },
      ],
    });

    expect(service.section()).toEqual({
      label: 'Instructor view',
      title: 'COMP423',
      subtitle: 'Spring 2026 - Section 001',
      items: [
        {
          route: '/courses/1/dashboard',
          label: 'Dashboard',
          description: 'Course overview and quick links',
          icon: 'dashboard',
        },
      ],
    });

    service.clear();

    expect(service.section()).toBeNull();
  });
});
