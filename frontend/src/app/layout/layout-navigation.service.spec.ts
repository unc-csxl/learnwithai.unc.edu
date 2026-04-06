import { TestBed } from '@angular/core/testing';
import { LayoutNavigationService } from './layout-navigation.service';

describe('LayoutNavigationService', () => {
  it('should merge base and child-route navigation and clear them independently', () => {
    TestBed.configureTestingModule({});
    const service = TestBed.inject(LayoutNavigationService);

    expect(service.section()).toBeNull();

    service.setSection({
      groups: [
        {
          label: 'Course',
          items: [
            {
              route: '/courses/1/dashboard',
              label: 'COMP423',
              subtitle: 'Spring 2026 - Section 001',
              description: 'Course overview and quick links',
              icon: 'dashboard',
            },
          ],
        },
      ],
    });

    expect(service.section()).toEqual({
      groups: [
        {
          label: 'Course',
          items: [
            {
              route: '/courses/1/dashboard',
              label: 'COMP423',
              subtitle: 'Spring 2026 - Section 001',
              description: 'Course overview and quick links',
              icon: 'dashboard',
            },
          ],
        },
      ],
    });

    service.updateSection((section) => ({
      groups: [
        {
          ...section.groups[0],
          items: section.groups[0].items.map((item, index) =>
            index === 0 ? { ...item, label: 'COMP426' } : item,
          ),
        },
      ],
    }));

    expect(service.section()?.groups[0].items[0].label).toBe('COMP426');

    service.setContextSection({
      visibleBaseRoutes: ['/courses/1/dashboard'],
      groups: [
        {
          label: 'Current activity',
          items: [
            {
              route: '/courses/1/activities/10',
              label: 'Explain Dependency Injection',
              icon: 'assignment',
              exact: false,
            },
          ],
        },
      ],
    });

    expect(service.section()).toEqual({
      groups: [
        {
          label: 'Course',
          items: [
            {
              route: '/courses/1/dashboard',
              label: 'COMP426',
              subtitle: 'Spring 2026 - Section 001',
              description: 'Course overview and quick links',
              icon: 'dashboard',
            },
          ],
        },
        {
          label: 'Current activity',
          items: [
            {
              route: '/courses/1/activities/10',
              label: 'Explain Dependency Injection',
              icon: 'assignment',
              exact: false,
            },
          ],
        },
      ],
    });

    service.clearContext();

    expect(service.section()).toEqual({
      groups: [
        {
          label: 'Course',
          items: [
            {
              route: '/courses/1/dashboard',
              label: 'COMP426',
              subtitle: 'Spring 2026 - Section 001',
              description: 'Course overview and quick links',
              icon: 'dashboard',
            },
          ],
        },
      ],
    });

    service.clear();

    expect(service.section()).toBeNull();

    service.updateSection((section) => section);

    expect(service.section()).toBeNull();
  });
});
