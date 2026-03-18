import { Injectable, signal } from '@angular/core';

/** Reactive page title shared between the layout shell and child components. */
@Injectable({ providedIn: 'root' })
export class PageTitleService {
  private readonly _title = signal('');

  /** The current page title displayed in the toolbar. */
  readonly title = this._title.asReadonly();

  /** Set the current page title. Also updates the browser tab title. */
  setTitle(title: string): void {
    this._title.set(title);
    document.title = title ? `${title} – Learn with AI` : 'Learn with AI';
  }
}
