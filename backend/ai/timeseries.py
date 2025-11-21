"""
Time-series analysis for Skill DNA - Skill Evolution Forecasting
Predicts skill trends, identifies emerging skills, and mutation risks
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class SkillEvolutionAnalyzer:
    """
    Analyzes temporal skill patterns to predict future trends
    Identifies emerging skills ("mutations") and declining skills ("extinction")
    """

    def __init__(self, evolution_df: pd.DataFrame):
        """
        Initialize with skill evolution data (year x skill x popularity)
        """
        self.evolution_df = evolution_df
        self.skills = evolution_df['skill'].unique()
        # Category column is optional - add default if missing
        if 'category' not in evolution_df.columns:
            evolution_df['category'] = 'General'
        self.categories = evolution_df['category'].unique()
        self.years = sorted(evolution_df['year'].unique())

    def calculate_growth_rate(self, skill: str, window: int = 3) -> Dict[str, float]:
        """
        Calculate skill growth rate over recent years
        Uses linear regression on recent window
        """
        skill_data = self.evolution_df[self.evolution_df['skill'] == skill].sort_values('year')

        if len(skill_data) < window:
            return {"growth_rate": 0.0, "current_popularity": 0.0, "trend": "stable"}

        # Recent window
        recent_data = skill_data.tail(window)
        X = recent_data['year'].values.reshape(-1, 1)
        y = recent_data['popularity'].values

        # Linear regression
        model = LinearRegression()
        model.fit(X, y)

        growth_rate = float(model.coef_[0])
        current_popularity = float(skill_data.iloc[-1]['popularity'])

        # Classify trend
        if growth_rate > 5:
            trend = "explosive"
        elif growth_rate > 1:
            trend = "growing"
        elif growth_rate > -1:
            trend = "stable"
        elif growth_rate > -5:
            trend = "declining"
        else:
            trend = "dying"

        return {
            "growth_rate": round(growth_rate, 2),
            "current_popularity": round(current_popularity, 1),
            "trend": trend
        }

    def forecast_skill(self, skill: str, forecast_years: int = 2) -> List[Dict[str, Any]]:
        """
        Forecast future skill popularity using polynomial regression
        """
        skill_data = self.evolution_df[self.evolution_df['skill'] == skill].sort_values('year')

        X = skill_data['year'].values.reshape(-1, 1)
        y = skill_data['popularity'].values

        # Polynomial regression (degree 2 for smooth curves)
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        # Forecast
        future_years = np.arange(self.years[-1] + 1, self.years[-1] + forecast_years + 1).reshape(-1, 1)
        future_X_poly = poly.transform(future_years)
        predictions = model.predict(future_X_poly)

        # Ensure predictions are non-negative
        predictions = np.maximum(predictions, 0)

        forecast = []
        for year, pred in zip(future_years.flatten(), predictions):
            forecast.append({
                "year": int(year),
                "predicted_popularity": round(float(pred), 1),
                "confidence": "medium"  # Placeholder
            })

        return forecast

    def identify_mutations(self, threshold_growth: float = 10.0) -> List[Dict[str, Any]]:
        """
        Identify "skill mutations" - rapidly emerging skills
        """
        mutations = []

        for skill in self.skills:
            growth_info = self.calculate_growth_rate(skill, window=3)

            if growth_info['growth_rate'] > threshold_growth:
                skill_category = self.evolution_df[self.evolution_df['skill'] == skill]['category'].iloc[0]

                mutations.append({
                    "skill": skill,
                    "category": skill_category,
                    "growth_rate": growth_info['growth_rate'],
                    "current_popularity": growth_info['current_popularity'],
                    "mutation_type": "emerging",
                    "urgency": "high" if growth_info['growth_rate'] > 20 else "medium"
                })

        # Sort by growth rate
        mutations = sorted(mutations, key=lambda x: x['growth_rate'], reverse=True)
        return mutations

    def identify_extinction_risks(self, threshold_decline: float = -5.0) -> List[Dict[str, Any]]:
        """
        Identify skills at risk of becoming obsolete
        """
        extinctions = []

        for skill in self.skills:
            growth_info = self.calculate_growth_rate(skill, window=3)

            if growth_info['growth_rate'] < threshold_decline:
                skill_category = self.evolution_df[self.evolution_df['skill'] == skill]['category'].iloc[0]

                extinctions.append({
                    "skill": skill,
                    "category": skill_category,
                    "decline_rate": growth_info['growth_rate'],
                    "current_popularity": growth_info['current_popularity'],
                    "risk_level": "critical" if growth_info['growth_rate'] < -10 else "high"
                })

        # Sort by decline rate
        extinctions = sorted(extinctions, key=lambda x: x['decline_rate'])
        return extinctions

    def analyze_category_trends(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze trends by skill category (legacy, cloud, e-mobility, AI)
        """
        category_trends = {}

        for category in self.categories:
            category_data = self.evolution_df[self.evolution_df['category'] == category]

            # Average popularity over time
            yearly_avg = category_data.groupby('year')['popularity'].mean()

            # Recent trend (last 3 years)
            recent_years = yearly_avg.tail(3)
            X = np.array(recent_years.index).reshape(-1, 1)
            y = recent_years.values

            model = LinearRegression()
            model.fit(X, y)

            growth_rate = float(model.coef_[0])
            current_avg = float(yearly_avg.iloc[-1])

            # Classify category health
            if growth_rate > 5:
                health = "thriving"
            elif growth_rate > 0:
                health = "growing"
            elif growth_rate > -5:
                health = "stable"
            else:
                health = "declining"

            category_trends[category] = {
                "growth_rate": round(growth_rate, 2),
                "current_avg_popularity": round(current_avg, 1),
                "health": health,
                "skills_count": int(len(category_data['skill'].unique()))
            }

        return category_trends

    def generate_evolution_chart_data(self) -> List[Dict[str, Any]]:
        """
        Generate data for frontend Recharts evolution timeline
        Replaces EVOLUTION_DATA in constants.ts

        Aggregates skills by category for clean visualization:
        - legacy_engineering → Legacy
        - software_cloud → Software
        - e_mobility → EV
        - ai_emerging → AI
        """
        # Category name mapping for frontend
        category_map = {
            'legacy_engineering': 'Legacy',
            'software_cloud': 'Software',
            'e_mobility': 'EV',
            'ai_emerging': 'AI'
        }

        chart_data = []

        for year in self.years:
            year_data = {"year": int(year)}  # Convert numpy int to Python int

            # Get all skills for this year
            year_df = self.evolution_df[self.evolution_df['year'] == year]

            # Aggregate by category (average popularity of skills in each category)
            for db_category, frontend_category in category_map.items():
                category_skills = year_df[year_df['category'] == db_category]

                if len(category_skills) > 0:
                    # Average popularity across all skills in this category
                    avg_popularity = float(category_skills['popularity'].mean())
                    year_data[frontend_category] = round(avg_popularity, 1)
                else:
                    year_data[frontend_category] = 0.0

            chart_data.append(year_data)

        return chart_data

    def calculate_mutation_risk_score(self, skill: str) -> float:
        """
        Calculate "mutation risk" - likelihood of skill becoming obsolete
        Based on: trend, volatility, category health
        """
        growth_info = self.calculate_growth_rate(skill)
        skill_category = self.evolution_df[self.evolution_df['skill'] == skill]['category'].iloc[0]
        category_trends = self.analyze_category_trends()

        # Components of risk score
        trend_risk = max(0, -growth_info['growth_rate'] / 10)  # Declining = higher risk
        category_risk = 1.0 if category_trends[skill_category]['health'] == 'declining' else 0.3

        # Volatility (standard deviation of popularity)
        skill_data = self.evolution_df[self.evolution_df['skill'] == skill]
        volatility = skill_data['popularity'].std()
        volatility_risk = min(1.0, volatility / 50)

        # Combine (weighted average)
        risk_score = (0.5 * trend_risk) + (0.3 * category_risk) + (0.2 * volatility_risk)
        return round(min(1.0, risk_score), 2)

    def calculate_forecast_accuracy(self, skill: str, test_years: int = 2) -> Dict[str, Any]:
        """
        Calculate forecast accuracy (MAPE, RMSE) using backtesting
        Trains on historical data, predicts recent years, compares to actuals

        Args:
            skill: Skill name to evaluate
            test_years: Number of recent years to use for testing (default: 2)

        Returns:
            {
                'mape': Mean Absolute Percentage Error (lower is better),
                'rmse': Root Mean Squared Error (lower is better),
                'test_years': Number of years tested,
                'comparison': [{year, actual, predicted, error, error_percent}],
                'accuracy_grade': 'Excellent' | 'Good' | 'Acceptable' | 'Poor' | 'Very Poor'
            }
        """
        skill_data = self.evolution_df[self.evolution_df['skill'] == skill].sort_values('year')

        if len(skill_data) < 4:  # Need at least 4 years for meaningful backtest
            return {
                "mape": None,
                "rmse": None,
                "test_years": 0,
                "comparison": [],
                "accuracy_grade": "Unknown",
                "error": "Insufficient data for accuracy calculation (need 4+ years)"
            }

        # Limit test_years to available data
        max_test_years = len(skill_data) - 2  # Keep at least 2 years for training
        test_years = min(test_years, max_test_years)

        # Split: train on all but last test_years, predict those years
        train_data = skill_data.iloc[:-test_years]
        test_data = skill_data.iloc[-test_years:]

        X_train = train_data['year'].values.reshape(-1, 1)
        y_train = train_data['popularity'].values

        X_test = test_data['year'].values.reshape(-1, 1)
        y_test = test_data['popularity'].values

        # Train polynomial model
        poly = PolynomialFeatures(degree=2)
        X_train_poly = poly.fit_transform(X_train)
        X_test_poly = poly.transform(X_test)

        model = LinearRegression()
        model.fit(X_train_poly, y_train)

        # Predict
        predictions = model.predict(X_test_poly)
        predictions = np.maximum(predictions, 0)  # Non-negative

        # Calculate MAPE (Mean Absolute Percentage Error)
        # MAPE = mean(|actual - predicted| / actual) * 100
        mape_values = []
        for actual, pred in zip(y_test, predictions):
            if actual > 0:  # Avoid division by zero
                mape_values.append(abs(actual - pred) / actual)

        mape = np.mean(mape_values) * 100 if mape_values else None

        # Calculate RMSE (Root Mean Squared Error)
        rmse = np.sqrt(np.mean((y_test - predictions) ** 2))

        # Generate detailed comparison
        comparison = []
        for year, actual, pred in zip(test_data['year'].values, y_test, predictions):
            error_pct = round(float(abs(actual - pred) / actual * 100), 1) if actual > 0 else None
            comparison.append({
                "year": int(year),
                "actual": round(float(actual), 1),
                "predicted": round(float(pred), 1),
                "error": round(float(actual - pred), 1),
                "error_percent": error_pct
            })

        return {
            "mape": round(float(mape), 2) if mape is not None else None,
            "rmse": round(float(rmse), 2),
            "test_years": test_years,
            "comparison": comparison,
            "accuracy_grade": self._grade_accuracy(mape) if mape is not None else "Unknown"
        }

    def _grade_accuracy(self, mape: float) -> str:
        """
        Grade forecast accuracy based on MAPE

        MAPE Thresholds:
        - < 5%: Excellent (highly accurate forecasts)
        - 5-10%: Good (reliable for planning)
        - 10-20%: Acceptable (useful with caution)
        - 20-30%: Poor (high uncertainty)
        - > 30%: Very Poor (unreliable)
        """
        if mape < 5:
            return "Excellent"
        elif mape < 10:
            return "Good"
        elif mape < 20:
            return "Acceptable"
        elif mape < 30:
            return "Poor"
        else:
            return "Very Poor"

    def generate_strategic_insights(self) -> Dict[str, Any]:
        """
        Generate strategic HR insights for managers
        """
        mutations = self.identify_mutations(threshold_growth=10.0)
        extinctions = self.identify_extinction_risks(threshold_decline=-5.0)
        category_trends = self.analyze_category_trends()

        # Identify priority upskilling areas
        upskilling_priorities = []
        for mutation in mutations[:5]:  # Top 5 emerging skills
            upskilling_priorities.append({
                "skill": mutation['skill'],
                "reason": f"Explosive growth: +{mutation['growth_rate']}%/year",
                "urgency": mutation['urgency'],
                "category": mutation['category']
            })

        # Identify skills to phase out
        phase_out = []
        for extinction in extinctions[:5]:  # Top 5 declining skills
            phase_out.append({
                "skill": extinction['skill'],
                "reason": f"Declining: {extinction['decline_rate']}%/year",
                "risk_level": extinction['risk_level'],
                "category": extinction['category']
            })

        return {
            "emerging_skills": mutations[:10],
            "declining_skills": extinctions[:10],
            "category_health": category_trends,
            "upskilling_priorities": upskilling_priorities,
            "phase_out_recommendations": phase_out,
            "summary": {
                "high_growth_skills": int(len([m for m in mutations if m['urgency'] == 'high'])),
                "critical_risks": int(len([e for e in extinctions if e['risk_level'] == 'critical'])),
                "thriving_categories": int(len([c for c, v in category_trends.items() if v['health'] == 'thriving']))
            }
        }


