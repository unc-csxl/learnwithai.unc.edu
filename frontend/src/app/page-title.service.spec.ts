import { TestBed } from '@angular/core/testing';
import { PageTitleService } from './page-title.service';

describe('PageTitleService', () => {
  let service: PageTitleService;

  beforeEach(() => {
    service = TestBed.inject(PageTitleService);
  });

  it('should start with an empty title', () => {
    expect(service.title()).toBe('');
  });

  it('should update the title signal', () => {
    service.setTitle('My Courses');
    expect(service.title()).toBe('My Courses');
  });

  it('should update document.title with suffix', () => {
    service.setTitle('My Courses');
    expect(document.title).toBe('My Courses – Learn with AI');
  });

  it('should use base title when page title is empty', () => {
    service.setTitle('');
    expect(document.title).toBe('Learn with AI');
  });
});
