import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const STAGES = {
  login: 'login',
  hrDashboard: 'hr-dashboard',
  employeeDashboard: 'employee-dashboard'
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000').replace(/\/$/, '');

const parseSkills = (raw) => {
  if (!raw || typeof raw !== 'string') return [];
  return raw
    .replace(/,/g, ';')
    .split(';')
    .map((skill) => skill.trim())
    .filter((skill) => Boolean(skill) && skill !== '-')
    .map((skill) => skill.replace(/\s+/g, ' '));
};

const toJobsMap = (jobs = []) => jobs.reduce((acc, job) => {
  acc[job.job_id] = job;
  return acc;
}, {});

function App() {
  const [stage, setStage] = useState(STAGES.login);
  const [role, setRole] = useState('HR');
  const [password, setPassword] = useState('');
  const passwordRef = useRef(null);
  const [employees, setEmployees] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [employeeMatches, setEmployeeMatches] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [bootstrapDone, setBootstrapDone] = useState(false);
  const [lookingForOpportunities, setLookingForOpportunities] = useState(false);
  const [lookingReason, setLookingReason] = useState('');
  const [trainingPlan, setTrainingPlan] = useState(null);
  const [trainingPlanLoading, setTrainingPlanLoading] = useState(false);
  const [trainingPlanError, setTrainingPlanError] = useState('');
  const [hrSelectedJobId, setHrSelectedJobId] = useState('');
  const [hrJobMatches, setHrJobMatches] = useState([]);
  const [hrLoadingMatches, setHrLoadingMatches] = useState(false);
  const [hrTrainingPlans, setHrTrainingPlans] = useState({});
  const [hrError, setHrError] = useState('');
  const [learningHours, setLearningHours] = useState(5);

  const apiRequest = useCallback(async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, options);
    const isJson = response.headers.get('content-type')?.includes('application/json');
    let payload = null;

    if (isJson) {
      try {
        payload = await response.json();
      } catch (jsonErr) {
        console.warn('Failed to parse JSON response', jsonErr);
      }
    }

    if (!response.ok) {
      throw new Error(payload?.detail || payload?.error || `Request failed (${response.status})`);
    }

    return payload ?? {};
  }, []);

  const loadEmployees = useCallback(async () => {
    const data = await apiRequest('/employees');
    setEmployees(Array.isArray(data) ? data : []);
  }, [apiRequest]);

  const loadJobs = useCallback(async () => {
    const data = await apiRequest('/jobs');
    setJobs(Array.isArray(data) ? data : []);
  }, [apiRequest]);

  const loadMatchesForEmployee = useCallback(async (empId) => {
    if (!empId) {
      setEmployeeMatches([]);
      return;
    }
    setLoadingMatches(true);
    try {
      const data = await apiRequest(`/api/job-matches?emp_id=${encodeURIComponent(empId)}`);
      setEmployeeMatches(data?.data ?? []);
    } catch (err) {
      console.error(err);
      setLoginError('Could not load matches for this employee.');
      setEmployeeMatches([]);
    } finally {
      setLoadingMatches(false);
    }
  }, [apiRequest]);

  useEffect(() => {
    const bootstrap = async () => {
      setLoadError('');
      try {
        await Promise.all([loadEmployees(), loadJobs()]);
      } catch (err) {
        setLoadError(err.message || 'Failed to load initial data');
      } finally {
        setBootstrapDone(true);
      }
    };
    bootstrap();
  }, [loadEmployees, loadJobs]);

  useEffect(() => {
    setSelectedJobId(null);
    setLoginError('');
    loadMatchesForEmployee(selectedEmployeeId);
  }, [selectedEmployeeId, loadMatchesForEmployee]);

  useEffect(() => {
    const emp = employees.find((item) => item.emp_id === selectedEmployeeId);
    if (emp && Number.isFinite(Number(emp.learning_hours_per_week))) {
      setLearningHours(Math.max(1, Number(emp.learning_hours_per_week)));
    } else {
      setLearningHours(5);
    }
  }, [selectedEmployeeId, employees]);

  useEffect(() => {
    if (jobs.length && !hrSelectedJobId) {
      setHrSelectedJobId(jobs[0].job_id);
    }
  }, [jobs, hrSelectedJobId]);

  useEffect(() => {
    const loadHrMatches = async () => {
      if (!hrSelectedJobId) {
        setHrJobMatches([]);
        return;
      }
      setHrLoadingMatches(true);
      setHrError('');
      try {
        const data = await apiRequest(`/api/job-matches?job_id=${encodeURIComponent(hrSelectedJobId)}`);
        const matches = (data?.data ?? []).slice(0, 10);
        setHrJobMatches(matches);
        const plans = {};
        await Promise.all(matches.map(async (row) => {
          try {
            const plan = await apiRequest(`/training_plan/${row.job_id}/${row.emp_id}`);
            plans[`${row.job_id}-${row.emp_id}`] = plan;
          } catch (err) {
            plans[`${row.job_id}-${row.emp_id}`] = null;
          }
        }));
        setHrTrainingPlans(plans);
      } catch (err) {
        setHrJobMatches([]);
        setHrError(err.message || 'Unable to load job matches');
      } finally {
        setHrLoadingMatches(false);
      }
    };
    loadHrMatches();
  }, [hrSelectedJobId, apiRequest]);

  useEffect(() => {
    if (employeeMatches.length === 0) {
      setSelectedJobId(null);
      return;
    }
    setSelectedJobId(employeeMatches[0].job_id);
  }, [employeeMatches]);

  const jobsById = useMemo(() => toJobsMap(jobs), [jobs]);

  const activeEmployee = useMemo(
    () => employees.find((emp) => emp.emp_id === selectedEmployeeId) ?? null,
    [employees, selectedEmployeeId]
  );

  const userProfile = useMemo(() => {
    if (!activeEmployee) {
      return { id: '', name: 'Pick an employee', role: role === 'HR' ? 'HR' : 'Employee', location: '-', skills: [] };
    }
    return {
      id: activeEmployee.emp_id,
      name: activeEmployee.emp_id,
      role: activeEmployee.emp_position || 'Employee',
      location: '-',
      skills: parseSkills(activeEmployee.emp_skills),
      desiredJob: activeEmployee.emp_desired_job
    };
  }, [activeEmployee, role]);

  const selectedMatch = useMemo(
    () => employeeMatches.find((match) => match.job_id === selectedJobId) ?? employeeMatches[0] ?? null,
    [employeeMatches, selectedJobId]
  );

  const missingSkills = useMemo(() => (selectedMatch ? parseSkills(selectedMatch.skill_miss) : []), [selectedMatch]);
  const matchedSkills = useMemo(() => (selectedMatch ? parseSkills(selectedMatch.skill_match) : []), [selectedMatch]);

  useEffect(() => {
    if (!selectedMatch) {
      setTrainingPlan(null);
      return;
    }
    const loadPlan = async () => {
      setTrainingPlanLoading(true);
      setTrainingPlanError('');
      try {
        const data = await apiRequest(`/training_plan/${selectedMatch.job_id}/${selectedMatch.emp_id}`);
        setTrainingPlan(data || null);
      } catch (err) {
        setTrainingPlan(null);
        setTrainingPlanError(err.message || 'Unable to load training plan');
      } finally {
        setTrainingPlanLoading(false);
      }
    };
    loadPlan();
  }, [selectedMatch, apiRequest]);

  const startLogin = (event) => {
    if (event) event.preventDefault();
    setLoginError('');
    if (role === 'Employee' && !selectedEmployeeId) {
      setLoginError('Select an employee to enter as Employee.');
      return;
    }
    if (role === 'HR') {
      setStage(STAGES.hrDashboard);
    } else {
      setStage(STAGES.employeeDashboard);
    }
  };

  const logout = () => {
    setStage(STAGES.login);
    setSelectedJobId(null);
    setRole('HR');
    setSelectedEmployeeId('');
    setPassword('');
    setEmployeeMatches([]);
    setLookingForOpportunities(false);
    setLookingReason('');
    setHrSelectedJobId('');
    setHrJobMatches([]);
    setHrTrainingPlans({});
    setHrError('');
  };

  const goHome = () => {
    setStage(role === 'HR' ? STAGES.hrDashboard : STAGES.employeeDashboard);
  };

  return (
    <div className="app">
      <div className="app__bg app__bg--one" />
      <div className="app__bg app__bg--two" />

      {stage === STAGES.login && (
      <Login
        role={role}
        setRole={setRole}
        employeeId={selectedEmployeeId}
        setEmployeeId={setSelectedEmployeeId}
          password={password}
          setPassword={setPassword}
          onSubmit={startLogin}
          passwordRef={passwordRef}
          employees={employees}
          matches={employeeMatches}
          matchesLoading={loadingMatches}
          error={loginError || loadError}
          bootstrapDone={bootstrapDone}
        />
      )}

      {stage !== STAGES.login && (
        <div className="layout">
          <Header
            stage={stage}
            role={role}
            onNavigateHome={goHome}
            onLogout={logout}
          />

          {stage === STAGES.hrDashboard && (
            <HrDashboard
              jobs={jobs}
              selectedJobId={hrSelectedJobId}
              setSelectedJobId={setHrSelectedJobId}
              jobMatches={hrJobMatches}
              loadingMatches={hrLoadingMatches}
              trainingPlans={hrTrainingPlans}
              error={hrError}
            />
          )}
          {stage === STAGES.employeeDashboard && (
            <EmployeeDashboard
              userProfile={userProfile}
              matches={employeeMatches}
              selectedJobId={selectedJobId}
              setSelectedJobId={setSelectedJobId}
              missingSkills={missingSkills}
              matchedSkills={matchedSkills}
              jobsById={jobsById}
              selectedMatch={selectedMatch}
              lookingForOpportunities={lookingForOpportunities}
              setLookingForOpportunities={setLookingForOpportunities}
          lookingReason={lookingReason}
          setLookingReason={setLookingReason}
          trainingPlan={trainingPlan}
          trainingPlanLoading={trainingPlanLoading}
          trainingPlanError={trainingPlanError}
        />
      )}
        </div>
      )}
    </div>
  );
}

