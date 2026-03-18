import { TestBed } from '@angular/core/testing';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark');
    TestBed.configureTestingModule({});
    service = TestBed.inject(ThemeService);
    TestBed.flushEffects();
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark');
  });

  it('should default to system mode', () => {
    expect(service.mode()).toBe('system');
  });

  it('should persist preference to localStorage', () => {
    service.mode.set('dark');
    TestBed.flushEffects();
    expect(localStorage.getItem('theme-mode')).toBe('dark');
  });

  it('should apply dark class when mode is dark', () => {
    service.mode.set('dark');
    TestBed.flushEffects();
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(service.isDark()).toBe(true);
  });

  it('should apply light class when mode is light', () => {
    service.mode.set('light');
    TestBed.flushEffects();
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(service.isDark()).toBe(false);
  });

  it('should remove classes when mode is system', () => {
    service.mode.set('dark');
    TestBed.flushEffects();
    service.mode.set('system');
    TestBed.flushEffects();
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.classList.contains('light')).toBe(false);
  });

  it('toggle should cycle system -> light -> dark -> system', () => {
    expect(service.mode()).toBe('system');
    service.toggle();
    expect(service.mode()).toBe('light');
    service.toggle();
    expect(service.mode()).toBe('dark');
    service.toggle();
    expect(service.mode()).toBe('system');
  });

  it('should load saved preference from localStorage', () => {
    localStorage.setItem('theme-mode', 'dark');
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({});
    const newService = TestBed.inject(ThemeService);
    expect(newService.mode()).toBe('dark');
  });

  it('should ignore invalid localStorage values', () => {
    localStorage.setItem('theme-mode', 'invalid');
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({});
    const newService = TestBed.inject(ThemeService);
    expect(newService.mode()).toBe('system');
  });

  it('should listen for system theme changes when matchMedia is available', () => {
    const listeners: Array<() => void> = [];
    const mockMql = {
      matches: false,
      addEventListener: (_event: string, cb: () => void) => listeners.push(cb),
    };
    Object.defineProperty(window, 'matchMedia', {
      value: vi.fn().mockReturnValue(mockMql),
      writable: true,
      configurable: true,
    });

    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark');
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({});
    const newService = TestBed.inject(ThemeService);
    TestBed.flushEffects();

    // isDark should reflect matchMedia when in system mode
    expect(newService.isDark()).toBe(false);

    // Simulate system dark mode change while in system mode
    mockMql.matches = true;
    listeners.forEach((cb) => cb());
    expect(newService.isDark()).toBe(true);

    // Switch to light mode — media query listener should be ignored
    newService.mode.set('light');
    TestBed.flushEffects();
    expect(newService.isDark()).toBe(false);
    mockMql.matches = false;
    listeners.forEach((cb) => cb());
    expect(newService.isDark()).toBe(false);

    // Switch back to system mode — isDark should read from matchMedia
    newService.mode.set('system');
    TestBed.flushEffects();
    expect(newService.isDark()).toBe(false);

    // Clean up
    Object.defineProperty(window, 'matchMedia', {
      value: undefined,
      writable: true,
      configurable: true,
    });
  });
});
