#!/usr/bin/env node
/**
 * Build script for Vercel deployment.
 * Injects API_URL into index.html (replaces empty string for same-origin API).
 */
const fs = require('fs');
const path = require('path');

// API_URL: empty = same-origin (proxy). Non-empty = direct Render URL. Default direct for reliability.
const apiUrl = (process.env.API_URL || 'https://app-review-insights-analyser.onrender.com').replace(/\/$/, '');
const src = path.join(__dirname, 'public', 'index.html');
const out = path.join(__dirname, 'public', 'index.html');

let html = fs.readFileSync(src, 'utf8');
// Match full API assignment (simple or ternary) and replace with backend URL for Vercel
html = html.replace(/const API = [^;]+;/, `const API = ${JSON.stringify(apiUrl)};`);
fs.writeFileSync(out, html);
console.log('Built with API_URL:', apiUrl || '(same-origin)');
