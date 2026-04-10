/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  OnDestroy,
  effect,
  DestroyRef,
  Injector,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CourseService } from '../../course.service';
import {
  MEMBERSHIP_TYPE,
  MembershipType,
  RosterMember,
  RosterUploadStatus,
} from '../../../api/models';
import { AuthService } from '../../../auth.service';
import { PageTitleService } from '../../../page-title.service';
import { JobUpdateService } from '../../../job-update.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';
import { SuccessSnackbarService } from '../../../success-snackbar.service';
import { RosterUploadResultDialog } from './roster-upload-result-dialog.component';

const DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 3;

/** Displays the roster for a course. */
@Component({
  selector: 'app-roster',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSnackBarModule,
    MatDialogModule,
  ],
  templateUrl: './roster.component.html',
  styleUrl: './roster.component.scss',
})
export class Roster implements OnDestroy {
  private courseService = inject(CourseService);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private snackBar = inject(MatSnackBar);
  private dialog = inject(MatDialog);
  private jobUpdateService = inject(JobUpdateService);
  private layoutNavigation = inject(LayoutNavigationService);
  private successSnackbar = inject(SuccessSnackbarService);
  private injector = inject(Injector);
  private destroyRef = inject(DestroyRef);
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  protected readonly roster = signal<RosterMember[]>([]);
  protected readonly viewerRole = signal<MembershipType | null>(null);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = signal(10);
  protected readonly searchQuery = signal('');
  protected readonly savingRoleByUserPid = signal<Record<number, boolean>>({});
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly uploading = signal(false);
  protected readonly courseId: number;
  protected readonly currentUserPid = computed(() => this.authService.user()?.pid ?? null);
  protected readonly displayedColumns = ['given_name', 'family_name', 'user_pid', 'email', 'type'];
  protected readonly roleOptions = MEMBERSHIP_TYPE;
  protected readonly dataSource = computed(() => this.roster());

  constructor() {
    this.layoutNavigation.clearContext();
    this.titleService.setTitle('Roster');
    this.courseId = Number(this.route.parent?.snapshot.paramMap.get('id'));
    this.jobUpdateService.subscribe(this.courseId);
    void this.loadViewerRole();
    void this.loadRoster();
  }

  ngOnDestroy(): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    this.jobUpdateService.unsubscribe(this.courseId);
  }

  protected onSearchInput(value: string): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      const query = value.length >= MIN_SEARCH_LENGTH ? value : '';
      if (query !== this.searchQuery()) {
        this.searchQuery.set(query);
        this.page.set(1);
        this.loadRoster();
      }
    }, DEBOUNCE_MS);
  }

  protected onPage(event: PageEvent): void {
    this.page.set(event.pageIndex + 1);
    this.pageSize.set(event.pageSize);
    this.loadRoster();
  }

  protected isInactive(member: RosterMember): boolean {
    return member.state !== 'enrolled';
  }

  protected canEditRole(member: RosterMember): boolean {
    const currentUserPid = this.currentUserPid();

    return (
      this.viewerRole() === 'instructor' &&
      currentUserPid !== null &&
      member.state !== 'dropped' &&
      member.user_pid !== currentUserPid
    );
  }

  protected isSavingRole(userPid: number): boolean {
    return Boolean(this.savingRoleByUserPid()[userPid]);
  }

  protected roleLabel(role: MembershipType): string {
    return role === 'ta' ? 'TA' : role.charAt(0).toUpperCase() + role.slice(1);
  }

  protected async onRoleChange(member: RosterMember, nextRole: MembershipType): Promise<void> {
    if (!this.canEditRole(member) || nextRole === member.type) {
      return;
    }

    const previousRole = member.type;
    this.updateRosterMemberRole(member.user_pid, nextRole);
    this.setSavingRole(member.user_pid, true);

    try {
      const updatedMembership = await this.courseService.updateMemberRole(
        this.courseId,
        member.user_pid,
        {
          type: nextRole,
        },
      );
      this.updateRosterMemberRole(member.user_pid, updatedMembership.type);
      this.successSnackbar.open(
        `Updated ${member.given_name} ${member.family_name} to ${this.roleLabel(updatedMembership.type)}.`,
      );
    } catch {
      this.updateRosterMemberRole(member.user_pid, previousRole);
      this.snackBar.open('Failed to update member role.', 'Dismiss', {
        duration: 5000,
      });
    } finally {
      this.setSavingRole(member.user_pid, false);
    }
  }

  protected async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.uploading.set(true);
    try {
      const result = await this.courseService.uploadRoster(this.courseId, file);
      this.snackBar.open('Roster upload processing…', undefined, {
        duration: 0,
      });
      this.watchJobUpdate(result.id);
    } catch {
      this.snackBar.open('Failed to upload roster CSV.', 'Dismiss', {
        duration: 5000,
      });
    } finally {
      this.uploading.set(false);
      input.value = '';
    }
  }

  // ------------------------------------------------------------------
  // Private helpers
  // ------------------------------------------------------------------

  private async loadViewerRole(): Promise<void> {
    try {
      const courses = await this.courseService.getMyCourses();
      const currentCourse = courses.find((course) => course.id === this.courseId);
      this.viewerRole.set(currentCourse?.membership.type ?? null);
    } catch {
      this.viewerRole.set(null);
    }
  }

  private watchJobUpdate(jobId: number): void {
    const jobSignal = this.jobUpdateService.updateForJob(jobId);
    const effectRef = effect(
      async () => {
        const update = jobSignal();
        if (update === null) return;
        if (update.status !== 'completed' && update.status !== 'failed') return;

        effectRef.destroy();
        await this.handleJobFinished(jobId);
      },
      { injector: this.injector },
    );
    this.destroyRef.onDestroy(() => effectRef.destroy());
  }

  private async handleJobFinished(jobId: number): Promise<void> {
    this.snackBar.dismiss();
    try {
      const status = await this.courseService.getRosterUploadStatus(this.courseId, jobId);
      this.showUploadResult(status);
      await this.loadRoster();
    } catch {
      this.snackBar.open('Failed to check upload status.', 'Dismiss', {
        duration: 5000,
      });
    }
  }

  private showUploadResult(status: RosterUploadStatus): void {
    this.dialog.open(RosterUploadResultDialog, {
      data: status,
      width: '400px',
    });
  }

  private setSavingRole(userPid: number, saving: boolean): void {
    this.savingRoleByUserPid.update((savingStates) => {
      if (saving) {
        return { ...savingStates, [userPid]: true };
      }

      const remainingStates = { ...savingStates };
      delete remainingStates[userPid];
      return remainingStates;
    });
  }

  private updateRosterMemberRole(userPid: number, role: MembershipType): void {
    this.roster.update((members) =>
      members.map((member) => (member.user_pid === userPid ? { ...member, type: role } : member)),
    );
  }

  private async loadRoster(): Promise<void> {
    try {
      const result = await this.courseService.getRoster(this.courseId, {
        page: this.page(),
        pageSize: this.pageSize(),
        query: this.searchQuery() || undefined,
      });
      this.roster.set(result.items);
      this.total.set(result.total);
    } catch (err: unknown) {
      if (err != null && typeof err === 'object' && 'status' in err && err.status === 403) {
        this.errorMessage.set('You do not have permission to view this roster.');
      } else {
        this.errorMessage.set('Failed to load roster.');
      }
    } finally {
      this.loaded.set(true);
    }
  }
}
