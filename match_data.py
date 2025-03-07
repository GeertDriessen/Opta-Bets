import pandas as pd
from datetime import datetime
import numpy as np
from team_mappings import TEAM_MAP

# Load the CSV files
opta_df = pd.read_csv('opta_predictions.csv')
unibet_df = pd.read_csv('unibet_predictions.csv')  # Changed from unibet_odds.csv to match new file name

# Mapping dictionaries
COMPETITION_MAP = {
    'UCL': 'Cha',  # Champions League matches are under 'Cha'
    'UEL': 'UEL',  # Keep Europa League separate for now
    'EPL': 'Eng',  # Premier League under 'Eng'
    'ERE': 'Ned',  # Eredivisie
    'ESP': 'Spa',  # La Liga
    'ITA': 'Ita',  # Serie A
    'GER': 'Dui',  # Bundesliga
    'FRA': 'Fra',  # Ligue 1
    'BEL': 'Bel',  # Belgian League
    'POR': 'Por',  # Portuguese League
    'BUN': 'Dui',  # Alternative code for Bundesliga
    'SEA': 'Ita',  # Alternative code for Serie A
    'LL': 'Spa',   # Alternative code for La Liga
    'LI1': 'Fra',  # Alternative code for Ligue 1
}

def convert_time_format(date_time):
    """Convert Opta's date_time format to match Unibet's"""
    try:
        # Parse "Feb 19 @ 18:45" format
        dt = datetime.strptime(date_time, '%b %d @ %H:%M')
        return dt.strftime('%H:%M')  # Return only time in HH:MM format
    except:
        return date_time

def odds_to_probabilities(odds):
    """Convert betting odds to probabilities"""
    return 1 / odds * 100

def normalize_team_name(name):
    """Normalize team name for better matching by removing common variations"""
    normalized = name.lower()
    
    # Common prefixes/suffixes to remove
    replacements = {
        'fc ': '', ' fc': '', 
        'asc ': '', ' asc': '',
        'ac ': '', ' ac': '',
        'as ': '', ' as': '',
        'ss ': '', ' ss': '',
        'cf ': '', ' cf': '',
        'united': 'utd',
        'real ': '',
        'racing ': '',
        'olympic ': '',
        'olympique ': '',
        'athletic ': '',
        'atletico ': '',
        'rc ': '',
        'afc ': '',
        'rcd ': '',
        'sd ': '',
        'ud ': '',
        'cd ': '',
        'stade ': '',
        'saint': 'st',
        'sporting ': '',
        'deportivo ': '',
        'rovers': '',
        'albion': '',
        'city': '',
        'town': '',
        ' & ': '',
        ' and ': '',
    }
    
    # Remove accents and special characters
    replacements.update({
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ñ': 'n',
        'ß': 'ss',
        'ø': 'o',
        'æ': 'ae',
        '-': ' ',
        '.': '',
    })
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Remove multiple spaces and strip
    normalized = ' '.join(normalized.split())
    return normalized.strip()

def find_team_match(team_name, df_column):
    """Find if a team name matches in the given dataframe column using more flexible matching"""
    df_column = df_column.astype(str)
    
    # First try exact mapping
    if team_name in TEAM_MAP:
        mapped_name = TEAM_MAP[team_name]
        exact_match = df_column.str.contains(mapped_name, case=False, na=False, regex=False)
        if exact_match.any():
            return exact_match
    
    # Try normalized matching for both the original and mapped name
    team_variations = [team_name]
    if team_name in TEAM_MAP:
        team_variations.append(TEAM_MAP[team_name])
    
    # Normalize all variations of team names
    normalized_variations = [normalize_team_name(v) for v in team_variations]
    normalized_column = df_column.apply(normalize_team_name)
    
    # Try to match any of the normalized variations
    return normalized_column.apply(lambda x: any(v in x or x in v for v in normalized_variations))

