import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import traceback

def send_email(subject, body, to_email, gmail_user, gmail_password):
    """Send email with Gmail"""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = to_email

        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(gmail_user, gmail_password)
            smtp_server.sendmail(gmail_user, to_email, msg.as_string())
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def format_bets_as_html(bets):
    """Format betting recommendations as HTML for email"""
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { background-color: #4CAF50; color: white; padding: 10px; text-align: center; }
            .bet { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .excellent { background-color: #CCFFCC; }
            .very-good { background-color: #E6FFE6; }
            .good { background-color: #F0FFF0; }
            .speculative { background-color: #FFFAF0; }
            .low-confidence { background-color: #FFF0F0; }
            .bet-header { font-weight: bold; font-size: 18px; }
            .details { margin-left: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Opta Betting Recommendations</h1>
            <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </div>
    """
    
    for i, bet in enumerate(bets, 1):
        if bet['confidence_score'] >= 80:
            rating = "⭐⭐⭐⭐⭐ EXCELLENT"
            css_class = "excellent"
        elif bet['confidence_score'] >= 60:
            rating = "⭐⭐⭐⭐ VERY GOOD"
            css_class = "very-good"
        elif bet['confidence_score'] >= 40:
            rating = "⭐⭐⭐ GOOD"
            css_class = "good"
        elif bet['confidence_score'] >= 20:
            rating = "⭐⭐ SPECULATIVE" 
            css_class = "speculative"
        else:
            rating = "⭐ LOW CONFIDENCE"
            css_class = "low-confidence"
            
        html += f"""
        <div class="bet {css_class}">
            <div class="bet-header">{i}. Bet on {bet['bet_type']} in {bet['match']}</div>
            <div class="details">
                <p>Odds: {bet['odds']:.2f}</p>
                <p>Implied probability: {bet['implied_prob']:.2f}%</p>
                <p>Opta probability: {bet['opta_prob']:.2f}%</p>
                <p>Edge: +{bet['difference']:.2f}%</p>
                <p>Expected profit per €1 bet: €{bet['expected_return']:.2f}</p>
                <p>Confidence Score: {bet['confidence_score']}/100 - {rating}</p>
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    return html

def get_rating_description(confidence_score):
    """Get the star rating and description based on confidence score"""
    if confidence_score >= 80:
        return "⭐⭐⭐⭐⭐ EXCELLENT"
    elif confidence_score >= 60:
        return "⭐⭐⭐⭐ VERY GOOD"
    elif confidence_score >= 40:
        return "⭐⭐⭐ GOOD"
    elif confidence_score >= 20:
        return "⭐⭐ SPECULATIVE" 
    else:
        return "⭐ LOW CONFIDENCE"

def format_error_as_html(error_message, traceback_info=None):
    """Format error information as HTML for email"""
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { background-color: #FF6347; color: white; padding: 10px; text-align: center; }
            .content { margin: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #FFF0F0; }
            .error { font-weight: bold; color: #B22222; }
            .traceback { background-color: #F8F8F8; padding: 10px; font-family: monospace; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚠️ Opta Betting System Error</h1>
            <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </div>
        <div class="content">
            <h2>Error Details</h2>
            <p class="error">""" + error_message + """</p>
    """
    
    if traceback_info:
        html += f"""
            <h3>Stack Trace</h3>
            <div class="traceback">{traceback_info}</div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    return html