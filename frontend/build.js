#!/usr/bin/env node
/**
 * Build script for Vercel deployment.
 * Injects API_URL into index.html (replaces empty string for same-origin API).
 */
const fs = require('fs');
const path = require('path');

const apiUrl = (process.env.API_URL || 'https://app-review-insights-analyser.onrender.com').replace(/\/$/, '');
const src = path.join(__dirname, 'public', 'index.html');
const out = path.join(__dirname, 'public', 'index.html');

let html = fs.readFileSync(src, 'utf8');
html = html.replace(/const API = ['"]?[^'"]*['"]?;/, `const API = ${JSON.stringify(apiUrl)};`);
fs.writeFileSync(out, html);
console.log('Built with API_URL:', apiUrl || '(same-origin)');
