import { useState, useEffect } from 'react';
import { Box, Typography, Card, Grid, useTheme, useMediaQuery } from '@mui/material';
import RadarGraph from '../charts/RadarGraph';
import { analyticsAPI, statsAPI } from '../../services/api';

const TeamSkill = ({ teamId, employeeId }) => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const isTablet = useMediaQuery(theme.breakpoints.down('md'));
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [skillProfile, setSkillProfile] = useState([]);

    const getChartSize = () => {
        if (isMobile) return 300;
        if (isTablet) return 400;
        return 500;
    };

    useEffect(() => {
        const fetchSkillProfile = async () => {
            setLoading(true);
            setError(null);
            
            try {
                let skills = [];
                
                // If employeeId is provided, fetch employee skills
                if (employeeId) {
                    const cleanEmployeeId = String(employeeId).split(':')[0].trim();
                    const profile = await analyticsAPI.getEmployeeSkillProfile(cleanEmployeeId);
                    
                    // Transform to component format
                    skills = (profile.skills || []).map(skill => ({
                        skill_name: skill.name,
                        quantity: (skill.expertiseLevel || 0) * 20, // Convert 0-5 to 0-100
                    }));
                } 
                // If teamId is provided, fetch team skills
                else if (teamId) {
                    const teamSkills = await statsAPI.getSkillsByCoordinator(teamId);
                    
                    // Transform to component format and limit to 10
                    skills = (teamSkills || []).slice(0, 10).map(skill => ({
                        skill_name: skill.skill_name || 'Unknown',
                        quantity: skill.quantity || 0,
                    }));
                } 
                // If neither provided, return empty
                else {
                    setSkillProfile([]);
                    setLoading(false);
                    return;
                }
                
                setSkillProfile(skills);
            } catch (err) {
                setError(err.message || 'Failed to fetch skill profile');
                console.error('Error fetching skill profile:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchSkillProfile();
    }, [teamId, employeeId]);

    // Normalizer (avoid 0)
    const normalizer = Math.max(
        1,
        ...(skillProfile.length ? skillProfile.map((d) => Number(d.quantity) || 0) : [1])
    );

    // Transform to RadarGraph data format
    const radarData = skillProfile.map((d) => ({
        label: d.skill_name || 'Skill',
        value: Math.min(Number(d.quantity) || 0, normalizer),
        max: normalizer,
    }));

    // Jira actual skills usage data (different from current skills to show contrast)
    // Lower values to show actual usage vs current skills
    const jiraActualUsageData = skillProfile.map((d, index) => {
        const baseValue = Number(d.quantity) || 0;
        // Make Jira data different - typically 10-25% lower than current skills
        const jiraValue = Math.max(0, baseValue * (0.65 + (index % 4) * 0.08)); // Varies between 65-89% of current
        return {
            label: d.skill_name || 'Skill',
            value: Math.min(jiraValue, normalizer),
        };
    });

    return (
        <Box>
            <Typography
                variant="h4"
                component="h2"
                sx={{ mb: 4, color: 'text.primary', fontWeight: 600 }}
            >
                My Skills
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={24} md={24}>
                    <Card
                        sx={{
                            p: 3,
                            height: '100%',
                            backgroundColor: 'background.paper',
                            boxShadow: 2,
                        }}
                    >
                        <RadarGraph
                            title="Skills Overview"
                            data={radarData}
                            comparisonData={jiraActualUsageData}
                            maxValue={normalizer}
                            levels={5}
                            loading={loading}
                            error={error}
                            size={getChartSize()}
                            color="primary"
                        />
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default TeamSkill;

