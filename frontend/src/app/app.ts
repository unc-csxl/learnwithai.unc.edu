import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/** Shell component that hosts the application router outlet. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class App {}
