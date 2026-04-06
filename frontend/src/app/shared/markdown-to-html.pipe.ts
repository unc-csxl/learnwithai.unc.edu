import { Pipe, PipeTransform } from '@angular/core';
import { marked } from 'marked';

/** Converts markdown text into sanitized HTML for Angular innerHTML bindings. */
@Pipe({
  name: 'markdownToHtml',
})
export class MarkdownToHtmlPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value?.trim()) {
      return '';
    }

    return marked.parse(value, {
      async: false,
      breaks: true,
      gfm: true,
    }) as string;
  }
}
