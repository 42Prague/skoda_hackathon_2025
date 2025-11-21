# Mutation Risk Score Formula

## Overview

The **Mutation Risk Score** quantifies the likelihood that a skill will become obsolete or significantly diminished in value over time. This metric helps identify skills requiring immediate attention for reskilling/upskilling programs.

**Score Range**: 0.0 to 1.0 (higher = greater obsolescence risk)

## Formula Components

The mutation risk score is calculated using a weighted combination of five key components:

### 1. **Velocity** (Weight: 25%)

**Definition**: Rate of change in skill popularity (growth acceleration/deceleration)

**Calculation**:
```python
growth_rates = (popularity[t] - popularity[t-1]) / popularity[t-1]
velocity = abs(mean(diff(growth_rates)))
```

**Interpretation**:
- High velocity = Rapid changes in demand (unstable)
- Low velocity = Steady, predictable demand

---

### 2. **Volatility** (Weight: 20%)

**Definition**: Standard deviation of year-over-year growth rates

**Calculation**:
```python
volatility = std_dev(growth_rates)
```

**Interpretation**:
- High volatility = Unpredictable market demand
- Low volatility = Stable, consistent demand

---

### 3. **Market Share Loss** (Weight: 25%)

**Definition**: Decline from peak popularity

**Calculation**:
```python
market_share_loss = 1 - (current_popularity / peak_popularity)
```

**Interpretation**:
- 0.0 = At peak popularity
- 0.5 = Lost 50% from peak
- 1.0 = Completely declining

---

### 4. **Age Risk** (Weight: 15%)

**Definition**: Time since skill emerged (legacy risk factor)

**Calculation**:
```python
skill_age_years = latest_year - first_year + 1
age_risk = min(skill_age_years / 10, 1.0)
```

**Interpretation**:
- Newer skills (<3 years) = Low age risk
- Mature skills (5-7 years) = Moderate age risk
- Legacy skills (10+ years) = High age risk

---

### 5. **Recent Trend** (Weight: 15%)

**Definition**: Latest year-over-year growth direction

**Calculation**:
```python
recent_growth = (popularity[latest] - popularity[previous]) / popularity[previous]
trend_risk = 1.0 if recent_growth < -0.1 else 0.0
```

**Interpretation**:
- Declining >10%/year = Critical trend risk (1.0)
- Growing or stable = No trend risk (0.0)

---

## Final Score Calculation

```python
risk_score = (
    velocity      * 0.25 +
    volatility    * 0.20 +
    market_share_loss * 0.25 +
    age_risk      * 0.15 +
    trend_risk    * 0.15
)

# Normalize to 0-1 range
risk_score = min(max(risk_score, 0), 1)
```

---

## Risk Levels & Recommendations

| Score Range | Risk Level | Recommendation |
|-------------|-----------|---------------|
| 0.0 - 0.3   | **Low**   | Stable skill. Continue normal development programs. |
| 0.3 - 0.5   | **Medium** | Monitor emerging alternatives. Consider cross-training programs. |
| 0.5 - 0.7   | **High**   | Begin transition planning. Identify replacement skills and start reskilling. |
| 0.7 - 1.0   | **Critical** | URGENT: Rapid obsolescence detected. Immediate reskilling program required. |

---

## Example Calculations

### Example 1: Legacy CAD Software (High Risk)

**Input Data**:
- Current popularity: 12% (down from 45% peak)
- Skill age: 12 years
- Recent growth: -18% YoY
- Volatility: 0.15 (high variance)

**Component Scores**:
- Velocity: 0.22
- Volatility: 0.15
- Market Share Loss: 0.73 (lost 73% from peak)
- Age Risk: 1.0 (12 years > 10 year threshold)
- Trend Risk: 1.0 (declining >10%)

**Final Score**: `0.22*0.25 + 0.15*0.20 + 0.73*0.25 + 1.0*0.15 + 1.0*0.15 = 0.608`

**Risk Level**: **High** → Begin transition planning

---

### Example 2: Emerging AI/ML Skill (Low Risk)

**Input Data**:
- Current popularity: 32% (at peak)
- Skill age: 3 years
- Recent growth: +45% YoY
- Volatility: 0.08 (stable growth)

**Component Scores**:
- Velocity: 0.12
- Volatility: 0.08
- Market Share Loss: 0.0 (at peak)
- Age Risk: 0.3 (3/10 years)
- Trend Risk: 0.0 (growing)

**Final Score**: `0.12*0.25 + 0.08*0.20 + 0.0*0.25 + 0.3*0.15 + 0.0*0.15 = 0.091`

**Risk Level**: **Low** → Continue normal development

---

## Data Requirements

**Minimum**: 3 years of historical popularity data per skill

**Recommended**: 5+ years for accurate trend analysis

**Sources**:
- LMS completion rates
- Project assignments
- HR qualification records
- External market demand data

---

## Integration Points

**API Endpoint**: `GET /api/skill-details/{skill_name}`

**Response Format**:
```json
{
  "mutation_risk": 0.608,
  "risk_level": "High",
  "components": {
    "velocity": 0.22,
    "volatility": 0.15,
    "market_share_loss": 0.73,
    "age_risk": 1.0,
    "trend_risk": 1.0
  },
  "recommendation": "Begin transition planning. Identify replacement skills and start reskilling.",
  "metadata": {
    "current_popularity": 12,
    "peak_popularity": 45,
    "skill_age_years": 12,
    "recent_growth_rate": -0.18
  }
}
```

---

## Implementation

**Source Code**: `backend/ai/advanced_insights.py`

**Function**: `AdvancedInsightsEngine.calculate_mutation_risk_score(skill: str)`

**Caching**: Results cached per skill to optimize performance

---

## Validation & Accuracy

**Backtest Period**: 2013-2025 (12 years)

**Validation Approach**:
- Compare predicted high-risk skills (2020) vs actual obsolescence (2025)
- Expected accuracy: >80% for skills with 5+ years history

**Known Limitations**:
1. Cannot predict disruptive technology shifts (e.g., sudden AI breakthroughs)
2. Requires stable historical data (garbage in = garbage out)
3. Industry-specific factors not accounted for

---

## Future Enhancements

1. **External Market Data Integration**:
   - Job posting trends (LinkedIn, Indeed)
   - GitHub repository activity
   - StackOverflow question volume

2. **Skill Replacement Correlation**:
   - Track which emerging skills replace declining ones
   - Build skill transition graphs

3. **Industry-Specific Weighting**:
   - Different weights for automotive vs software vs manufacturing

4. **AI-Powered Anomaly Detection**:
   - Flag sudden trend shifts that don't fit historical patterns

---

## References

- **Timeseries Analysis**: `backend/ai/timeseries.py`
- **Advanced Insights**: `backend/ai/advanced_insights.py`
- **API Implementation**: `backend/api/main.py` (lines 390-391)

---

**Last Updated**: 2025-11-21
**Version**: 1.0
**Author**: Skill DNA Analytics Engine
