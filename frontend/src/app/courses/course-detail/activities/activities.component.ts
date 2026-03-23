import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { PageTitleService } from '../../../page-title.service';

/** Placeholder for the student activities view. */
@Component({
  selector: 'app-activities',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="space-y-3">
      <p class="text-sm opacity-75">Student Activities</p>
      <p>Student activity workflows will live here soon.</p>
    </section>
  `,
})
export class Activities {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Student Activities');
  }
}
