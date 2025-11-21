import { useRef, useEffect } from 'react';
import { Box, Typography, useTheme, Tooltip } from '@mui/material';

const NetworkGraph = ({ 
  title, 
  data, 
  maxValue = 100,
  size = 500,
  centerNode = { label: 'Job', type: 'job' },
  loading = false,
  error = null 
}) => {
  const svgRef = useRef(null);
  const theme = useTheme();

  useEffect(() => {
    if (!data || data.length === 0 || loading || error || !svgRef.current) return;

    const svg = svgRef.current;
    const width = size;
    const height = size;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35; // Distance from center to skill nodes

    // Clear previous content
    svg.innerHTML = '';

    // Create groups for edges, nodes, and labels
    const edgesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    edgesGroup.setAttribute('class', 'edges');
    const nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    nodesGroup.setAttribute('class', 'nodes');
    const labelsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    labelsGroup.setAttribute('class', 'labels');

    // Calculate angles for skill nodes (distributed around the circle)
    const angleStep = (2 * Math.PI) / data.length;

    // Draw edges first (so they appear behind nodes)
    data.forEach((skill, index) => {
      const angle = index * angleStep - Math.PI / 2; // Start from top
      const skillX = centerX + radius * Math.cos(angle);
      const skillY = centerY + radius * Math.sin(angle);

      const edge = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      edge.setAttribute('x1', centerX);
      edge.setAttribute('y1', centerY);
      edge.setAttribute('x2', skillX);
      edge.setAttribute('y2', skillY);
      edge.setAttribute('stroke', theme.palette.primary.main);
      edge.setAttribute('stroke-width', '2');
      edge.setAttribute('opacity', '0.4');
      edgesGroup.appendChild(edge);
    });

    // Draw center node (Job/Employee)
    const centerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    centerCircle.setAttribute('cx', centerX);
    centerCircle.setAttribute('cy', centerY);
    centerCircle.setAttribute('r', 40);
    centerCircle.setAttribute('fill', theme.palette.primary.main);
    centerCircle.setAttribute('stroke', theme.palette.primary.dark);
    centerCircle.setAttribute('stroke-width', '3');
    centerCircle.setAttribute('class', 'center-node');
    nodesGroup.appendChild(centerCircle);

    // Center node label
    const centerText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centerText.setAttribute('x', centerX);
    centerText.setAttribute('y', centerY);
    centerText.setAttribute('text-anchor', 'middle');
    centerText.setAttribute('dominant-baseline', 'middle');
    centerText.setAttribute('fill', theme.palette.primary.contrastText || '#fff');
    centerText.setAttribute('font-size', '14');
    centerText.setAttribute('font-weight', 'bold');
    centerText.textContent = centerNode.label;
    labelsGroup.appendChild(centerText);

    // Draw skill nodes
    data.forEach((skill, index) => {
      const angle = index * angleStep - Math.PI / 2;
      const skillX = centerX + radius * Math.cos(angle);
      const skillY = centerY + radius * Math.sin(angle);
      
      // Calculate node size based on skill value (min 15, max 35)
      const skillValue = Number(skill.value) || 0;
      const normalizedValue = Math.max(0, Math.min(1, skillValue / maxValue));
      const nodeRadius = 15 + (normalizedValue * 20);

      // Calculate color based on skill value
      let nodeColor;
      if (normalizedValue >= 0.8) {
        nodeColor = theme.palette.success.main;
      } else if (normalizedValue >= 0.6) {
        nodeColor = theme.palette.info.main;
      } else if (normalizedValue >= 0.4) {
        nodeColor = theme.palette.warning.main;
      } else {
        nodeColor = theme.palette.error.light;
      }

      // Create skill node circle
      const skillCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      skillCircle.setAttribute('cx', skillX);
      skillCircle.setAttribute('cy', skillY);
      skillCircle.setAttribute('r', nodeRadius);
      skillCircle.setAttribute('fill', nodeColor);
      skillCircle.setAttribute('stroke', theme.palette.background.paper || '#fff');
      skillCircle.setAttribute('stroke-width', '2');
      skillCircle.setAttribute('class', 'skill-node');
      skillCircle.setAttribute('data-skill', skill.label);
      skillCircle.setAttribute('data-value', skillValue);
      
      // Add hover effect
      skillCircle.style.cursor = 'pointer';
      skillCircle.style.transition = 'all 0.2s ease';
      
      skillCircle.addEventListener('mouseenter', () => {
        skillCircle.setAttribute('r', nodeRadius + 5);
        skillCircle.setAttribute('opacity', '0.9');
      });
      
      skillCircle.addEventListener('mouseleave', () => {
        skillCircle.setAttribute('r', nodeRadius);
        skillCircle.setAttribute('opacity', '1');
      });

      nodesGroup.appendChild(skillCircle);

      // Skill label (positioned outside the node)
      const labelDistance = nodeRadius + 25;
      const labelX = centerX + (radius + labelDistance) * Math.cos(angle);
      const labelY = centerY + (radius + labelDistance) * Math.sin(angle);

      const skillLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      skillLabel.setAttribute('x', labelX);
      skillLabel.setAttribute('y', labelY);
      skillLabel.setAttribute('text-anchor', angle > -Math.PI / 2 && angle < Math.PI / 2 ? 'start' : 'end');
      skillLabel.setAttribute('dominant-baseline', 'middle');
      skillLabel.setAttribute('fill', theme.palette.text.primary);
      skillLabel.setAttribute('font-size', '12');
      skillLabel.setAttribute('font-weight', '500');
      
      // Truncate long labels
      const labelText = skill.label.length > 15 ? skill.label.substring(0, 15) + '...' : skill.label;
      skillLabel.textContent = labelText;
      
      labelsGroup.appendChild(skillLabel);

      // Skill value label (inside or near the node)
      const valueLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      valueLabel.setAttribute('x', skillX);
      valueLabel.setAttribute('y', skillY);
      valueLabel.setAttribute('text-anchor', 'middle');
      valueLabel.setAttribute('dominant-baseline', 'middle');
      valueLabel.setAttribute('fill', theme.palette.background.paper || '#fff');
      valueLabel.setAttribute('font-size', '11');
      valueLabel.setAttribute('font-weight', 'bold');
      valueLabel.textContent = Math.round(normalizedValue * 100);
      labelsGroup.appendChild(valueLabel);
    });

    // Append groups in order (edges, nodes, labels)
    svg.appendChild(edgesGroup);
    svg.appendChild(nodesGroup);
    svg.appendChild(labelsGroup);

  }, [data, maxValue, size, centerNode, loading, error, theme]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: size }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: size }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: size }}>
        <Typography color="text.secondary">No data available</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {title && (
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, textAlign: 'center' }}>
          {title}
        </Typography>
      )}
      <Box
        sx={{
          width: size,
          height: size,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
          backgroundColor: theme.palette.background.default,
        }}
      >
        <svg
          ref={svgRef}
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ overflow: 'visible' }}
        />
      </Box>
      {/* Legend */}
      <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: theme.palette.success.main,
            }}
          />
          <Typography variant="caption">High (80-100%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: theme.palette.info.main,
            }}
          />
          <Typography variant="caption">Medium (60-80%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: theme.palette.warning.main,
            }}
          />
          <Typography variant="caption">Low (40-60%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: theme.palette.error.light,
            }}
          />
          <Typography variant="caption">Very Low (&lt;40%)</Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default NetworkGraph;

