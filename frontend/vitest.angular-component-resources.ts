/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, extname, join, relative, resolve } from 'node:path';

type CompiledOutputFile = {
  path: string;
  text: string;
};

type EsbuildBuildResult = {
  outputFiles?: CompiledOutputFile[];
};

type EsbuildModule = {
  build(options: Record<string, unknown>): Promise<EsbuildBuildResult>;
};

type SassModule = {
  compile(file: string, options?: { loadPaths?: string[] }): { css: string };
};

type VitestTransformPlugin = {
  name: string;
  enforce: 'pre';
  buildStart(): void;
  transform(code: string, id: string): Promise<{ code: string; map: null } | null>;
  resolveId(source: string, importer?: string): string | null;
  load(id: string): Promise<string | null>;
};

const require = createRequire(import.meta.url);
const angularBuildRequire = createRequire(require.resolve('@angular/build/package.json'));
const esbuild = angularBuildRequire('esbuild') as EsbuildModule;
const { createCompilerPlugin }: typeof import('@angular/build/private') =
  angularBuildRequire('@angular/build/private');

const JIT_URI_REGEXP = /^angular:jit:(template|style):(file|inline);(.*)$/;
const JIT_VIRTUAL_PREFIX = '\0learnwithai:angular-jit:';
const COMPILATION_CACHE_DIR = '.angular/cache/vitest-explorer';

let sassModulePromise: Promise<SassModule | null> | undefined;

export function angularComponentResourcesPlugin(
  workspaceRoot = process.cwd(),
): VitestTransformPlugin {
  const compiledModules = new Map<string, { source: string; compiled: string }>();

  return {
    name: 'learnwithai:angular-component-resources',
    enforce: 'pre',
    buildStart() {
      compiledModules.clear();
    },
    async transform(code: string, id: string) {
      if (!shouldCompile(id, workspaceRoot)) {
        return null;
      }

      const cached = compiledModules.get(id);
      if (cached && cached.source === code) {
        return { code: cached.compiled, map: null };
      }

      const compiled = await compileAngularModule(id, workspaceRoot);
      compiledModules.set(id, { source: code, compiled });

      return {
        code: compiled,
        map: null,
      };
    },
    resolveId(source: string, importer?: string) {
      const parsed = parseJitUri(source);
      if (!parsed) {
        return null;
      }

      if (parsed.origin === 'file') {
        if (!importer) {
          return null;
        }

        return `${JIT_VIRTUAL_PREFIX}${parsed.type}:${parsed.origin}:${resolve(dirname(importer), parsed.specifier)}`;
      }

      return `${JIT_VIRTUAL_PREFIX}${parsed.type}:${parsed.origin}:${parsed.specifier}`;
    },
    async load(id: string) {
      const parsed = parseVirtualJitId(id);
      if (!parsed) {
        return null;
      }

      const contents =
        parsed.origin === 'inline'
          ? Buffer.from(parsed.specifier, 'base64').toString('utf-8')
          : await loadResourceContents(parsed.specifier, parsed.type, workspaceRoot);

      return `export default ${JSON.stringify(contents)};`;
    },
  };
}

async function compileAngularModule(id: string, workspaceRoot: string): Promise<string> {
  const result = await esbuild.build({
    entryPoints: [id],
    bundle: false,
    write: false,
    format: 'esm',
    platform: 'browser',
    absWorkingDir: workspaceRoot,
    outdir: join(workspaceRoot, COMPILATION_CACHE_DIR),
    plugins: [
      createCompilerPlugin(
        {
          sourcemap: false,
          tsconfig: join(workspaceRoot, 'tsconfig.spec.json'),
          jit: true,
          includeTestMetadata: true,
          incremental: false,
        },
        {
          workspaceRoot,
          optimization: false,
          inlineFonts: false,
          sourcemap: false,
          outputNames: {
            bundles: '[name]',
            media: 'media/[name]',
          },
          target: ['es2022'],
          cacheOptions: {
            enabled: false,
            path: join(workspaceRoot, COMPILATION_CACHE_DIR),
            basePath: join(workspaceRoot, '.angular/cache'),
          },
          inlineStyleLanguage: 'scss',
        },
      ),
    ],
  });

  const compiledFile = result.outputFiles?.find((file: CompiledOutputFile) =>
    file.path.endsWith('.js'),
  );
  if (!compiledFile) {
    throw new Error(
      `Angular compilation did not emit JavaScript for ${relative(workspaceRoot, id)}.`,
    );
  }

  return compiledFile.text;
}

async function loadResourceContents(
  specifier: string,
  type: 'template' | 'style',
  workspaceRoot: string,
): Promise<string> {
  if (type === 'template') {
    return readFile(specifier, 'utf-8');
  }

  if (extname(specifier) === '.scss' || extname(specifier) === '.sass') {
    const sass = await loadSassModule();
    if (sass) {
      return sass.compile(specifier, { loadPaths: [workspaceRoot, dirname(specifier)] }).css;
    }
  }

  return readFile(specifier, 'utf-8');
}

function shouldCompile(id: string, workspaceRoot: string): boolean {
  return (
    id.startsWith(join(workspaceRoot, 'src/app')) &&
    id.endsWith('.ts') &&
    !id.endsWith('.spec.ts') &&
    !id.includes('/node_modules/') &&
    !id.includes('/.angular/')
  );
}

function parseJitUri(
  specifier: string,
): { type: 'template' | 'style'; origin: 'file' | 'inline'; specifier: string } | undefined {
  const matches = JIT_URI_REGEXP.exec(specifier);
  if (!matches) {
    return undefined;
  }

  return {
    type: matches[1] as 'template' | 'style',
    origin: matches[2] as 'file' | 'inline',
    specifier: matches[3],
  };
}

function parseVirtualJitId(
  id: string,
): { type: 'template' | 'style'; origin: 'file' | 'inline'; specifier: string } | undefined {
  if (!id.startsWith(JIT_VIRTUAL_PREFIX)) {
    return undefined;
  }

  const [type, origin, ...specifierParts] = id.slice(JIT_VIRTUAL_PREFIX.length).split(':');
  if (!type || !origin || specifierParts.length === 0) {
    return undefined;
  }

  return {
    type: type as 'template' | 'style',
    origin: origin as 'file' | 'inline',
    specifier: specifierParts.join(':'),
  };
}

async function loadSassModule(): Promise<SassModule | null> {
  sassModulePromise ??= (async () => {
    try {
      return angularBuildRequire('sass') as SassModule;
    } catch {
      return null;
    }
  })();

  return sassModulePromise;
}
