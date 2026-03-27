import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { PageTitleService } from '../../../page-title.service';

/** Landing view for instructor course navigation. */
@Component({
  selector: 'app-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule],
  templateUrl: './dashboard.component.html',
})
export class Dashboard {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Dashboard');
  }
}
