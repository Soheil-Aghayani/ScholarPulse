import { copyFile, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const nativeBuild = args.includes('--native');
const outputIndex = args.indexOf('--out');
const outputName = outputIndex >= 0 ? args[outputIndex + 1] : 'site-dist';
const outputDir = path.resolve(projectRoot, outputName || 'site-dist');
const defaultBackend = 'https://scholarpulse-hfew.onrender.com';
const staticFiles = [
  'index.html',
  'manifest.json',
  'sw.js',
  'icon.svg',
  'icon-192.png',
  'icon-512.png'
];

if (outputDir === projectRoot) {
  throw new Error('Refusing to use the repository root as the build output.');
}

await rm(outputDir, { recursive: true, force: true });
await mkdir(outputDir, { recursive: true });

for (const relativePath of staticFiles) {
  const source = path.join(projectRoot, relativePath);
  const target = path.join(outputDir, relativePath);
  await copyFile(source, target);
}

if (nativeBuild) {
  const backend = String(process.env.SCHOLARPULSE_API_BASE || defaultBackend).trim().replace(/\/+$/, '');
  const indexPath = path.join(outputDir, 'index.html');
  const indexHtml = await readFile(indexPath, 'utf8');
  const bootstrap = `  <script>window.SCHOLARPULSE_NATIVE = true; window.SCHOLARPULSE_API_BASE = ${JSON.stringify(backend)};</script>\n`;
  await writeFile(indexPath, indexHtml.replace(/<head>/i, `<head>\n${bootstrap}`), 'utf8');
}

console.log(`Built ${nativeBuild ? 'native' : 'web'} app assets in ${path.relative(projectRoot, outputDir)}`);
