import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { RosterUploadStatus } from '../../../api/models';

/** Dialog that displays the results of a roster CSV upload. */
@Component({
  selector: 'app-roster-upload-result-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatDialogModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Upload Results</h2>
    <mat-dialog-content>
      @if (data.status === 'completed') {
        <p>
          Created: <strong>{{ data.created_count }}</strong>
        </p>
        <p>
          Updated: <strong>{{ data.updated_count }}</strong>
        </p>
        @if (data.error_count > 0) {
          <p>
            Errors: <strong>{{ data.error_count }}</strong>
          </p>
          <pre class="error-details">{{ data.error_details }}</pre>
        }
      } @else {
        <p role="alert">The upload failed. Please try again.</p>
        @if (data.error_details) {
          <pre class="error-details">{{ data.error_details }}</pre>
        }
      }
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-flat-button mat-dialog-close>Close</button>
    </mat-dialog-actions>
  `,
  styles: `
    .error-details {
      max-height: 200px;
      overflow-y: auto;
      font-size: 0.85rem;
      white-space: pre-wrap;
      background: var(--mat-sys-surface-variant);
      padding: 8px;
      border-radius: 4px;
    }
  `,
})
export class RosterUploadResultDialog {
  protected readonly data = inject<RosterUploadStatus>(MAT_DIALOG_DATA);
}
