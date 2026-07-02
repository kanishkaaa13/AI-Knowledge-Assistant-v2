const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, 'components', 'chat');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.tsx'));

const replacements = [
  { regex: /bg-\[\#080808\]/g, replacement: 'bg-[var(--bg-primary)]' },
  { regex: /bg-\[\#0f0f0f\]/g, replacement: 'bg-[var(--bg-secondary)]' },
  { regex: /bg-\[\#111111\]/g, replacement: 'bg-[var(--bg-panel)]' },
  { regex: /bg-\[\#1a1a1a\]/g, replacement: 'bg-[var(--assistant-bubble)]' },
  { regex: /border-\[\#1f1f1f\]/g, replacement: 'border-[var(--border-color)]' },
  { regex: /border-\[\#2a2a2a\]/g, replacement: 'border-[var(--border-color)]' },
  { regex: /border-\[\#2d2d2d\]/g, replacement: 'border-[var(--border-color)]' },
  { regex: /text-\[\#f1f1f1\]/g, replacement: 'text-[var(--text-primary)]' },
  { regex: /text-\[\#6b7280\]/g, replacement: 'text-[var(--text-secondary)]' },
  { regex: /text-\[\#4b5563\]/g, replacement: 'text-[var(--text-secondary)]' },
  { regex: /bg-\[\#2a2a2a\]/g, replacement: 'bg-[var(--border-color)]' },
];

files.forEach(file => {
  const filePath = path.join(dir, file);
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;
  
  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });
  
  if (original !== content) {
    fs.writeFileSync(filePath, content);
    console.log(`Updated ${file}`);
  }
});
