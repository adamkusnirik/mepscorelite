import os
import pandas as pd
from datetime import datetime
from file_utils import load_combined_dataset, load_json_auto

# Define term dates
TERM_DATES = {
    '8': ('2014-07-01', '2019-07-01'),
    '9': ('2019-07-02', '2024-07-15'),
    '10': ('2024-07-16', '2029-07-15'),
}

def calculate_score(activities: dict) -> float:
    """Calculate activity score for an MEP based on their activities."""
    # Define weights for different activities
    WEIGHTS = {
        'speeches': 1.0,
        'reports_rapporteur': 10.0,
        'reports_shadow': 5.0,
        'amendments': 1.0,
        # Add other weighted activities as needed
    }
    
    score = 0
    for activity, count in activities.items():
        score += count * WEIGHTS.get(activity, 0)
        
    return float(score)

def build_ranking(term: str, parltrack_dir: str = "data/parltrack") -> pd.DataFrame:
    """Build a ranking of MEPs for a specific term using Parltrack data."""
    if term not in TERM_DATES:
        raise ValueError(f"Invalid term: {term}. Available terms are: {', '.join(TERM_DATES.keys())}")
        
    term_start, term_end = TERM_DATES[term]
    
    # Load MEP profiles from the correct Parltrack file
    meps_data = load_json_auto(os.path.join(parltrack_dir, 'ep_meps.json'))
    activities_data = load_combined_dataset(
        os.path.join(parltrack_dir, 'ep_mep_activities.json'),
        [os.path.join(parltrack_dir, f'ep_mep_activities_term{term}.json') for term in (8, 9, 10)],
    )
        
    # Create a dictionary for activities for faster lookups
    activities_dict = {str(activity['mep_id']): activity for activity in activities_data}
    
    rows = []
    # Iterate through the list of MEPs
    for mep in meps_data:
        mep_id = str(mep.get('UserID'))
        if not mep_id:
            continue

        mep_activities = activities_dict.get(mep_id, {})
        
        # Filter activities by term dates
        speeches = len([s for s in mep_activities.get('speeches', []) if TERM_DATES[term][0] <= s.get('date', '') <= TERM_DATES[term][1]])
        reports_rapporteur = len([r for r in mep_activities.get('reports', []) if TERM_DATES[term][0] <= r.get('date', '') <= TERM_DATES[term][1]])
        
        # Assuming amendments are also in the activities file
        amendments = len([a for a in mep_activities.get('amendments', []) if TERM_DATES[term][0] <= a.get('date', '') <= TERM_DATES[term][1]])
        
        activity_counts = {
            'speeches': speeches,
            'reports_rapporteur': reports_rapporteur,
            'amendments': amendments,
            'reports_shadow': 0  # Placeholder for shadow reports
        }
        
        score = calculate_score(activity_counts)
        
        row = {
            "mep_id": mep_id,
            "full_name": mep.get('fullName', 'Unknown'),
            "country": mep.get('country', 'Unknown'),
            "group": mep.get('politicalGroup', 'Unknown'),
            "national_party": mep.get('nationalPoliticalGroup', ''),
            "speeches": speeches,
            "reports_rapporteur": reports_rapporteur,
            "amendments": amendments,
            "reports_shadow": 0,
            "score": score,
        }
        rows.append(row)
        
    df = pd.DataFrame(rows)
    
    if not df.empty:
        df = df.sort_values("score", ascending=False).reset_index(drop=True)
        df['rank'] = df.index + 1
        
    return df

def save_ranking(df: pd.DataFrame, term: str):
    """Save the ranking DataFrame to a JSON file."""
    output_dir = os.path.join('public', 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'term{term}_dataset.json')
    df.to_json(output_file, orient='records', indent=2)
    print(f"Successfully saved ranking for term {term} to {output_file}")

if __name__ == '__main__':
    for term in TERM_DATES.keys():
        print(f"Building ranking for term {term}...")
        try:
            ranking_df = build_ranking(term)
            if not ranking_df.empty:
                save_ranking(ranking_df, term)
        except Exception as e:
            print(f"Error building ranking for term {term}: {e}")
            import traceback
            traceback.print_exc() 
