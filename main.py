import time
import pandas as pd
import os
import argparse
import traceback
from datetime import datetime

# Import utility modules
from script_utils import run_script, verify_data
from betting_utils import analyze_match_data
from email_utils import send_email, format_bets_as_html, get_rating_description, format_error_as_html

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Opta betting system')
    parser.add_argument('--email', action='store_true', help='Send email with recommendations')
    parser.add_argument('--to_email', type=str, help='Email address to send recommendations to')
    parser.add_argument('--skip_scrapers', action='store_true', help='Skip scraping steps, just analyze existing data')
    args = parser.parse_args()
    
    # Get email credentials from environment variables if emailing is enabled
    gmail_user = os.environ.get('GMAIL_USER', '')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD', '')
    to_email = args.to_email or os.environ.get('TO_EMAIL', '')
    
    # Track if we encounter any errors
    error_encountered = False
    error_message = ""
    error_traceback = ""
    
    try:
        if args.email and (not gmail_user or not gmail_password or not to_email):
            error_encountered = True
            error_message = "Email credentials missing. Please set GMAIL_USER, GMAIL_APP_PASSWORD and TO_EMAIL environment variables."
            print(error_message)
            print("You can also provide the recipient email with --to_email option")
            return
        
        print("Starting betting odds collection and analysis process...")
        
        if not args.skip_scrapers:
            # Run Opta scraper to get predictions
            print("\nRunning Opta scraper...")
            if not run_script('opta_scraper.py', 'Opta predictions scraper'):
                error_encountered = True
                error_message = "Failed to get Opta predictions."
                print(f"{error_message} Stopping process.")
                raise Exception(error_message)
                
            # Run Unibet scraper to get current odds
            print("\nWaiting 5 seconds before running Unibet scraper...")
            time.sleep(5)  # Small delay between scraping operations
            
            if not run_script('unibet_scraper.py', 'Unibet odds scraper'):
                error_encountered = True
                error_message = "Failed to get Unibet odds."
                print(f"{error_message} Stopping process.")
                raise Exception(error_message)
        else:
            print("Skipping scraping steps as requested...")
        
        # Verify Opta data
        if not verify_data('opta_predictions.csv'):
            error_encountered = True
            error_message = "Opta predictions data verification failed."
            print(f"{error_message} Stopping process.")
            raise Exception(error_message)
        
        # Verify Unibet data
        if not verify_data('unibet_predictions.csv'):
            error_encountered = True
            error_message = "Unibet odds data verification failed."
            print(f"{error_message} Stopping process.")
            raise Exception(error_message)
        
        # Run match data analysis
        print("\nRunning match analysis...")
        if not run_script('match_data.py', 'Match analysis'):
            error_encountered = True
            error_message = "Failed to complete match analysis."
            print(error_message)
            raise Exception(error_message)
        
        # Verify final output
        if not verify_data('matched_predictions.csv'):
            error_encountered = True
            error_message = "Process completed but no matched predictions were generated."
            print(error_message)
            if args.email:
                email_body = format_error_as_html(error_message)
                subject = f"⚠️ Opta Betting System - No Matches Found - {datetime.now().strftime('%Y-%m-%d')}"
                send_email(subject, email_body, to_email, gmail_user, gmail_password)
            return
        
        print("\nProcess completed successfully!")
        # Display summary of results
        try:
            # Load matched predictions
            df = pd.read_csv('matched_predictions.csv')
            print(f"\nFound {len(df)} matches with betting opportunities")
            print("\nSample of opportunities:")
            print(df[['home_team', 'away_team', 'prob_difference_home', 'prob_difference_draw', 'prob_difference_away']].head())
            
            # Analyze the data and get betting recommendations
            threshold = 2.0
            sorted_bets = analyze_match_data(df, threshold)
            
            # Display the recommendations
            print("\n📊 RECOMMENDED BETS (BEST TO WORST) 📊")
            print("=" * 80)
            
            if not sorted_bets:
                print("No bets meeting the threshold criteria were found.")
                
                if args.email:
                    no_bets_message = "The system ran successfully, but no betting opportunities meeting the threshold criteria were found."
                    email_body = format_error_as_html(no_bets_message)
                    subject = f"Opta Betting System - No Bets Found - {datetime.now().strftime('%Y-%m-%d')}"
                    send_email(subject, email_body, to_email, gmail_user, gmail_password)
                return
            
            for i, bet in enumerate(sorted_bets, 1):
                rating = get_rating_description(bet['confidence_score'])
                
                print(f"{i}. Bet on {bet['bet_type']} in {bet['match']}")
                print(f"   Odds: {bet['odds']:.2f}")
                print(f"   Implied probability: {bet['implied_prob']:.2f}%")
                print(f"   Opta probability: {bet['opta_prob']:.2f}%")
                print(f"   Edge: +{bet['difference']:.2f}%")
                print(f"   Expected profit per €1 bet: €{bet['expected_return']:.2f}")
                print(f"   Confidence Score: {bet['confidence_score']}/100 - {rating}")
                print()
            
            # Send email with recommendations if requested
            if args.email:
                today = datetime.now().strftime("%Y-%m-%d")
                subject = f"Opta Betting Recommendations - {today}"
                email_body = format_bets_as_html(sorted_bets)
                
                print(f"Sending email to {to_email}...")
                send_email(subject, email_body, to_email, gmail_user, gmail_password)
                
        except Exception as e:
            error_encountered = True
            error_message = f"Error displaying results summary: {str(e)}"
            error_traceback = traceback.format_exc()
            print(error_message)
            print(error_traceback)
            
            if args.email:
                email_body = format_error_as_html(error_message, error_traceback)
                subject = f"⚠️ Opta Betting System Error - {datetime.now().strftime('%Y-%m-%d')}"
                send_email(subject, email_body, to_email, gmail_user, gmail_password)
    
    except Exception as e:
        error_encountered = True
        if not error_message:  # If we haven't already set an error message
            error_message = f"Unexpected error: {str(e)}"
        error_traceback = traceback.format_exc()
        print(error_message)
        print(error_traceback)
        
        if args.email:
            email_body = format_error_as_html(error_message, error_traceback)
            subject = f"⚠️ Opta Betting System Error - {datetime.now().strftime('%Y-%m-%d')}"
            send_email(subject, email_body, to_email, gmail_user, gmail_password)
    
    finally:
        if error_encountered:
            print("\n⚠️ Process completed with errors. See above for details.")
            if args.email:
                print(f"Error information was sent to {to_email}")
        else:
            print("\nProcess completed successfully!")

if __name__ == "__main__":
    main()