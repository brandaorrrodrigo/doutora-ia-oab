const fs = require('fs');

let content = fs.readFileSync('docker-compose.yml', 'utf8');

// Fix 1: Change Redis port from 6379 to 6381
content = content.replace(/ports:\s*\n\s*- "6379:6379"/, 'ports:\n      - "6381:6379"');

// Fix 2: Remove Ollama healthcheck
const lines = content.split('\n');
const newLines = [];
let inOllamaHealthcheck = false;
let healthcheckIndent = 0;

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    const indent = line.search(/\S/);
    
    if (trimmed.startsWith('healthcheck:') && i > 40 && i < 80) {
        inOllamaHealthcheck = true;
        healthcheckIndent = indent;
        continue;
    }
    
    if (inOllamaHealthcheck) {
        if (indent <= healthcheckIndent && trimmed.length > 0 && !trimmed.startsWith('#')) {
            inOllamaHealthcheck = false;
            newLines.push(line);
        }
        continue;
    }
    
    newLines.push(line);
}

fs.writeFileSync('docker-compose.yml', newLines.join('\n'));
console.log('✓ Fixed!');
