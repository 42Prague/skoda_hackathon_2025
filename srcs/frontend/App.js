import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  TextInput,
  ScrollView,
  FlatList
} from 'react-native';

const EMPLOYEES = [
  { id: 1, name: 'Amira Chen', role: 'Product Designer', status: 'Active posting', location: 'Prague', skills: ['Figma', 'Prototyping', 'Research'] },
  { id: 2, name: 'Luis Ortega', role: 'Senior Backend', status: 'Interviewing', location: 'Berlin', skills: ['Node.js', 'Postgres', 'APIs'] },
  { id: 3, name: 'max govindaraju', role: 'HR Business Partner', status: 'New hire', location: 'Remote', skills: ['Communication', 'Onboarding', 'Excel'] },
  { id: 4, name: 'Jonas Eriksen', role: 'Mobile Engineer', status: 'Internal move', location: 'Copenhagen', skills: ['React Native', 'TypeScript', 'Debugging'] }
];

const theme = {
  bg: '#0E3A2F',
  card: '#0b2f26',
  muted: '#b2e6c7',
  primary: '#78FAAE',
  accent: '#78FAAE',
  border: '#135240'
};

/**
 * PATH: the "dream job" path shown at top.
 * Each step can have 'label' and 'weeksFromPrevious' (how many weeks from previous step).
 * The UI will compute cumulative weeks to show "from beginning" and "between steps".
 */
const PATH = [
  { id: 's1', label: 'Skill_1', weeksFromPrevious: 0 },    // start
  { id: 's2', label: 'Skill_2', weeksFromPrevious: 4 },
  { id: 's3', label: 'Skill_3', weeksFromPrevious: 6 },
  { id: 's4', label: 'Skill_4', weeksFromPrevious: 8 }
];

/**
 * JOBS: example job cards similar to job lists on Indeed/LinkedIn.
 * Each job has requiredSkills (used to compare with userSkills) and its own path (weeks).
 */
const JOBS = [
  {
    id: 'j1',
    title: 'Frontend Engineer (React)',
    company: 'Greenwave Labs',
    location: 'Prague, CZ',
    posted: '2 days ago',
    salary: '€48k - €60k',
    requiredSkills: ['React', 'JavaScript', 'TypeScript', 'CSS', 'Accessibility'],
    description:
      'We are looking for a Frontend Engineer to build performant, accessible interfaces. You will collaborate with product and design to ship user-focused web apps.'
  },
  {
    id: 'j2',
    title: 'Data Analyst',
    company: 'Insight Metrics',
    location: 'Remote',
    posted: '5 days ago',
    salary: '€42k - €52k',
    requiredSkills: ['SQL', 'Excel', 'Tableau', 'Statistics'],
    description:
      'Join a small data team to analyse customer behaviour and build dashboards used by leadership to make strategic decisions.'
  },
  {
    id: 'j3',
    title: 'Mobile Developer (React Native)',
    company: 'Nomad Apps',
    location: 'Berlin, DE',
    posted: '1 week ago',
    salary: '€55k - €70k',
    requiredSkills: ['React Native', 'TypeScript', 'APIs', 'Testing'],
    description:
      'Build cross-platform mobile apps for a scaling consumer product. You will help shape architecture and CI workflows.'
  }
];

