import Papa from 'papaparse'

// Parse the top_skills_tfidf cell string into an array of [skill, weight]
export function parseTopSkills(cell, max = 10) {
  if (!cell) return []
  try {
    // Remove starting/ending brackets if present
    const trimmed = cell.trim()
    if (!trimmed.startsWith('[')) return []
    // Use Function-safe parsing: replace parentheses with JSON-like brackets
    // Example: [("ai", 0.48), ("cloud", 0.28)] -> [["ai", 0.48], ["cloud", 0.28]]
    const jsonLike = trimmed
      .replace(/\(/g, '[')
      .replace(/\)/g, ']')
    // Wrap single quotes to double quotes for JSON parsing
    const normalized = jsonLike.replace(/'([^']+)'/g, '"$1"')
    const arr = JSON.parse(normalized)
    return Array.isArray(arr) ? arr.slice(0, max).filter(t => Array.isArray(t) && typeof t[0] === 'string').map(t => [t[0], Number(t[1])]) : []
  } catch (e) {
    return []
  }
}

export async function loadEmployeeSkillPositions(csvUrl) {
  return new Promise((resolve, reject) => {
    Papa.parse(csvUrl, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: results => {
        const rows = results.data.map(r => ({
          employee_id: r.employee_id?.toString() || '',
          skill_sentence: r.skill || '',
          x: Number(r.x),
            y: Number(r.y),
          cluster_kmeans: r.cluster_kmeans?.toString() || 'unknown',
          top_skills_raw: r.top_skills_tfidf || '',
          top_skills: parseTopSkills(r.top_skills_tfidf, 10)
        }))
        resolve(rows)
      },
      error: err => reject(err)
    })
  })
}
