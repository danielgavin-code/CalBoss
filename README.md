**📅 CalBoss: Command-Line Calendar Power Tool ✨**

CalBoss is your personal calendar assistant for the terminal.
It integrates with Google Calendar to help you plan, schedule, and celebrate — all from your command line.
The fun feature added is catchup tool to allow you put reminders to reconnect with friends at the command prompt.

**💼 What It Can Do:**

* ⏰ View today's schedule or your whole week
* 📝 Add events with optional reminders, locations, and repeat settings
* 🎂 Track birthdays (and show them grouped by month)
* 🧑‍🤝‍🧑 Suggest when to check in with friends you’ve lost touch with (Catch-Up Mode!)
* 🗑️ Delete events by ID
* 🔍 Search your calendar by keyword (coming soon)


<pre>CalBoss: Google calendar integration for the command line. 📅 ✨ 

Usage: CalBoss
  [options]

📆 Event Management:
  --today Show today's schedule.
  --week View full Monday–Sunday overview.
  --add "<event>" Add an event (e.g. "Call with Chris at 1PM").
  --date YYYY-MM-DD Set date for event (required with --add).
  --starttime HH:MM Start time (24hr or AM/PM).
  --endtime HH:MM End time (24hr or AM/PM).
  --allday All day event.
  --location "<place>" Include a location with your event.
  --reminder <duration> Reminder before event (e.g. 15m, 1h).
  --remove <event_id> Delete an event by ID.
  --note <event_id> "<note>" Add a note to an existing event.
  --repeat Repeat events (e.g. daily, weekly, monthly, yearly).

🎂 Birthday:
  --bday-add "<Name> MM/DD" Add a birthday (auto-repeats yearly).
  --bday-remove "<Name>" Remove a birthday.
  --bday-show Show birthdays this month. 
  --bday-show --all Show all saved birthdays. 
      
👫 Catch-Up Mode: 
  --catchup-suggest "<Name, ...>" Suggests when to check in with each person.
  --catchup "<Name>" 
    --date YYYY-MM-DD Schedule a personal check-in. Adds a "🤖 Catch-Up" event. 
    [--reminder <time>] (Optional) Set a pre-check-in reminder. 
  --catchup-list Show upcoming catch-up events. 
  --catchup-clear "<Name>" Remove someone from your catch-up list. 
    
Examples: 
  CalBoss --today
  CalBoss --add "Coffee with Sarah" --date 2025-05-24 --starttime 14:00 --endtime 15:00 --reminder 30m
  CalBoss --bday-add "Charmaine 07/03" CalBoss --bday-show --all CalBoss --catchup-suggest "Lisa, Nick, Aunt Gina" 
    
✨ Pro Tip: 👀 Check your week every Monday. Be proactive, not reactive. </pre>



**🛠️ Requirements**

<pre>Python 3.10+
google-api-python-client
google-auth-httplib2
google-auth-oauthlib 
pytz
python-dateutil</pre>



**📦 Installation**

<pre>git clone https://github.com/danielgavin-code/CalBoss.git 
cd CalBoss pip install -r requirements.txt </pre>



**🔑 Setup Google Calendar Access**

Follow instructions to enable the Google Calendar API:
Google Calendar API Quickstart
Download your credentials.json and place it in the CalBoss/ directory
Run CalBoss once and follow the browser-based authentication flow



**🧪 Sample Workflows**

☕ Add an event:
CalBoss.py --add "Coffee with Sarah" --date 2025-06-14 --starttime 15:00 --endtime 16:00
🎂 See birthdays this month:
CalBoss.py --bday-show
🤖 Suggest catch-up schedule:
CalBoss.py --catchup-suggest "Aunt Gina, Lisa"