def find_matching_games():
    matches = []
    recommendations = []
    
    # Convert DataFrame columns to string type
    unibet_df = pd.read_csv('unibet_predictions.csv')
    for col in ['competition', 'home_team', 'away_team']:
        unibet_df[col] = unibet_df[col].astype(str)
    
    # Get available competitions for logging
    available_competitions = unibet_df['competition'].unique()
    
    # Process each Opta prediction
    for _, opta_row in opta_df.iterrows():
        # Convert competition name
        opta_comp = COMPETITION_MAP.get(opta_row['competition'], opta_row['competition'])
        
        # For Champions League games, look in both original competition and 'Cha'
        competition_matches = (unibet_df['competition'].str.contains(opta_comp, case=False, na=False))
        if opta_comp in ['Eng', 'Spa', 'Ita', 'Dui', 'Fra', 'Ned']:
            competition_matches = (
                (unibet_df['competition'] == opta_comp) | 
                (unibet_df['competition'] == 'Cha')  # Also check Champions League
            )
        
        # Get original and mapped team names
        opta_home = opta_row['home_team']
        opta_away = opta_row['away_team']
        mapped_home = TEAM_MAP.get(opta_home, opta_home)
        mapped_away = TEAM_MAP.get(opta_away, opta_away)
        
        # Filter Unibet data for matching games
        matching_games = unibet_df[
            competition_matches &
            (
                (find_team_match(mapped_home, unibet_df['home_team']) & 
                 find_team_match(mapped_away, unibet_df['away_team']))
                |
                (find_team_match(mapped_home, unibet_df['home_team'].str.split(' - ').str[0]) & 
                 find_team_match(mapped_away, unibet_df['home_team'].str.split(' - ').str[1]))
            )
        ]
        
        if not matching_games.empty:
            unibet_game = matching_games.iloc[0]
            
            # Convert odds to probabilities - handling empty or invalid odds
            try:
                unibet_home_odds = float(unibet_game['home_odds']) if pd.notna(unibet_game['home_odds']) else 0
                unibet_draw_odds = float(unibet_game['draw_odds']) if pd.notna(unibet_game['draw_odds']) else 0
                unibet_away_odds = float(unibet_game['away_odds']) if pd.notna(unibet_game['away_odds']) else 0
                
                unibet_home_prob = odds_to_probabilities(unibet_home_odds) if unibet_home_odds > 0 else 0
                unibet_draw_prob = odds_to_probabilities(unibet_draw_odds) if unibet_draw_odds > 0 else 0
                unibet_away_prob = odds_to_probabilities(unibet_away_odds) if unibet_away_odds > 0 else 0
            except (ValueError, ZeroDivisionError):
                print(f"Invalid odds for {mapped_home} vs {mapped_away}")
                continue
            
            match_data = {
                'competition': opta_comp,
                'date_time': opta_row['date_time'],
                'home_team': mapped_home,
                'away_team': mapped_away,
                'opta_home_win_%': opta_row['home_win_%'],
                'opta_draw_%': opta_row['draw_%'],
                'opta_away_win_%': opta_row['away_win_%'],
                'unibet_home_odds': unibet_home_odds,
                'unibet_draw_odds': unibet_draw_odds,
                'unibet_away_odds': unibet_away_odds,
                'unibet_home_prob_%': round(unibet_home_prob, 1),
                'unibet_draw_prob_%': round(unibet_draw_prob, 1),
                'unibet_away_prob_%': round(unibet_away_prob, 1),
                'prob_difference_home': round(opta_row['home_win_%'] - unibet_home_prob, 1),
                'prob_difference_draw': round(opta_row['draw_%'] - unibet_draw_prob, 1),
                'prob_difference_away': round(opta_row['away_win_%'] - unibet_away_prob, 1)
            }
            
            # Only add valid matches where we have both probabilities
            if all(v != 0 for v in [unibet_home_prob, unibet_draw_prob, unibet_away_prob]):
                matches.append(match_data)
                print(f"Matched: {mapped_home} vs {mapped_away} ({opta_comp})")
                
                # Add betting recommendations with more detailed odds info
                threshold = 5  # Minimum probability difference to recommend a bet
                if match_data['prob_difference_home'] > threshold:
                    recommendations.append(
                        f"Bet on {mapped_home} to win against {mapped_away} "
                        f"(Unibet odds: {unibet_home_odds:.2f}, "
                        f"Implied prob: {unibet_home_prob:.1f}%, "
                        f"Opta prob: {opta_row['home_win_%']:.1f}%)"
                    )
                if match_data['prob_difference_draw'] > threshold:
                    recommendations.append(
                        f"Bet on draw between {mapped_home} and {mapped_away} "
                        f"(Unibet odds: {unibet_draw_odds:.2f}, "
                        f"Implied prob: {unibet_draw_prob:.1f}%, "
                        f"Opta prob: {opta_row['draw_%']:.1f}%)"
                    )
                if match_data['prob_difference_away'] > threshold:
                    recommendations.append(
                        f"Bet on {mapped_away} to win against {mapped_home} "
                        f"(Unibet odds: {unibet_away_odds:.2f}, "
                        f"Implied prob: {unibet_away_prob:.1f}%, "
                        f"Opta prob: {opta_row['away_win_%']:.1f}%)"
                    )
        else:
            print(f"No match found: {mapped_home} vs {mapped_away} ({opta_comp})")
            print(f"Looking for competition containing: {opta_comp}")
            print(f"Available competitions in Unibet data: {unibet_df['competition'].unique()}")
    
    # Create DataFrame and save to CSV
    if matches:
        matched_df = pd.DataFrame(matches)
        # Sort by date_time and competition
        matched_df = matched_df.sort_values(['date_time', 'competition'])
        # Save to CSV
        matched_df.to_csv('matched_predictions.csv', index=False)
        print(f"\nSaved {len(matches)} matched games to matched_predictions.csv")
        print("\nSample of matched data:")
        print(matched_df.head())
        
        # Print summary of probability differences
        print("\nSummary of probability differences:")
        print("Average home win difference: ", round(matched_df['prob_difference_home'].mean(), 2))
        print("Average draw difference: ", round(matched_df['prob_difference_draw'].mean(), 2))
        print("Average away win difference: ", round(matched_df['prob_difference_away'].mean(), 2))
        
        # Print ranges of differences
        print("\nRanges of probability differences:")
        print("Home win difference range: ", 
              f"{round(matched_df['prob_difference_home'].min(), 2)} to {round(matched_df['prob_difference_home'].max(), 2)}")
        print("Draw difference range: ",
              f"{round(matched_df['prob_difference_draw'].min(), 2)} to {round(matched_df['prob_difference_draw'].max(), 2)}")
        print("Away win difference range: ",
              f"{round(matched_df['prob_difference_away'].min(), 2)} to {round(matched_df['prob_difference_away'].max(), 2)}")
        
        # Print betting recommendations
        if recommendations:
            print("\nBetting Recommendations:")
            for recommendation in recommendations:
                print(recommendation)
    else:
        print("No matches were found")

if __name__ == "__main__":
    print("Starting to match games...")
    find_matching_games()