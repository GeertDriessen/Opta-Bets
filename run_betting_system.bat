@echo off
echo Running Opta Betting System...
cd /d "c:\Users\GeertDriessen\OneDrive - Pipple BV (1)\Documents\Opta Bets"

:: Set environment variables for email (replace with your own values)
set GMAIL_USER=your_email@gmail.com
set GMAIL_APP_PASSWORD=your_app_password_here
set TO_EMAIL=your_recipient_email@example.com

:: Run the Python script with email option
python main.py --email

echo Process completed
pause