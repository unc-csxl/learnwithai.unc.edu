import { MarkdownToHtmlPipe } from './markdown-to-html.pipe';

describe('MarkdownToHtmlPipe', () => {
  let pipe: MarkdownToHtmlPipe;

  beforeEach(() => {
    pipe = new MarkdownToHtmlPipe();
  });

  it('should return an empty string for blank values', () => {
    expect(pipe.transform('')).toBe('');
    expect(pipe.transform('   ')).toBe('');
    expect(pipe.transform(null)).toBe('');
    expect(pipe.transform(undefined)).toBe('');
  });

  it('should render markdown formatting to html', () => {
    const html = pipe.transform('**Bold** text\n\n- one\n- two');

    expect(html).toContain('<strong>Bold</strong>');
    expect(html).toContain('<ul>');
    expect(html).toContain('<li>one</li>');
    expect(html).toContain('<li>two</li>');
  });

  it('should preserve single-line markdown breaks', () => {
    const html = pipe.transform('First line\nSecond line');

    expect(html).toContain('First line<br>Second line');
  });
});
