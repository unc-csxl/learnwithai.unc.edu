import { Injectable, signal } from '@angular/core';

export type LayoutNavigationItem = {
  route: string;
  label: string;
  description?: string;
  icon: string;
};

export type LayoutNavigationSection = {
  label: string;
  title?: string;
  subtitle?: string;
  items: LayoutNavigationItem[];
};

/** Stores contextual sidebar navigation shown inside the shared app shell. */
@Injectable({ providedIn: 'root' })
export class LayoutNavigationService {
  private readonly _section = signal<LayoutNavigationSection | null>(null);

  /** The active contextual navigation section rendered in the app sidebar. */
  readonly section = this._section.asReadonly();

  /** Replace the current contextual navigation. */
  setSection(section: LayoutNavigationSection | null): void {
    this._section.set(section);
  }

  /** Clear any active contextual navigation. */
  clear(): void {
    this._section.set(null);
  }
}