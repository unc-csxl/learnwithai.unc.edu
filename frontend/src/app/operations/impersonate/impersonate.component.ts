/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal, OnDestroy } from '@angular/core';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, filter, switchMap } from 'rxjs/operators';
import { OperationsService } from '../operations.service';
import { PageTitleService } from '../../page-title.service';
import { UserSearchResult } from '../../api/models';

/** Allows operators to search for users and impersonate them. */
@Component({
  selector: 'app-impersonate',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    MatTableModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './impersonate.component.html',
  styleUrl: './impersonate.component.scss',
})
export class ImpersonateComponent implements OnDestroy {
  private operationsService = inject(OperationsService);
  private snackBar = inject(MatSnackBar);
  private titleService = inject(PageTitleService);

  protected readonly searchControl = new FormControl('', { nonNullable: true });
  protected readonly results = signal<UserSearchResult[]>([]);
  protected readonly searching = signal(false);
  protected readonly hasSearched = signal(false);
  protected readonly displayedColumns = ['pid', 'name', 'email', 'actions'];

  private searchSub: Subscription;

  constructor() {
    this.titleService.setTitle('Impersonate User');
    this.searchSub = this.searchControl.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        filter((query) => query.trim().length >= 2),
        switchMap((query) => this.performSearch(query.trim())),
      )
      .subscribe();
  }

  ngOnDestroy(): void {
    this.searchSub.unsubscribe();
  }

  protected async onImpersonate(user: UserSearchResult): Promise<void> {
    try {
      await this.operationsService.impersonate(user.pid);
    } catch {
      this.snackBar.open('Failed to start impersonation', undefined, { duration: 5000 });
    }
  }

  private async performSearch(query: string): Promise<void> {
    this.searching.set(true);
    try {
      const users = await this.operationsService.searchUsers(query);
      this.results.set(users);
    } catch {
      this.results.set([]);
      this.snackBar.open('Search failed', undefined, { duration: 5000 });
    } finally {
      this.searching.set(false);
      this.hasSearched.set(true);
    }
  }
}
