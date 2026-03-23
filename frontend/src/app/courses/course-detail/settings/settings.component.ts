import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { PageTitleService } from '../../../page-title.service';

/** Placeholder for course settings. */
@Component({
  selector: 'app-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './settings.component.html',
})
export class Settings {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Course Settings');
  }
}