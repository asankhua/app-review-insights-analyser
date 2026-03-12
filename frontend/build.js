#!/usr/bin/env node
/**
 * Build script for Vercel deployment.
 * Injects API_URL into index.html and outputs to dist/ at repo root.
 */
const fs = require('fs');
const path = require('path');

const apiUrl = (process.env.API_URL || 'https://app-review-insights-analyser-production.up.railway.app').replace(/\/$/, '');
const src = path.join(__dirname, 'public', 'index.html');
const outDir = path.join(__dirname, 'dist');
const outFile = path.join(outDir, 'index.html');

let html = fs.readFileSync(src, 'utf8');
html = html.replace(/const API = ['"]?[^'"]*['"]?;/, `const API = ${JSON.stringify(apiUrl)};`);
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(outFile, html);
console.log('Built with API_URL:', apiUrl || '(same-origin)');