export default function App() {
  const [stage, setStage] = React.useState('login'); // login | hr-dashboard | employee-dashboard
  const [role, setRole] = React.useState('HR');
  const [name, setName] = React.useState('');
  const [password, setPassword] = React.useState('');
  const passwordRef = React.useRef(null);

  // current selected job id for expanded view
  const [selectedJobId, setSelectedJobId] = React.useState(null);

  // user skills come from matched employee if name matches, otherwise default
  const DEFAULT_USER_SKILLS = ['Communication', 'Excel', 'React Native'];

  const findProfileByName = (n) => {
    if (!n) return null;
    const found = EMPLOYEES.find(e => e.name.toLowerCase() === n.toLowerCase());
    return found || null;
  };

  const userProfile = React.useMemo(() => {
    const match = findProfileByName(name);
    return match ? { ...match } : { id: 0, name: name || 'You', skills: DEFAULT_USER_SKILLS };
  }, [name]);

  const startLogin = () => {
    if (role === 'HR') return setStage('hr-dashboard');
    setStage('employee-dashboard');
  };

  const logout = () => {
    setStage('login');
    setSelectedJobId(null);
    setRole('HR');
    setName('');
    setPassword('');
  };

  const goHome = () => setStage(role === 'HR' ? 'hr-dashboard' : 'employee-dashboard');

  const renderHeader = (title, subtitle) => (
    <View style={styles.header}>
      <View>
        <Text style={styles.kicker}>Internal Job Management</Text>
        <Text style={styles.pageTitle}>{title}</Text>
        <Text style={styles.pageSubtitle}>{subtitle}</Text>
      </View>
      {stage !== 'login' && (
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <Pressable onPress={goHome} style={[styles.pill, { borderColor: theme.primary }]}>
            <Text style={[styles.pillText, { color: theme.primary }]}>{role === 'HR' ? 'HR' : 'Employee'} dashboard</Text>
          </Pressable>
          <Pressable onPress={logout} style={[styles.pill, { borderColor: '#f87171' }]}>
            <Text style={[styles.pillText, { color: '#f87171' }]}>Logout</Text>
          </Pressable>
        </View>
      )}
    </View>
  );

  /**
   * Helper component: circular step + connector line
   */
  const StepConnector = ({ stepIndex, cumulativeWeeks, betweenWeeksLabel, active = false }) => (
    <View style={styles.stepBlock}>
      <View style={styles.stepRow}>
        <View style={[styles.stepCircle, active && { borderColor: theme.primary, backgroundColor: 'rgba(120,250,174,0.06)' }]}>
          <Text style={[styles.stepCircleText, active && { color: theme.primary }]}>{stepIndex + 1}</Text>
        </View>
        {stepIndex < PATH.length - 1 && (
          <View style={styles.connector}>
            <View style={styles.connectorLine} />
            <Text style={styles.connectorLabel}>{`${betweenWeeksLabel} wk`}</Text>
          </View>
        )}
      </View>
      <Text style={styles.stepLabel}>{PATH[stepIndex].label}</Text>
      <Text style={styles.stepCumulative}>{cumulativeWeeks} wk from start</Text>
    </View>
  );

  /**
   * Top Path (Path to Dream Job) — shows all PATH steps and weeks
   */
  const PathToDreamJob = ({ highlightMissing = [] }) => {
    // compute cumulative weeks from start
    const cum = [];
    let total = 0;
    PATH.forEach((p, i) => {
      total += p.weeksFromPrevious ?? 0;
      cum.push(total);
    });

    return (
      <View style={[styles.card, styles.pathCard]}>
        <Text style={styles.pathTitle}>Path to Dream Job</Text>
        <Text style={styles.pathSubtitle}>Plan of skills and time to acquire them</Text>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 16 }} contentContainerStyle={{ paddingBottom: 6 }}>
          {PATH.map((p, i) => {
            // weeks between current and next
            const between = i < PATH.length - 1 ? PATH[i + 1].weeksFromPrevious ?? 0 : 0;
            // highlight if in missing list (useful for job-specific path; by default none)
            const isMissing = highlightMissing.includes(p.label);
            return (
              <View key={p.id} style={{ marginRight: 12 }}>
                <StepConnector
                  stepIndex={i}
                  cumulativeWeeks={cum[i]}
                  betweenWeeksLabel={i < PATH.length - 1 ? PATH[i + 1].weeksFromPrevious ?? 0 : 0}
                  active={isMissing}
                />
              </View>
            );
          })}
        </ScrollView>
      </View>
    );
  };

  /**
   * Job card list item
   */
  const JobCard = ({ job, expanded, onPress, isFirst }) => {
    // compute match of user skills
    const userSkillsSet = new Set(userProfile.skills.map(s => s.toLowerCase()));
    const matched = job.requiredSkills.filter(s => userSkillsSet.has(s.toLowerCase()));
    const missing = job.requiredSkills.filter(s => !userSkillsSet.has(s.toLowerCase()));

    return (
      <Pressable onPress={onPress} style={[styles.jobCard, expanded && styles.jobCardExpanded]}>
        <View style={styles.jobHeader}>
          <View style={{ flex: 1 }}>
            <Text style={styles.jobTitle}>{job.title}</Text>
            <Text style={styles.jobCompany}>{job.company} • {job.location}</Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={styles.jobPosted}>{job.posted}</Text>
            <Text style={styles.jobSalary}>{job.salary}</Text>
          </View>
        </View>

        <View style={styles.jobMetaRow}>
          <View style={styles.skillPreview}>
            {job.requiredSkills.slice(0, 4).map((s, idx) => {
              const have = userSkillsSet.has(s.toLowerCase());
              return (
                <View key={s + idx} style={[styles.skillChip, have ? styles.skillHave : styles.skillNeed]}>
                  <Text style={[styles.skillChipText, have ? styles.skillHaveText : styles.skillNeedText]} numberOfLines={1}>
                    {s}
                  </Text>
                </View>
              );
            })}
            {job.requiredSkills.length > 4 && <Text style={styles.moreSkills}>+{job.requiredSkills.length - 4}</Text>}
          </View>
        </View>

        {expanded && (
          <View style={styles.jobExpanded}>
            <Text style={styles.sectionTitle}>Skill match</Text>
            <View style={styles.skillListRow}>
              {job.requiredSkills.map(s => {
                const have = userSkillsSet.has(s.toLowerCase());
                return (
                  <View key={s} style={[styles.skillChip, have ? styles.skillHave : styles.skillNeed, { marginRight: 8, marginBottom: 8 }]}>
                    <Text style={[styles.skillChipText, have ? styles.skillHaveText : styles.skillNeedText]}>
                      {s}
                    </Text>
                  </View>
                );
              })}
            </View>

            <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Description</Text>
            <Text style={styles.jobDescription}>{job.description}</Text>

            <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Suggested path to meet requirements</Text>
            {/* For this job-specific path we create steps from missing skills (red) */}
            <View style={[styles.card, styles.jobPathCard]}>
              <Text style={styles.jobPathTitle}>Skills to Acquire</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 12 }}>
                {job.requiredSkills
                  .filter(s => !userSkillsSet.has(s.toLowerCase()))
                  .map((s, idx) => (
                    <View key={s + idx} style={styles.jobPathStep}>
                      <View style={styles.jobPathCircle}>
                        <Text style={styles.jobPathCircleText}>{idx + 1}</Text>
                      </View>
                      <Text style={styles.jobPathStepLabel}>{s}</Text>
                      <Text style={styles.jobPathWeeks}>{(idx + 1) * 2} wk</Text>
                    </View>
                  ))}
                {job.requiredSkills.filter(s => !userSkillsSet.has(s.toLowerCase())).length === 0 && (
                  <Text style={styles.jobPathEmpty}>Great! You already match this job's skills.</Text>
                )}
              </ScrollView>
            </View>
          </View>
        )}
      </Pressable>
    );
  };

  /********************
   * LOGIN component
   ********************/
  const Login = () => (
    <View style={styles.loginWrapper}>
      <View style={styles.heroCard}>
        <Text style={styles.authTitle}>Authentication</Text>
        <TextInput
          value={name}
          placeholder="Username (try 'max govindaraju' to load sample)"
          placeholderTextColor="#c8f2da"
          onChangeText={setName}
          blurOnSubmit={false}
          autoCapitalize="words"
          returnKeyType="next"
          onSubmitEditing={() => passwordRef.current?.focus()}
          style={styles.input}
        />
        <TextInput
          value={password}
          placeholder="Password"
          placeholderTextColor="#c8f2da"
          secureTextEntry
          onChangeText={setPassword}
          blurOnSubmit={false}
          autoCapitalize="none"
          returnKeyType="done"
          ref={passwordRef}
          onSubmitEditing={startLogin}
          style={styles.input}
        />
        <View style={styles.roleToggle}>
          {['HR', 'Employee'].map(item => {
            const active = role === item;
            return (
              <Pressable
                key={item}
                onPress={() => setRole(item)}
                style={[styles.roleToggleButton, active && styles.roleToggleActive]}
              >
                <Text style={[styles.roleToggleText, active && styles.roleToggleTextActive]}>{item}</Text>
              </Pressable>
            );
          })}
        </View>
        <Pressable onPress={startLogin} style={styles.loginButton}>
          <Text style={styles.loginButtonText}>Login</Text>
        </Pressable>
      </View>
    </View>
  );

  /********************
   * HR dashboard placeholder
   ********************/
  const HrDashboard = () => (
    <View style={{ gap: 18 }}>
      {renderHeader('Dashboard HR', '')}
      <View style={[styles.card, styles.placeholderCard]}>
        <Text style={styles.placeholderText}>HR Dashboard content (kept as placeholder)</Text>
      </View>
    </View>
  );

  /********************
   * Employee dashboard - the main UI asked for
   ********************/
  const EmployeeDashboard = () => {
    // selected job object
    const selectedJob = JOBS.find(j => j.id === selectedJobId) || null;

    return (
      <View style={{ gap: 18 }}>
        {renderHeader('Espace Collaborateur', 'Your growth and job opportunities')}
        <View style={{ gap: 14 }}>
          {/* Top path with highlight for missing skills if a job is selected */}
          <PathToDreamJob highlightMissing={selectedJob ? selectedJob.requiredSkills.filter(s => !userProfile.skills.map(x => x.toLowerCase()).includes(s.toLowerCase())) : []} />

          {/* Quick profile summary */}
          <View style={[styles.card, styles.profileCard]}>
            <View style={styles.profileRow}>
              <View>
                <Text style={styles.profileName}>{userProfile.name}</Text>
                <Text style={styles.profileRole}>{userProfile.role || 'Employee'}</Text>
                <Text style={styles.profileLocation}>{userProfile.location || '—'}</Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={styles.smallMuted}>Your skills</Text>
                <View style={{ flexDirection: 'row', marginTop: 8 }}>
                  {userProfile.skills.slice(0, 4).map(s => (
                    <View key={s} style={[styles.skillChip, styles.skillHave, { marginRight: 8 }]}>
                      <Text style={[styles.skillChipText, styles.skillHaveText]}>{s}</Text>
                    </View>
                  ))}
                  {userProfile.skills.length > 4 && <Text style={styles.moreSkills}>+{userProfile.skills.length - 4}</Text>}
                </View>
              </View>
            </View>
          </View>

          {/* Job list */}
          <View style={{ gap: 8 }}>
            <Text style={styles.sectionTitle}>Opportunities</Text>
            <View>
              {JOBS.map((job, idx) => (
                <JobCard
                  key={job.id}
                  job={job}
                  expanded={selectedJobId === job.id}
                  onPress={() => setSelectedJobId(selectedJobId === job.id ? null : job.id)}
                  isFirst={idx === 0}
                />
              ))}
            </View>
          </View>
        </View>
      </View>
    );
  };

  return (
    <ScrollView style={styles.app} contentContainerStyle={styles.container}>
      <View style={styles.bgBlobOne} />
      <View style={styles.bgBlobTwo} />
      {stage === 'login' && <Login />}
      {stage === 'hr-dashboard' && <HrDashboard />}
      {stage === 'employee-dashboard' && <EmployeeDashboard />}
    </ScrollView>
  );
}

