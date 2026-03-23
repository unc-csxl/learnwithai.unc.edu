import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { PageTitleService } from '../../../page-title.service';

/** Placeholder for the instructor tools view. */
@Component({
  selector: 'app-tools',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="space-y-3">
      <p class="text-sm opacity-75">Instructor Tools</p>
      <p>Instructor tools and automations will live here soon.</p>
    </section>
  `,
})
export class Tools {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Instructor Tools');
  }
}