def analyze_skill_evolution(evolution_csv_path: str) -> Dict[str, Any]:
    """
    Main time-series analysis pipeline
    """
    # Load data
    evolution_df = pd.read_csv(evolution_csv_path)

    # Initialize analyzer
    analyzer = SkillEvolutionAnalyzer(evolution_df)

    # Run all analyses
    results = {
        "evolution_chart_data": analyzer.generate_evolution_chart_data(),
        "strategic_insights": analyzer.generate_strategic_insights(),
        "category_trends": analyzer.analyze_category_trends(),
        "forecasts": {},
        "mutation_risks": {}
    }

    # Generate forecasts for top skills
    top_skills = evolution_df.groupby('skill')['popularity'].max().nlargest(10).index
    for skill in top_skills:
        results["forecasts"][skill] = analyzer.forecast_skill(skill, forecast_years=2)
        results["mutation_risks"][skill] = analyzer.calculate_mutation_risk_score(skill)

    return results


if __name__ == "__main__":
    # Test with synthetic data
    import sys
    sys.path.append('..')

    from data.synthetic_data import save_synthetic_data

    # Generate synthetic data
    print("🧬 Generating synthetic Škoda employee data...")
    save_synthetic_data()

    # Run time-series analysis
    print("\n[TIME]  Running skill evolution analysis...")
    results = analyze_skill_evolution("data/skill_evolution.csv")

    print("\n[OK] Analysis Complete!")
    print(f"\n📈 Strategic Insights:")
    insights = results['strategic_insights']
    print(f"   🚀 Emerging skills: {len(insights['emerging_skills'])}")
    print(f"   [WARN]  Declining skills: {len(insights['declining_skills'])}")
    print(f"   💪 Thriving categories: {insights['summary']['thriving_categories']}")

    print(f"\n🔥 Top 3 Mutations:")
    for mutation in insights['emerging_skills'][:3]:
        print(f"   - {mutation['skill']}: +{mutation['growth_rate']}%/year")

    print(f"\n[WARN]  Top 3 Extinction Risks:")
    for extinction in insights['declining_skills'][:3]:
        print(f"   - {extinction['skill']}: {extinction['decline_rate']}%/year")
