// Simple CSV helpers: parse and trigger download

export function parseCSV(csvText) {
  if (!csvText || typeof csvText !== 'string') return [];
  const lines = csvText.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const header = lines[0].split(',').map(h => h.trim());
  return lines.slice(1).map(line => {
    const cells = line.split(',');
    const obj = {};
    header.forEach((key, idx) => {
      const raw = (cells[idx] || '').trim();
      // Attempt numeric conversion when appropriate
      const num = Number(raw);
      obj[key] = raw === '' ? null : (isFinite(num) ? num : raw);
    });
    return obj;
  });
}

export function downloadCSV(csvText, filename = 'employee_skill_diagrams.csv') {
  const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
