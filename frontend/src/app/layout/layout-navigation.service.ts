/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, computed, signal } from '@angular/core';

export type LayoutNavigationItem = {
  route: string;
  label: string;
  description?: string;
  icon: string;
  subtitle?: string;
  exact?: boolean;
};

export type LayoutNavigationGroup = {
  label?: string;
  items: LayoutNavigationItem[];
};

export type LayoutNavigationSection = {
  groups: LayoutNavigationGroup[];
  visibleBaseRoutes?: string[];
};

/** Stores contextual sidebar navigation shown inside the shared app shell. */
@Injectable({ providedIn: 'root' })
export class LayoutNavigationService {
  private readonly _section = signal<LayoutNavigationSection | null>(null);
  private readonly _contextSection = signal<LayoutNavigationSection | null>(null);

  /** The active contextual navigation section rendered in the app sidebar. */
  readonly section = computed<LayoutNavigationSection | null>(() => {
    const groups = [...this.visibleBaseGroups(), ...(this._contextSection()?.groups ?? [])];

    return groups.length > 0 ? { groups } : null;
  });

  /** Replace the base course navigation shown in the app sidebar. */
  setSection(section: LayoutNavigationSection | null): void {
    this._section.set(section);
  }

  /** Update the base course navigation in place. */
  updateSection(update: (section: LayoutNavigationSection) => LayoutNavigationSection): void {
    const currentSection = this._section();
    if (currentSection === null) {
      return;
    }

    this._section.set(update(currentSection));
  }

  /** Add or replace navigation that is specific to the current child route. */
  setContextSection(section: LayoutNavigationSection | null): void {
    this._contextSection.set(section);
  }

  /** Clear child-route-specific navigation while keeping the course navigation. */
  clearContext(): void {
    this._contextSection.set(null);
  }

  /** Clear all active navigation. */
  clear(): void {
    this._section.set(null);
    this._contextSection.set(null);
  }

  private visibleBaseGroups(): LayoutNavigationGroup[] {
    const section = this._section();
    if (section === null) {
      return [];
    }

    const visibleBaseRoutes = this._contextSection()?.visibleBaseRoutes;
    if (visibleBaseRoutes === undefined) {
      return section.groups;
    }

    const visibleRouteSet = new Set(visibleBaseRoutes);
    return section.groups
      .map((group) => ({
        ...group,
        items: group.items.filter((item) => visibleRouteSet.has(item.route)),
      }))
      .filter((group) => group.items.length > 0);
  }
}