function Header({ stage, role, onNavigateHome, onLogout }) {
  const subtitle = stage === STAGES.hrDashboard ? '' : 'Your growth and job opportunities';
  const title = stage === STAGES.hrDashboard ? 'HR Dashboard' : 'Employee Space';
  return (
    <header className="header">
      <div>
        <p className="header__kicker">Internal Job Management</p>
        <h1 className="header__title">{title}</h1>
        {subtitle && <p className="header__subtitle">{subtitle}</p>}
      </div>
      <nav className="header__actions">
        <button type="button" className="button button--ghost" onClick={onNavigateHome}>
          {role === 'HR' ? 'HR dashboard' : 'Employee dashboard'}
        </button>
        <button type="button" className="button button--danger" onClick={onLogout}>
          Logout
        </button>
      </nav>
    </header>
  );
}

function Login({
  role,
  setRole,
  employeeId,
  setEmployeeId,
  password,
  setPassword,
  onSubmit,
  passwordRef,
  employees,
  matches,
  matchesLoading,
  error,
  bootstrapDone
}) {
  const hasEmployees = bootstrapDone && employees.length > 0;
  const dataListId = 'employee-suggestions';
  return (
    <div className="login">
      <form className="card login__card" onSubmit={onSubmit}>
        <h2 className="login__title">Authentication</h2>
        <label className="form-label" htmlFor="employeeId">Employee (emp_id)</label>
        <input
          id="employeeId"
          className="input"
          placeholder="Type an emp_id (e.g. E0001)"
          value={employeeId}
          onChange={(event) => setEmployeeId(event.target.value)}
          list={dataListId}
          disabled={!hasEmployees}
        />
        {hasEmployees && (
          <datalist id={dataListId}>
            {employees.map((emp) => (
              <option key={emp.emp_id} value={emp.emp_id}>{emp.emp_position || 'No role'}</option>
            ))}
          </datalist>
        )}

        <label className="form-label" htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          className="input"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          ref={passwordRef}
        />

        <div className="role-toggle" role="group" aria-label="Select role">
          {['HR', 'Employee'].map((item) => {
            const isActive = role === item;
            return (
              <button
                key={item}
                type="button"
                className={`role-toggle__btn${isActive ? ' role-toggle__btn--active' : ''}`}
                onClick={() => setRole(item)}
              >
                {item}
              </button>
            );
          })}
        </div>

        {error && <p className="data-sync__error">{error}</p>}
        <button type="submit" className="button button--primary login__submit">Login</button>
      </form>

      <EmployeeSkillPreview matches={matches} loading={matchesLoading} />
    </div>
  );
}

