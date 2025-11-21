/**
 * Utility function to create page URLs for navigation
 * Converts page names to URL paths
 */
export function createPageUrl(pageName: string): string {
  const routes: Record<string, string> = {
    'Login': '/login',
    'Dashboard': '/dashboard',
    'ManagerDashboard': '/manager-dashboard',
    'MyQualifications': '/my-qualifications',
    'AIRecommendations': '/ai-recommendations',
    'LearningPaths': '/learning-paths',
    'TeamSkillsOverview': '/team-skills-overview',
    'Profile': '/profile'
  };

  return routes[pageName] || '/';
}
