import math

def calculate_implied_probability(odds):
    """Calculate the implied probability from betting odds"""
    return 1 / odds

def evaluate_bet_value(predicted_prob, implied_prob):
    """Evaluate the value of a bet based on predicted and implied probabilities"""
    return predicted_prob - implied_prob

def calculate_expected_return(odds, predicted_prob):
    """Calculate the expected return for a €1 bet"""
    # Convert percentage to decimal
    prob_decimal = predicted_prob / 100
    # Expected return = (probability * potential winnings) - (1 - probability) * stake
    return (prob_decimal * (odds - 1)) - ((1 - prob_decimal) * 1)

def calculate_confidence_score(prob, edge, expected_return):
    """Calculate a confidence score that balances edge (short-term) and expected return (long-term)
    
    - Higher probabilities get more weight (more reliable in small sample sizes)
    - Edge is weighted for short-term reliability
    - Expected return is weighted for long-term value
    
    Returns a score from 0-100 where:
    - 80-100: Excellent bet (high confidence, strong value)
    - 60-79: Very good bet (good confidence, good value)
    - 40-59: Good bet (decent confidence, positive value)
    - 20-39: Speculative bet (lower confidence but potential value)
    - 0-19: Low confidence bet (risky, minimal edge)
    """
    # Convert percentage to decimal
    prob_decimal = prob / 100
    
    # Weight factors - giving more weight to expected return
    prob_weight = 0.3   # Weight for prediction accuracy/reliability
    edge_weight = 0.3   # Weight for betting edge (short-term)
    return_weight = 0.4 # Weight for expected return (long-term)
    
    # Normalize the edge (typical range 0-10%)
    normalized_edge = min(edge / 5, 1)  # Scale reduced to increase sensitivity
    
    # Normalize expected return (typically -1 to +2 for €1 bets)
    # Scale adjusted to give higher scores for good returns
    normalized_return = (expected_return + 0.5) / 2
    normalized_return = max(0, min(normalized_return, 1))
    
    # Apply a bonus for high probability bets (more reliable in small samples)
    prob_bonus = 0
    if prob_decimal > 0.4:
        prob_bonus = 0.1
    
    # Calculate weighted score
    score = (
        (prob_decimal * prob_weight) + 
        (normalized_edge * edge_weight) + 
        (normalized_return * return_weight) +
        prob_bonus
    ) * 100
    
    return round(score, 1)

def analyze_match_data(df, threshold=2.0):
    """Analyze matched prediction data and return recommended bets
    
    Args:
        df: DataFrame with matched predictions
        threshold: Minimum edge threshold for bet recommendations (default: 2.0)
        
    Returns:
        List of recommended bets sorted by confidence score
    """
    # Calculate implied probabilities
    df['implied_prob_home'] = df['unibet_home_odds'].apply(calculate_implied_probability) * 100
    df['implied_prob_draw'] = df['unibet_draw_odds'].apply(calculate_implied_probability) * 100
    df['implied_prob_away'] = df['unibet_away_odds'].apply(calculate_implied_probability) * 100
    
    # Calculate value (edge)
    df['value_home'] = df.apply(lambda row: evaluate_bet_value(row['opta_home_win_%'], row['implied_prob_home']), axis=1)
    df['value_draw'] = df.apply(lambda row: evaluate_bet_value(row['opta_draw_%'], row['implied_prob_draw']), axis=1)
    df['value_away'] = df.apply(lambda row: evaluate_bet_value(row['opta_away_win_%'], row['implied_prob_away']), axis=1)
    
    # Calculate expected returns
    df['expected_return_home'] = df.apply(lambda row: calculate_expected_return(row['unibet_home_odds'], row['opta_home_win_%']), axis=1)
    df['expected_return_draw'] = df.apply(lambda row: calculate_expected_return(row['unibet_draw_odds'], row['opta_draw_%']), axis=1)
    df['expected_return_away'] = df.apply(lambda row: calculate_expected_return(row['unibet_away_odds'], row['opta_away_win_%']), axis=1)
    
    # Create a list of all bet opportunities
    all_bets = []
    
    for index, row in df.iterrows():
        if row['value_home'] > threshold:
            confidence_score = calculate_confidence_score(
                row['opta_home_win_%'], 
                row['value_home'], 
                row['expected_return_home']
            )
            all_bets.append({
                'match': f"{row['home_team']} vs {row['away_team']}",
                'bet_type': 'Home Win',
                'implied_prob': row['implied_prob_home'],
                'opta_prob': row['opta_home_win_%'],
                'difference': row['value_home'],
                'expected_return': row['expected_return_home'],
                'odds': row['unibet_home_odds'],
                'confidence_score': confidence_score
            })
        if row['value_draw'] > threshold:
            confidence_score = calculate_confidence_score(
                row['opta_draw_%'], 
                row['value_draw'], 
                row['expected_return_draw']
            )
            all_bets.append({
                'match': f"{row['home_team']} vs {row['away_team']}",
                'bet_type': 'Draw',
                'implied_prob': row['implied_prob_draw'],
                'opta_prob': row['opta_draw_%'],
                'difference': row['value_draw'],
                'expected_return': row['expected_return_draw'],
                'odds': row['unibet_draw_odds'],
                'confidence_score': confidence_score
            })
        if row['value_away'] > threshold:
            confidence_score = calculate_confidence_score(
                row['opta_away_win_%'], 
                row['value_away'], 
                row['expected_return_away']
            )
            all_bets.append({
                'match': f"{row['home_team']} vs {row['away_team']}",
                'bet_type': 'Away Win',
                'implied_prob': row['implied_prob_away'],
                'opta_prob': row['opta_away_win_%'],
                'difference': row['value_away'],
                'expected_return': row['expected_return_away'],
                'odds': row['unibet_away_odds'],
                'confidence_score': confidence_score
            })
    
    # Sort bets by confidence score
    return sorted(all_bets, key=lambda x: x['confidence_score'], reverse=True)