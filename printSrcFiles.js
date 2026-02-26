const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

function printAllFiles(dir, prefix = '') {
  try {
    const items = fs.readdirSync(dir);

    items.forEach((item, index) => {
      const fullPath = path.join(dir, item);
      const isLast = index === items.length - 1;
      const pointer = isLast ? '└── ' : '├── ';

      const stats = fs.statSync(fullPath);
      if (stats.isDirectory()) {
        console.log(prefix + pointer + item + '/');
        printAllFiles(fullPath, prefix + (isLast ? '    ' : '│   '));
      } else {
        console.log(prefix + pointer + item);
      }
    });
  } catch (err) {
    console.error('Error reading folder:', dir, err);
  }
}

if (!fs.existsSync(srcDir)) {
  console.error('❌ src folder not found at:', srcDir);
} else {
  console.log('📂 Project structure for src:');
  printAllFiles(srcDir);
}