function EmployeeSkillPreview({ matches, loading }) {
  if (loading) {
    return (
      <div className="card login__card">
        <p className="card__subtitle">Loading matches...</p>
      </div>
    );
  }

  if (!matches || matches.length === 0) {
    return (
      <div className="card login__card">
        <p className="card__subtitle">Select an employee to preview their skills.</p>
      </div>
    );
  }

  const top = matches[0];
  const matched = parseSkills(top.skill_match);
  const missing = parseSkills(top.skill_miss);

  return (
    <div className="card login__card">
      <h3 className="card__title">Preview skills (from skill_match / skill_miss)</h3>
      <p className="card__subtitle">
        {top.job_title || `Job ${top.job_id}`} - score {top.match_score?.toFixed?.(2) ?? top.match_score}
      </p>
      <div className="chip-row chip-row--wrap">
        {matched.length === 0 && <span className="chip chip--muted">No matching skills yet</span>}
        {matched.map((skill) => (
          <span key={`m-${skill}`} className="chip chip--have">{skill}</span>
        ))}
      </div>
      <div className="chip-row chip-row--wrap">
        {missing.length === 0 && <span className="chip chip--have">Everything covered for this role</span>}
        {missing.map((skill) => (
          <span key={`x-${skill}`} className="chip chip--need">{skill}</span>
        ))}
      </div>
    </div>
  );
}

