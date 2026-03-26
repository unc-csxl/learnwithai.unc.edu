import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { PageTitleService } from '../../../page-title.service';

/** Landing page listing the available instructor tools. */
@Component({
  selector: 'app-tools',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, MatCardModule, MatIconModule],
  templateUrl: './tools.component.html',
  styleUrl: './tools.component.scss',
})
export class Tools {
  private titleService = inject(PageTitleService);

  constructor() {
    this.titleService.setTitle('Instructor Tools');
  }
}
