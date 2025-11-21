function normaliseBase(url) {
  return url.replace(/\/?$/, '');
}

function resolveBaseUrls() {
  const configured = normaliseBase(process.env.VITE_API_BASE_URL ?? 'http://localhost:3000');
  const candidates = [configured];

  if (configured.includes('localhost')) {
    candidates.push(normaliseBase(configured.replace('localhost', 'backend')));
  }

  return [...new Set(candidates)];
}

async function fetchJson(baseUrl, path) {
  const response = await fetch(`${baseUrl}${path}`);
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with ${response.status}: ${text}`);
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`Invalid JSON response from ${path}: ${error.message}`);
  }
}

function summariseMatches(payload) {
  const rows = Array.isArray(payload?.data) ? payload.data : [];
  return rows.slice(0, 3).map((row) => ({
    job_id: row.job_id,
    emp_id: row.emp_id,
    match_mark: row.match_mark,
    match_score: row.match_score,
  }));
}

function summariseTrainingPlans(payload) {
  const rows = Array.isArray(payload?.data) ? payload.data : [];
  return rows.slice(0, 3).map((row) => ({
    job_id: row.job_id,
    emp_id: row.emp_id,
    missing: row.skill_miss,
  }));
}

async function runChecks(baseUrl) {
  console.log(`Checking Talent Matching API at ${baseUrl}`);
  const health = await fetchJson(baseUrl, '/api/health');
  console.log('Health:', health);

  const matches = await fetchJson(baseUrl, '/api/job-matches?limit=5');
  console.log('Sample matches:', summariseMatches(matches));

  const plans = await fetchJson(baseUrl, '/api/training-plans?limit=5');
  console.log('Sample training plans:', summariseTrainingPlans(plans));
}

async function main() {
  const candidates = resolveBaseUrls();
  let lastError = null;

  for (const baseUrl of candidates) {
    try {
      await runChecks(baseUrl);
      return;
    } catch (error) {
      console.warn(`Attempt with base ${baseUrl} failed: ${error.message}`);
      lastError = error;
    }
  }

  if (lastError) {
    throw lastError;
  }
}

main().catch((error) => {
  console.error('API check failed:', error.message);
  process.exitCode = 1;
});
