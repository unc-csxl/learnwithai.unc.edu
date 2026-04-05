import { buildActivityContextNav } from './activity-nav';

describe('buildActivityContextNav', () => {
  const baseOptions = { courseId: 1, activityId: 10, activityTitle: 'Test IYOW' };

  it('should produce 3 sibling items for staff', () => {
    const result = buildActivityContextNav({ ...baseOptions, role: 'staff' });

    expect(result.visibleBaseRoutes).toEqual(['/courses/1/dashboard', '/courses/1/activities']);
    expect(result.groups).toHaveLength(1);

    const items = result.groups[0].items;
    expect(items).toHaveLength(3);
    expect(items[0]).toEqual(
      expect.objectContaining({ route: '/courses/1/activities/10', label: 'Test IYOW' }),
    );
    expect(items[1]).toEqual(
      expect.objectContaining({ route: '/courses/1/activities/10/edit', label: 'Activity Editor' }),
    );
    expect(items[2]).toEqual(
      expect.objectContaining({
        route: '/courses/1/activities/10/submit',
        label: 'Preview & Test',
      }),
    );
  });

  it('should produce 1 item for student', () => {
    const result = buildActivityContextNav({ ...baseOptions, role: 'student' });

    expect(result.visibleBaseRoutes).toEqual(['/courses/1/student', '/courses/1/activities']);
    expect(result.groups).toHaveLength(1);

    const items = result.groups[0].items;
    expect(items).toHaveLength(1);
    expect(items[0]).toEqual(
      expect.objectContaining({ route: '/courses/1/activities/10/submit', label: 'Test IYOW' }),
    );
  });

  it('should append extra groups', () => {
    const extraGroups = [
      {
        label: 'Submission',
        items: [
          {
            route: '/courses/1/activities/10/submissions/111',
            label: 'Student 111',
            icon: 'person',
          },
        ],
      },
    ];
    const result = buildActivityContextNav({ ...baseOptions, role: 'staff', extraGroups });

    expect(result.groups).toHaveLength(2);
    expect(result.groups[0].label).toBe('Current activity');
    expect(result.groups[1]).toEqual(
      expect.objectContaining({ label: 'Submission', items: extraGroups[0].items }),
    );
  });

  it('should label the group "Current activity"', () => {
    const result = buildActivityContextNav({ ...baseOptions, role: 'staff' });
    expect(result.groups[0].label).toBe('Current activity');
  });
});