/********************
 * Styles
 ********************/
const styles = StyleSheet.create({
  app: {
    backgroundColor: theme.bg
  },
  container: {
    minHeight: '100vh',
    paddingVertical: 32,
    paddingHorizontal: 20,
    gap: 20,
    position: 'relative'
  },
  bgBlobOne: {
    position: 'absolute',
    width: 320,
    height: 320,
    backgroundColor: '#0c473a',
    opacity: 0.35,
    borderRadius: 999,
    top: -40,
    left: -80,
    transform: [{ rotate: '12deg' }]
  },
  bgBlobTwo: {
    position: 'absolute',
    width: 260,
    height: 260,
    backgroundColor: '#0a2d24',
    opacity: 0.32,
    borderRadius: 999,
    bottom: 60,
    right: -60,
    transform: [{ rotate: '-8deg' }]
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6
  },
  loginWrapper: {
    flex: 1,
    minHeight: 520,
    alignItems: 'center',
    justifyContent: 'center'
  },
  kicker: {
    color: theme.muted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontSize: 12
  },
  pageTitle: {
    color: '#fff',
    fontSize: 30,
    fontWeight: '700',
    marginTop: 4
  },
  pageSubtitle: {
    color: theme.muted,
    marginTop: 6,
    fontSize: 15
  },
  heroCard: {
    backgroundColor: '#0b2f26',
    borderColor: theme.border,
    borderWidth: 1,
    padding: 24,
    borderRadius: 26,
    gap: 14,
    width: '100%',
    maxWidth: 520,
    alignItems: 'center'
  },
  authTitle: {
    color: theme.primary,
    fontSize: 32,
    fontWeight: '700',
    marginBottom: 12
  },
  input: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderColor: theme.border,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#fff',
    fontSize: 16,
    minWidth: 260,
    alignSelf: 'stretch'
  },
  roleToggle: {
    flexDirection: 'row',
    borderRadius: 999,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#103c31'
  },
  roleToggleButton: {
    paddingVertical: 10,
    paddingHorizontal: 22,
    backgroundColor: '#0b2f26'
  },
  roleToggleActive: {
    backgroundColor: '#08261f'
  },
  roleToggleText: {
    color: '#bfead2',
    fontWeight: '700',
    fontSize: 14
  },
  roleToggleTextActive: {
    color: '#78FAAE'
  },
  loginButton: {
    backgroundColor: '#0c2e26',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#123a2f',
    marginTop: 6
  },
  loginButtonText: {
    color: '#c9f5de',
    fontWeight: '700',
    fontSize: 18
  },

  /***** cards & common *****/
  card: {
    borderWidth: 1,
    borderColor: theme.border,
    backgroundColor: '#0f1b2f',
    borderRadius: 16,
    padding: 14
  },
  pathCard: {
    paddingVertical: 18
  },
  pathTitle: {
    color: theme.primary,
    fontSize: 20,
    fontWeight: '800'
  },
  pathSubtitle: {
    color: theme.muted,
    fontSize: 13,
    marginTop: 6
  },
  stepBlock: {
    width: 140,
    alignItems: 'flex-start'
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  stepCircle: {
    width: 44,
    height: 44,
    borderRadius: 44,
    borderWidth: 1,
    borderColor: theme.border,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent'
  },
  stepCircleText: {
    color: '#fff',
    fontWeight: '700'
  },
  connector: {
    marginLeft: 10,
    alignItems: 'center'
  },
  connectorLine: {
    width: 60,
    height: 2,
    backgroundColor: '#123a2f',
    marginBottom: 6
  },
  connectorLabel: {
    color: theme.muted,
    fontSize: 12
  },
  stepLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 8
  },
  stepCumulative: {
    color: theme.muted,
    fontSize: 12
  },

  profileCard: {
    paddingHorizontal: 18,
    paddingVertical: 14
  },
  profileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  profileName: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '800'
  },
  profileRole: {
    color: theme.muted,
    fontSize: 13,
    marginTop: 6
  },
  profileLocation: {
    color: theme.muted,
    fontSize: 13
  },
  smallMuted: {
    color: theme.muted,
    fontSize: 12
  },

  sectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8
  },

  /***** job list styling *****/
  jobCard: {
    backgroundColor: '#0b2f26',
    borderColor: theme.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginBottom: 10
  },
  jobCardExpanded: {
    backgroundColor: '#0f3b32'
  },
  jobHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10
  },
  jobTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800'
  },
  jobCompany: {
    color: theme.muted,
    fontSize: 13,
    marginTop: 4
  },
  jobPosted: {
    color: theme.muted,
    fontSize: 12
  },
  jobSalary: {
    color: '#d9f9de',
    fontSize: 12,
    marginTop: 6,
    fontWeight: '700'
  },
  jobMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  skillPreview: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'nowrap'
  },
  skillChip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'transparent'
  },
  skillChipText: {
    fontWeight: '700',
    fontSize: 12
  },
  skillHave: {
    backgroundColor: 'rgba(120,250,174,0.15)',
    borderColor: theme.primary
  },
  skillHaveText: {
    color: theme.primary
  },
  skillNeed: {
    backgroundColor: 'rgba(248,113,113,0.08)',
    borderColor: '#f87171'
  },
  skillNeedText: {
    color: '#f87171'
  },
  moreSkills: {
    color: theme.muted,
    marginLeft: 8,
    fontSize: 12
  },

  jobExpanded: {
    marginTop: 12
  },
  jobDescription: {
    color: theme.muted,
    lineHeight: 20
  },

  jobPathCard: {
    padding: 12,
    marginTop: 8,
    borderRadius: 12,
    backgroundColor: '#0b2f26'
  },
  jobPathTitle: {
    color: '#fff',
    fontWeight: '800'
  },
  jobPathStep: {
    width: 120,
    marginRight: 12,
    alignItems: 'center'
  },
  jobPathCircle: {
    width: 44,
    height: 44,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#f87171',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(248,113,113,0.05)'
  },
  jobPathCircleText: {
    color: '#f87171',
    fontWeight: '800'
  },
  jobPathStepLabel: {
    color: '#fff',
    marginTop: 8,
    fontWeight: '700'
  },
  jobPathWeeks: {
    color: theme.muted,
    fontSize: 12,
    marginTop: 4
  },
  jobPathEmpty: {
    color: theme.muted,
    paddingVertical: 8
  },

  placeholderCard: {
    padding: 24,
    alignItems: 'center'
  },
  placeholderText: {
    color: theme.muted
  }
});