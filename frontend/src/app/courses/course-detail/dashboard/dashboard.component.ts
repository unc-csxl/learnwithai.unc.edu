import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { PageTitleService } from '../../../page-title.service';

/** Landing view for instructor course navigation. */
@Component({
  selector: 'app-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './dashboard.component.html',
})
export class Dashboard {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Dashboard');
  }
}