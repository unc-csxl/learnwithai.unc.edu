import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MatPane } from './mat-pane';

describe('MatPane', () => {
  let component: MatPane;
  let fixture: ComponentFixture<MatPane>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MatPane],
    }).compileComponents();

    fixture = TestBed.createComponent(MatPane);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
