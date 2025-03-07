# Opta Betting System

A system for collecting football match predictions from Opta and comparing them with odds from Unibet to identify value betting opportunities.

## Project Overview

This system works by:
1. Scraping Opta predictions for upcoming football matches
2. Scraping current odds from Unibet
3. Matching games between the two sources
4. Analyzing differences between predicted and implied probabilities
5. Generating recommended bets based on value and confidence
6. Sending email notifications with betting recommendations

## File Structure

- `main.py` - Main script that orchestrates the entire process
- `opta_scraper.py` - Scrapes predictions from Opta
- `unibet_scraper.py` - Scrapes odds from Unibet
- `match_data.py` - Matches games between data sources and analyzes value
- `team_mappings.py` - Handles team name variations between different sources
- `betting_utils.py` - Utilities for bet evaluation and confidence scoring
- `email_utils.py` - Email notification functions
- `script_utils.py` - Utilities for running scripts and verifying data
- `opta_predictions.csv` - Stores scraped Opta predictions
- `unibet_predictions.csv` - Stores scraped Unibet odds
- `matched_predictions.csv` - Stores matched and analyzed betting opportunities

## How to Use

### Complete Process

To run the complete process (scraping + analysis + recommendations):

```
python main.py
```

This will:
1. Run the Opta scraper to collect match predictions
2. Run the Unibet scraper to collect current odds
3. Match the games between the two sources
4. Calculate value and confidence scores for betting opportunities
5. Display recommended bets sorted from best to worst

### With Email Notifications

To run the process and receive email notifications with the recommendations:

```
python main.py --email --to_email your.email@example.com
```

Alternatively, set the environment variables before running:
```
set GMAIL_USER=your_gmail@gmail.com
set GMAIL_APP_PASSWORD=your_app_password_here
set TO_EMAIL=your.email@example.com
python main.py --email
```

Note: For Gmail, you need to use an App Password, not your regular account password. You can create one in your Google Account security settings.

### Running Individual Components

If you want to run just the scrapers or just the analysis:

```
# Only run Opta scraper
python opta_scraper.py

# Only run Unibet scraper
python unibet_scraper.py

# Only run matching and analysis (if CSVs already exist)
python main.py --skip_scrapers
```

### Automated Scheduling

The system can be scheduled to run automatically:

#### Using GitHub Actions (Recommended)

1. Push your code to a GitHub repository
2. The included `.github/workflows/betting-schedule.yml` file will run the system every 2 days at 9:00 AM UTC
3. Set up the following repository secrets in GitHub:
   - `GMAIL_USER`: Your Gmail address
   - `GMAIL_APP_PASSWORD`: Your Gmail app password
   - `TO_EMAIL`: Email address to receive recommendations

#### Using Windows Task Scheduler

1. Edit the `run_betting_system.bat` file with your email credentials
2. Create a scheduled task in Windows Task Scheduler that runs this batch file

## Understanding the Output

For each recommended bet, the system provides:

- **Match and Bet Type**: Team names and bet type (Home Win/Draw/Away Win)
- **Odds**: Decimal odds from Unibet
- **Implied Probability**: The probability implied by the betting odds
- **Opta Probability**: The probability predicted by Opta
- **Edge**: The difference between Opta's probability and the implied probability
- **Expected Profit**: Expected return per €1 bet
- **Confidence Score**: A score from 0-100 that considers probability, edge, and expected return
- **Rating**: A star rating and category (Excellent, Very Good, Good, Speculative, Low Confidence)

Example:
```
1. Bet on Away Win in Bayern München vs Bochum
   Odds: 23.00
   Implied probability: 4.35%
   Opta probability: 8.70%
   Edge: +4.35%
   Expected profit per €1 bet: €1.00
   Confidence Score: 58.7/100 - ⭐⭐⭐ GOOD
```

## Confidence Score Formula

The confidence score is calculated using this formula:

```
confidence_score = ((prob_decimal * 0.3) + 
                   (normalized_edge * 0.3) + 
                   (normalized_return * 0.4) +
                   prob_bonus) * 100
```

Where:
- `prob_decimal` is the predicted probability as a decimal (0-1)
- `normalized_edge` is the betting edge normalized to a 0-1 scale
- `normalized_return` is the expected return normalized to a 0-1 scale
- `prob_bonus` is 0.1 for high probability bets (>40%), otherwise 0

This balances short-term reliability (edge) with long-term value (expected return).

## Confidence Score Categories

The system rates bets in these categories:

- ⭐⭐⭐⭐⭐ **EXCELLENT** (80-100): High confidence, strong value
- ⭐⭐⭐⭐ **VERY GOOD** (60-79): Good confidence, good value
- ⭐⭐⭐ **GOOD** (40-59): Decent confidence, positive value
- ⭐⭐ **SPECULATIVE** (20-39): Lower confidence but potential value
- ⭐ **LOW CONFIDENCE** (0-19): Risky with minimal edge

## Error Handling

The system includes comprehensive error handling:
- Validates all input data before processing
- Provides detailed error messages in the console
- When using email notifications, sends error reports with detailed information if any part of the process fails

## Requirements

- Python 3.7+
- Required packages (included in `requirements.txt`):
  - pandas
  - selenium (with ChromeDriver)
  - undetected_chromedriver
  - beautifulsoup4
  - webdriver-manager
  
## Note About Web Scraping

The scraping components (opta_scraper.py and unibet_scraper.py) may need occasional updates if the websites change their structure. The ChromeDriver version should also be kept compatible with your Chrome browser version.