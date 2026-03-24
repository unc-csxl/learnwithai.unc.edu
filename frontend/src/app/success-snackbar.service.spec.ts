import { TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SuccessSnackbarService } from './success-snackbar.service';

describe('SuccessSnackbarService', () => {
  function setup() {
    const mockSnackBar = { open: vi.fn() };
    TestBed.configureTestingModule({
      providers: [SuccessSnackbarService, { provide: MatSnackBar, useValue: mockSnackBar }],
    });
    return { service: TestBed.inject(SuccessSnackbarService), mockSnackBar };
  }

  it('should open a snackbar with the given message and default 5 s duration', () => {
    const { service, mockSnackBar } = setup();
    service.open('Saved!');
    expect(mockSnackBar.open).toHaveBeenCalledWith('Saved!', undefined, {
      duration: 5000,
      politeness: 'polite',
    });
  });

  it('should support a custom duration', () => {
    const { service, mockSnackBar } = setup();
    service.open('Done', 3000);
    expect(mockSnackBar.open).toHaveBeenCalledWith('Done', undefined, {
      duration: 3000,
      politeness: 'polite',
    });
  });
});
