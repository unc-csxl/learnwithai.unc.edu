import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { PageTitleService } from '../../../page-title.service';

/** Placeholder for student-facing course tools. */
@Component({
  selector: 'app-student-view',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section>
      <p class="text-sm opacity-75">Student Tools</p>
      <p>Student-facing course tools will live here soon.</p>
    </section>
  `,
})
export class StudentView {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Student Tools');
  }
}
