import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CourseService } from '../course.service';
import { MembershipResponse } from '../../api/generated/models/membership-response';

/** Displays the roster for a course. Instructors see all members. */
@Component({
  selector: 'app-course-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <main>
      <nav>
        <a routerLink="/courses">&larr; Back to courses</a>
      </nav>
      <h1>Course Roster</h1>
      @if (errorMessage()) {
        <p role="alert">{{ errorMessage() }}</p>
      } @else if (roster().length > 0) {
        <a [routerLink]="['/courses', courseId, 'add-member']" role="button">Add Member</a>
        <table>
          <caption class="sr-only">
            Members of this course
          </caption>
          <thead>
            <tr>
              <th scope="col">PID</th>
              <th scope="col">Role</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            @for (member of roster(); track member.user_pid) {
              <tr>
                <td>{{ member.user_pid }}</td>
                <td>{{ member.type }}</td>
                <td>{{ member.state }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else if (loaded()) {
        <p>No members found for this course.</p>
      }
    </main>
  `,
  styles: `
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
  `,
})
export class CourseDetail {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);

  protected readonly roster = signal<MembershipResponse[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly courseId: number;

  constructor() {
    this.courseId = Number(this.route.snapshot.paramMap.get('id'));
    this.courseService.getRoster(this.courseId).subscribe({
      next: (roster) => {
        this.roster.set(roster);
        this.loaded.set(true);
      },
      error: (err) => {
        if (err.status === 403) {
          this.errorMessage.set('You do not have permission to view this roster.');
        } else {
          this.errorMessage.set('Failed to load roster.');
        }
        this.loaded.set(true);
      },
    });
  }
}
