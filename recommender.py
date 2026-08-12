
"""
recommender.py
---------------
Simple fund recommender: input risk appetite, output top 3 funds by Sharpe ratio
within matching risk_grade.
"""
import pandas as pd
def recommend_funds(risk_appetite, perf_path="07_scheme_performance_cleaned.csv"):
    """
    risk_appetite: 'Low', 'Moderate', or 'High'
    Returns top 3 funds by Sharpe ratio within matching risk_grade.
    """
    perf = pd.read_csv(perf_path)
    risk_map = {"Low": ["Low"],"Moderate": ["Moderate", "Moderately High"],"High": ["High", "Very High"],   }
    if risk_appetite not in risk_map:
        raise ValueError("risk_appetite must be 'Low', 'Moderate', or 'High'")
    matched = perf[perf["risk_grade"].isin(risk_map[risk_appetite])]
    top3 = matched.sort_values("sharpe_ratio", ascending=False).head(3)
    print(f"\nTop 3 funds for '{risk_appetite}' risk appetite:\n")
    print(top3[["scheme_name", "fund_house", "risk_grade", "sharpe_ratio", "return_3yr_pct"]].to_string(index=False))
    return top3
if __name__ == "__main__":
    for appetite in ["Low", "Moderate", "High"]:
        recommend_funds(appetite)