function HrDashboard({ jobs, selectedJobId, setSelectedJobId, jobMatches, loadingMatches, trainingPlans, error }) {
  const empty = !jobs || jobs.length === 0;
  const selectedJob = jobs.find((job) => job.job_id === selectedJobId) || jobs[0] || null;

  return (
    <section className="section">
      <div className="card">
        <div className="section__title-row">
          <div>
            <h2 className="card__title">Available jobs</h2>
            <p className="card__subtitle">Review openings and top matching employees.</p>
          </div>
          <span className="pill">{jobs.length} jobs</span>
        </div>

        {empty && <p className="data-sync__empty">No jobs available.</p>}

        {!empty && (
          <div className="opportunities__layout hr-layout">
            <div className="opportunities__list">
              {jobs.map((job) => {
                const required = parseSkills(job.job_required_skills || '');
                const active = selectedJobId === job.job_id;
                return (
                  <article
                    key={job.job_id}
                    className={`job-card job-card--compact${active ? ' job-card--selected' : ''}`}
                    onClick={() => setSelectedJobId(job.job_id)}
                  >
                    <header className="job-card__header">
                      <div>
                        <h3 className="job-card__title">{job.job_title}</h3>
                        <p className="job-card__company">{job.job_id}</p>
                      </div>
                      <div className="job-card__meta">
                        <span>{required.length} required skills</span>
                        <span className="job-card__salary">Education: {job.job_required_education || '-'}</span>
                      </div>
                    </header>
                    <div className="chip-row chip-row--wrap">
                      {required.map((skill) => (
                        <span key={skill} className="chip chip--have">{skill}</span>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>

            <HrMatchPanel
              job={selectedJob}
              matches={jobMatches}
              loading={loadingMatches}
              trainingPlans={trainingPlans}
              error={error}
            />
          </div>
        )}
      </div>
    </section>
  );
}

function EmployeeDashboard({
  userProfile,
  matches,
  selectedJobId,
  setSelectedJobId,
  missingSkills,
  matchedSkills,
  jobsById,
  selectedMatch,
  lookingForOpportunities,
  setLookingForOpportunities,
  lookingReason,
  setLookingReason,
  trainingPlan,
  trainingPlanLoading,
  trainingPlanError,
  learningHours,
  setLearningHours
}) {
  return (
    <section className="section">
      <ProfileCard userProfile={userProfile} matchedSkills={matchedSkills} missingSkills={missingSkills} />
      <DreamJobSummary missingSkills={missingSkills} />
      <OpportunityToggle
        active={lookingForOpportunities}
        onToggle={() => setLookingForOpportunities((prev) => !prev)}
        reason={lookingReason}
        onChooseReason={setLookingReason}
      />
      <div className="opportunities__layout">
        <Opportunities
          matches={matches}
          jobsById={jobsById}
          selectedJobId={selectedJobId}
          setSelectedJobId={setSelectedJobId}
        />
        <LearningPanel
          selectedMatch={selectedMatch}
          jobsById={jobsById}
          missingSkills={missingSkills}
          matchedSkills={matchedSkills}
          trainingPlan={trainingPlan}
          trainingPlanLoading={trainingPlanLoading}
          trainingPlanError={trainingPlanError}
          learningHours={learningHours}
          setLearningHours={setLearningHours}
        />
      </div>
      <DreamJobPath />
    </section>
  );
}

function PathToDreamJob({ missingSkills, jobTitle }) {
  const steps = missingSkills.length > 0 ? missingSkills : ['No gaps for the selected role'];

  return (
    <div className="path">
      {steps.map((label, index) => {
        const between = 2;
        return (
          <div key={label} className="path__step">
            <div className="path__row">
              <div className={`path__node${missingSkills.includes(label) ? ' path__node--active' : ''}`}>
                <span>{index + 1}</span>
              </div>
              {index < steps.length - 1 && (
                <div className="path__connector">
                  <div className="path__line" />
                  <span className="path__connector-text">{between} wk</span>
                </div>
              )}
            </div>
            <p className="path__label">{label}</p>
            <p className="path__meta">{index * between} wk from start</p>
          </div>
        );
      })}
    </div>
  );
}

function ProfileCard({ userProfile, matchedSkills, missingSkills }) {
  return (
    <div className="card profile">
      <div>
        <h3 className="profile__name">{userProfile.name}</h3>
        <p className="profile__role">{userProfile.role || 'Employee'}</p>
        <p className="profile__location">{userProfile.location || '-'}</p>
      </div>
      <div className="profile__skills">
        <span className="profile__skills-label">Your skills</span>
        <div className="chip-row">
          {userProfile.skills.slice(0, 4).map((skill) => (
            <span key={skill} className="chip chip--have">{skill}</span>
          ))}
          {matchedSkills?.slice(0, 4).map((skill) => (
            <span key={`match-${skill}`} className="chip chip--have">{skill}</span>
          ))}
          {missingSkills?.slice(0, 4).map((skill) => (
            <span key={`miss-${skill}`} className="chip chip--need">{skill}</span>
          ))}
          {userProfile.skills.length > 4 && (
            <span className="chip chip--muted">+{userProfile.skills.length - 4}</span>
          )}
        </div>
      </div>
    </div>
  );
}

function Opportunities({ matches, jobsById, selectedJobId, setSelectedJobId }) {
  if (!matches || matches.length === 0) {
    return (
      <section className="opportunities">
        <h2 className="section__title">Opportunities</h2>
        <p className="data-sync__empty">No matches yet for this employee.</p>
      </section>
    );
  }

  return (
    <section className="opportunities">
      <div className="section__title-row">
        <div>
          <h2 className="section__title">Opportunities</h2>
          <p className="section__subtitle">Ranked by match score</p>
        </div>
        <span className="pill">{matches.length} roles</span>
      </div>
      <div className="opportunities__list">
        {matches.map((match) => {
          const job = jobsById[match.job_id] || {};
          const requiredSkills = parseSkills(job.job_required_skills || '');
          const matched = parseSkills(match.skill_match);
          const missing = parseSkills(match.skill_miss);
          const matchedSet = new Set(matched.map((s) => s.toLowerCase()));
          const isSelected = selectedJobId === match.job_id;
          return (
            <article
              key={match.job_id}
              className={`job-card job-card--compact${isSelected ? ' job-card--selected' : ''}`}
              onClick={() => setSelectedJobId(match.job_id)}
            >
              <header className="job-card__header">
                <div>
                  <h3 className="job-card__title">{match.job_title || job.job_title || match.job_id}</h3>
                  <p className="job-card__company">{job.job_id} - Match {match.match_mark || '-'}</p>
                </div>
                <div className="job-card__meta">
                  <span>Score {match.match_score?.toFixed?.(2) ?? match.match_score}</span>
                  <span className="job-card__salary">{requiredSkills.length} required skills</span>
                </div>
              </header>

              <div className="chip-row chip-row--wrap">
                {requiredSkills.slice(0, 4).map((skill) => (
                  <span key={skill} className={`chip ${matchedSet.has(skill.toLowerCase()) ? 'chip--have' : 'chip--need'}`}>
                    {skill}
                  </span>
                ))}
                {requiredSkills.length > 4 && (
                  <span className="chip chip--muted">+{requiredSkills.length - 4} more</span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function LearningPanel({
  selectedMatch,
  jobsById,
  missingSkills,
  matchedSkills,
  trainingPlan,
  trainingPlanLoading,
  trainingPlanError,
  learningHours,
  setLearningHours
}) {
  if (!selectedMatch) {
    return (
      <div className="card card--placeholder">
        <h3 className="card__title">Growth path</h3>
        <p className="card__subtitle">Pick a job on the left to view the skill path.</p>
      </div>
    );
  }

  const job = jobsById[selectedMatch.job_id] || {};
  const requiredSkills = parseSkills(job.job_required_skills || '');
  const planSkills = trainingPlan ? parseSkills(trainingPlan.skill_miss) : missingSkills;
  const deepCourses = trainingPlan ? parseList(trainingPlan.deep_courses_list) : [];
  const deepHours = trainingPlan ? parseNumericList(trainingPlan.deep_hours_list) : [];
  const hoursPerWeek = Math.max(1, Number(learningHours) || 1);
  const scoreValue = Number(selectedMatch.match_score) || 0;
  const matchedCount = matchedSkills.length;
  const requiredCount = requiredSkills.length || 1;
  const requiredMatchRatio = Math.min(1, matchedCount / requiredCount);

  const totalHours = (deepHours.length ? deepHours : planSkills.map(() => 10)).reduce((sum, hrs) => {
    const val = Number(hrs);
    return sum + (Number.isFinite(val) ? val : 10);
  }, 0);
  const totalWeeks = Math.ceil(totalHours / hoursPerWeek);

  return (
    <div className="card detail-panel">
      <div className="detail-panel__header">
        <div>
          <p className="eyebrow">Growth path</p>
          <h3 className="detail-panel__title">{selectedMatch.job_title || job.job_title || selectedMatch.job_id}</h3>
          <p className="card__subtitle">Required skills: {requiredSkills.length || 'n/a'}</p>
        </div>
        <div className="score-row">
          <ScoreDonut
            value={scoreValue}
            max={1}
            label="Match score"
            accent="#78faae"
            format={(val) => `${Math.round(val * 100)}%`}
          />
          <ScoreDonut
            value={requiredMatchRatio}
            max={1}
            label="Required skills"
            accent="#76b4ff"
            format={(val) => `${Math.round(val * 100)}%`}
            helper={`${matchedCount} / ${requiredSkills.length || 0} matched`}
          />
        </div>
      </div>

      <div className="detail-panel__skills">
        <div className="detail-panel__skills-group">
          <p className="detail-panel__label">You already have</p>
          <div className="chip-row chip-row--wrap">
            {matchedSkills.length === 0 && <span className="chip chip--muted">No overlap yet</span>}
            {matchedSkills.map((skill) => (
              <span key={`match-${skill}`} className="chip chip--have">{skill}</span>
            ))}
          </div>
        </div>
        <div className="detail-panel__skills-group">
          <p className="detail-panel__label">To learn next</p>
          <div className="chip-row chip-row--wrap">
            {missingSkills.length === 0 && <span className="chip chip--have">Ready for this role</span>}
            {missingSkills.map((skill) => (
              <span key={`miss-${skill}`} className="chip chip--need">{skill}</span>
            ))}
          </div>
        </div>
      </div>

      <LearningPath
        skills={planSkills}
        courses={deepCourses}
        hours={deepHours}
        isLoading={trainingPlanLoading}
        error={trainingPlanError}
        title={selectedMatch.job_title || job.job_title || selectedMatch.job_id}
        hoursPerWeek={hoursPerWeek}
        totalWeeks={totalWeeks}
        learningHours={learningHours}
        setLearningHours={setLearningHours}
      />
    </div>
  );
}

function LearningPath({ skills, courses, hours, isLoading, error, title, hoursPerWeek, totalWeeks, learningHours, setLearningHours }) {
  const normalizedSkills = skills && skills.length > 0 ? skills : ['No gaps identified'];
  const [draftHours, setDraftHours] = useState(learningHours);

  useEffect(() => {
    setDraftHours(learningHours);
  }, [learningHours]);

  if (isLoading) {
    return (
      <div className="detail-panel__path">
        <p className="detail-panel__label">Learning path</p>
        <p className="card__subtitle">Loading training steps...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="detail-panel__path">
        <p className="detail-panel__label">Learning path</p>
        <p className="data-sync__error">{error}</p>
      </div>
    );
  }

  return (
    <div className="detail-panel__path">
      <div className="detail-panel__path-header">
        <p className="detail-panel__label">Learning path</p>
        <span className="detail-panel__meta">Linked to {title}</span>
      </div>
      <div className="learning-path">
        <div className="learning-path__summary">
          <div>
            <p className="detail-panel__label">Total time</p>
            <p className="learning-path__total">{totalWeeks || 0} wk</p>
            <p className="detail-panel__meta">Based on courses + your weekly availability.</p>
          </div>
          <label className="learning-path__control">
            <span>Hours per week</span>
            <input
              type="number"
              min="1"
              max="60"
              value={draftHours}
              onChange={(e) => setDraftHours(Math.max(1, Number(e.target.value) || 1))}
            />
            <button
              type="button"
              className="button button--secondary learning-path__apply"
              onClick={() => setLearningHours(Math.max(1, Number(draftHours) || 1))}
            >
              Apply hours
            </button>
          </label>
        </div>
        {normalizedSkills.map((skill, index) => {
          const course = courses[index] || 'Recommended deep course';
          const hoursNeededRaw = hours[index];
          const hoursNeeded = Number.isFinite(Number(hoursNeededRaw)) ? Number(hoursNeededRaw) : 10;
          const weeks = Math.max(1, Math.ceil(hoursNeeded / hoursPerWeek));
          const isEven = index % 2 === 0;
          return (
            <div key={skill} className={`learning-path__item${isEven ? ' learning-path__item--left' : ' learning-path__item--right'}`}>
              <div className="learning-path__connector" />
              <div className="learning-path__card">
                <div className="learning-path__badge">{index + 1}</div>
                <div className="learning-path__content">
                  <p className="learning-path__skill">{skill}</p>
                  <p className="learning-path__course">{course}</p>
                </div>
                <span className="pill pill--time">{weeks} wk</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ScoreDonut({ value = 0, max = 1, label, accent = '#78faae', format = (v) => v, helper }) {
  const safeMax = max || 1;
  const pct = Math.max(0, Math.min(1, value / safeMax));
  const deg = pct * 360;
  const display = format ? format(value) : value;
  const style = {
    background: `conic-gradient(${accent} ${deg}deg, rgba(255,255,255,0.06) ${deg}deg)`,
  };

  return (
    <div className="score-donut">
      <div className="score-donut__circle" style={style}>
        <div className="score-donut__inner">
          <span className="score-donut__value">{display}</span>
          <span className="score-donut__label">{label}</span>
        </div>
      </div>
      {helper && <p className="score-donut__helper">{helper}</p>}
    </div>
  );
}

function HrMatchPanel({ job, matches, loading, trainingPlans, error }) {
  if (!job) {
    return <div className="card card--placeholder">Select a job to see top employees.</div>;
  }

  if (loading) {
    return (
      <div className="card card--placeholder">
        <p className="card__subtitle">Loading matches...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card card--placeholder">
        <p className="data-sync__error">{error}</p>
      </div>
    );
  }

  if (!matches || matches.length === 0) {
    return (
      <div className="card card--placeholder">
        <p className="card__subtitle">No employees ranked for this job yet.</p>
      </div>
    );
  }

  return (
    <div className="card detail-panel">
      <div className="detail-panel__header">
        <div>
          <p className="eyebrow">Top employees</p>
          <h3 className="detail-panel__title">{job.job_title}</h3>
          <p className="card__subtitle">Best matches ordered by score.</p>
        </div>
        <span className="pill">{matches.length} employees</span>
      </div>

      <div className="hr-matches">
        {matches.map((row) => {
          const plan = trainingPlans[`${row.job_id}-${row.emp_id}`];
          const skillMiss = parseSkills(plan?.skill_miss || row.skill_miss);
          const skillMatch = parseSkills(plan?.skill_match || row.skill_match);
          const requiredSkills = parseSkills(job.job_required_skills || '');
          const matchedCount = skillMatch.length;
          const requiredCount = requiredSkills.length || 1;
          const requiredRatio = Math.min(1, matchedCount / requiredCount);
          const scoreVal = Number(row.match_score) || 0;
          const deepCourses = parseList(plan?.deep_courses_list);
          const deepHours = parseNumericList(plan?.deep_hours_list);
          const timeWeeks = deepHours[0] ? Math.ceil(Number(deepHours[0]) / 10) : 2;
          return (
            <div key={`${row.job_id}-${row.emp_id}`} className="hr-matches__item">
              <div className="hr-matches__top">
                <div>
                  <p className="hr-matches__title">{row.emp_id}</p>
                  <p className="hr-matches__meta">{matchedCount} / {requiredCount} skills matched</p>
                </div>
                <div className="score-row">
                  <ScoreDonut
                    value={scoreVal}
                    max={1}
                    label="Match score"
                    accent="#78faae"
                    format={(val) => `${Math.round(val * 100)}%`}
                  />
                  <ScoreDonut
                    value={requiredRatio}
                    max={1}
                    label="Required skills"
                    accent="#76b4ff"
                    format={(val) => `${Math.round(val * 100)}%`}
                    helper={`${matchedCount} / ${requiredSkills.length || 0} matched`}
                  />
                </div>
              </div>
              <div className="chip-row chip-row--wrap">
                {skillMiss.length === 0 && <span className="chip chip--have">Ready</span>}
                {skillMiss.map((skill) => (
                  <span key={skill} className="chip chip--need">{skill}</span>
                ))}
              </div>
              <div className="hr-matches__course">
                <span className="pill pill--time">{timeWeeks} wk</span>
                <span className="hr-matches__course-name">{deepCourses[0] || 'Recommended deep course'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OpportunityToggle({ active, onToggle, reason, onChooseReason }) {
  const reasons = [
    { value: 'personal', label: 'Personal reasons' },
    { value: 'bored', label: 'Bored' },
    { value: 'learn', label: 'Learn a new skill' },
  ];

  return (
    <div className={`cta-bar${active ? ' cta-bar--active' : ''}`}>
      <div className="cta-bar__content">
        <div>
          <p className="eyebrow">Career mobility</p>
          <h3 className="cta-bar__title">I want new opportunities</h3>
          <p className="cta-bar__subtitle">Signal interest and tailor recommendations.</p>
        </div>
        <button type="button" className={`button button--primary cta-bar__button${active ? ' button--primary-strong' : ''}`} onClick={onToggle}>
          {active ? 'Interest enabled' : 'Enable interest'}
        </button>
      </div>
      {active && (
        <div className="cta-bar__reasons">
          {reasons.map((item) => {
            const selected = reason === item.value;
            return (
              <button
                key={item.value}
                type="button"
                className={`pill pill--choice${selected ? ' pill--choice-active' : ''}`}
                onClick={() => onChooseReason(item.value)}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function DreamJobPath() {
  const dreamJob = 'ML Engineer';
  const steps = [
    { id: 's1', label: 'Foundations: Python + SQL', weeks: 2 },
    { id: 's2', label: 'ML basics: Pandas + NumPy', weeks: 4 },
    { id: 's3', label: 'Modeling: TensorFlow intro', weeks: 6 },
    { id: 's4', label: 'Deployment: Docker + APIs', weeks: 8 },
  ];

  return (
    <div className="card">
      <h2 className="card__title">Path to dream job: {dreamJob}</h2>
      <p className="card__subtitle">Standard learning plan you can adapt.</p>
      <div className="path">
        {steps.map((step, index) => (
          <div key={step.id} className="path__step">
            <div className="path__row">
              <div className="path__node">
                <span>{index + 1}</span>
              </div>
              {index < steps.length - 1 && (
                <div className="path__connector">
                  <div className="path__line" />
                  <span className="path__connector-text">{step.weeks} wk</span>
                </div>
              )}
            </div>
            <p className="path__label">{step.label}</p>
            <p className="path__meta">{index === 0 ? 'Start now' : `${step.weeks} wk from previous`}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function DreamJobSummary({ missingSkills }) {
  const dreamJob = 'ML Engineer';
  const items = missingSkills.length > 0
    ? missingSkills.map((skill, index) => ({
      label: skill,
      weeks: (index + 1) * 2,
    }))
    : [{ label: 'Ready for this role', weeks: 0 }];

  return (
    <div className="card dream-card">
      <div className="dream-card__header">
        <div>
          <p className="eyebrow">Dream job</p>
          <h3 className="dream-card__title">{dreamJob}</h3>
          <p className="card__subtitle">Missing skills with estimated time to close the gap.</p>
        </div>
      </div>
      <div className="dream-card__list">
        {items.map((item) => (
          <div key={item.label} className="dream-card__item">
            <span className="dream-card__skill">{item.label}</span>
            <span className="pill pill--time">{item.weeks} wk</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
function parseList(raw) {
  if (!raw || typeof raw !== 'string') return [];
  return raw.split(';').map((item) => item.trim()).filter(Boolean);
}

function parseNumericList(raw) {
  return parseList(raw).map((num) => {
    const parsed = Number(num);
    return Number.isFinite(parsed) ? parsed : null;
  });
}
