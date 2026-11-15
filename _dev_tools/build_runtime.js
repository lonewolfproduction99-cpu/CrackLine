// Builds the GDJS runtime (TS -> JS) with esbuild, mirroring GDJS/scripts/build.js.
const { buildSync } = require('/opt/npm-tools/node_modules/esbuild');
const fs = require('fs'), path = require('path');
const root = '/tmp/gd', out = '/tmp/gdjsroot/Runtime';
const untransformed = ['GDJS/Runtime/pixi-renderers/pixi.js','GDJS/Runtime/pixi-renderers/three.js','GDJS/Runtime/pixi-renderers/ThreeAddons.js','GDJS/Runtime/pixi-renderers/draco','GDJS/Runtime/fontfaceobserver-font-manager/fontfaceobserver.js','GDJS/Runtime/Cordova','GDJS/Runtime/Electron','GDJS/Runtime/FacebookInstantGames','GDJS/Runtime/libs/CocoonJS','GDJS/Runtime/libs/rbush.js'].map(p => path.join(root, p));
const allowed = ['.js','.ts','.tsx','.html','.json','.xml','.wasm','.txt','.png','.svg'];
function walk(d, cb) { for (const f of fs.readdirSync(d)) { const p = path.join(d, f); const st = fs.statSync(p); if (st.isDirectory()) { if (!/node_modules|__tests__|tests$/.test(p)) walk(p, cb); } else cb(p); } }
let n = 0, err = 0;
function handle(inPath, outPath) {
  const ext = path.extname(inPath);
  if (!allowed.includes(ext) || inPath.endsWith('.d.ts') || inPath.endsWith('.spec.js') || inPath.endsWith('JsExtension.js')) return;
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  const untrans = untransformed.some(u => inPath.startsWith(u)) || inPath.endsWith('.min.js') || !['.js','.ts','.tsx'].includes(ext);
  if (untrans) { fs.copyFileSync(inPath, outPath); return; }
  try { buildSync({ entryPoints: [inPath], outfile: outPath.replace(/\.tsx?$/, '.js'), minify: false, sourcemap: false, logLevel: 'error' }); n++; }
  catch (e) { err++; console.error('ERR', inPath); }
}
walk(path.join(root, 'GDJS/Runtime'), p => handle(p, path.join(out, path.relative(path.join(root, 'GDJS/Runtime'), p))));
for (const ext of ['TextObject', 'TiledSpriteObject']) walk(path.join(root, 'Extensions', ext), p => handle(p, path.join(out, path.relative(root, p))));
console.log('built', n, 'errors', err);
