#!/usr/bin/python

#
#     Title    : CalBoss.py 
#     Version  : 1.0
#     Date     : 20 May 2025 
#     Author   : Daniel Gavin
#
#     Function : A speedy port of grep and varients zgrep and bzgrep.
#
#     Modification History
#
#     Date     : 20 May 2025 
#     Author   : Daniel Gavin
#     Changes  : New file.
#
#     Date     :
#     Author   :
#     Changes  :
#

import sys
import pytz
import pickle
import random
import os.path
import argparse

from datetime import datetime, timedelta

from googleapiclient.discovery      import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow      import InstalledAppFlow

VERSION = 'v0.1.0dev-beta'
SCOPES  = ['https://www.googleapis.com/auth/calendar.readonly']

###############################################################################
#
# Procedure   : GetCalendarService()
#
# Description : Authenticate and connect to Google Calendar API.
#             : - Use credentials.json for first-time access.
#             : - Store/refresh token in token.pickle.
#
# Input       : -none-
#
# Returns     : object - Google Calendar Service
#
###############################################################################

def GetCalendarService():

    creds = None

    # check for saved token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # if no valid token, start OAuth flow
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # save token for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


###############################################################################
#
# Procedure   : FetchTodayEvents()
#
# Description : Pulls all Google Calendar events for the current day
#             : Uses timezone-aware window from now until midnight
#
# Input       : service - Google Calendar API service object
#
# Returns     : list - all events scheduled for today
#
###############################################################################

def FetchTodayEvents(service):

    # todo - make this dynamic
    tz    = pytz.timezone("America/New_York")
    now   = datetime.now(tz)
    start = now.isoformat()
    end   = (now + timedelta(days=1)).isoformat()

    eventResult = service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    allEvents = eventResult.get('items', [])

    # chat gpt hack
    # filter to events happening *today* (EDT)
    today          = now.strftime("%Y-%m-%d")
    filteredEvents = []

    for event in allEvents:

        startTime = event['start'].get('dateTime', event['start'].get('date'))

        if today in startTime:
            filteredEvents.append(event)

    return filteredEvents


###############################################################################
#
# Procedure   : FetchWeekEvents()
#
# Description : Pulls Google Calendar events for next 7 days (today + 6).
#             : Returns dictionary grouped by date.
#
# Input       : service - Google Calendar API service object
#
# Returns     : dict - key = readable date label, value = list of events
#
###############################################################################

def FetchWeekEvents(service):

    tz    = pytz.timezone("America/New_York")
    now   = datetime.now(tz)
    start = now.isoformat()
    end   = (now + timedelta(days=7)).isoformat()

    eventResult = service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    allEvents     = eventResult.get('items', [])
    groupedEvents = {}

    for event in allEvents:

        start = event['start'].get('dateTime', event['start'].get('date'))
        dt    = datetime.fromisoformat(start) if 'T' in start else datetime.strptime(start, "%Y-%m-%d")
        dt    = dt.astimezone(tz)

        dayLabel = ""

        if dt.date() == now.date():
            dayLabel = f"Today ({dt.strftime('%b %d')})"

        elif dt.date() == (now + timedelta(days=1)).date():
            dayLabel = f"Tomorrow ({dt.strftime('%b %d')})"

        else:
            dayLabel = dt.strftime("%A (%b %d)")

        groupedEvents.setdefault(dayLabel, []).append(event)

    return groupedEvents


###############################################################################
#
# Procedure   : PrintHelp()
#
# Description : Beautified --help 
#
# Input       : -none-
#
# Returns     : -none- 
#
###############################################################################

def PrintHelp():

    proTips = [ "📅 Add your events with --date and --starttime to stay in boss mode.",
      "🔥 Repeating events? Use --repeat and never miss leg day again.",
      "🧠 Block off 'focus hours' on your calendar to actually get sh*t done.",
      "☕ Schedule your breaks. No one hustles non-stop without burning out.",
      "📍 Use event notes to track locations, URLs, or secret pizza spots.",
      "🗑️ Clear your calendar with --clear, but only if you're feeling brave.",
      "👀 Check your week every Monday. Stay ready, not reactive.",
      "🧼 Keep your backup fresh with --export — future you will thank you.",
      "💬 Add your therapist as an event. Normalize emotional maintenance.",
      "🌀 Spiral sessions are valid events. So is sexy time. #NoShame",
      "⏰ Reminders aren’t for the forgetful — they’re for the focused.",
      "📆 If it’s not in CalBoss, it’s not happening. Period."]

    helpText = """\
CalBoss: Google calendar integration for the command line.  Stay organized. 📅 ✨ 

Usage:
  CalBoss [options]

📆 Event Management:
  --today                        Show today's schedule.
  --week                         View full Monday–Sunday overview.
  --add "<event>"                Add an event (e.g. "Call with Lisa at 1PM").
  --date YYYY-MM-DD              Set date for event (required with --add).
  --starttime HH:MM              Start time (24hr or AM/PM).
  --endtime HH:MM                End time (24hr or AM/PM).
  --reminder <duration>          Reminder before event (e.g. 15m, 1h).
  --remove <event_id>            Delete an event by ID.
  --clear                        Clear today's events (asks first).
  --note <event_id> "<note>"     Add a note to an existing event.
  --repeat                       Add repeating events (e.g. weekly, monthly).

🎂 Birthday Boss Mode:
  --bday-add "<Name> MM/DD"      Add a birthday (auto-repeats yearly).
  --bday-remove "<Name>"         Remove a birthday.
  --bday-show                    Show birthdays this month.
  --bday-show --today            Show today's birthdays.
  --bday-show --week             Show birthdays in the next 7 days.
  --bday-show --all              Show all saved birthdays.

📊 Overview & Planning:
  --summary                      Show usage summary: hours booked vs free.
  --focus                        Filter for priority events only.
  --insights                     Analyze patterns (best/worst days).
  --vibe-check                   Show today’s time breakdown + free hours.

🔧 Other:
  --export                       Save all data to calboss-backup.json.
  --import <file>                Load data from a backup.
  --version                      Show CalBoss version.
  --help                         You’re looking at it.

Examples:
  CalBoss --today
  CalBoss --add "Coffee with Sarah" --date 2025-05-24 --starttime 14:00 --endtime 15:00 --reminder 30m
  CalBoss --bday-add "Charmaine 07/03"
  CalBoss --bday-show --week
  CalBoss --focus --week

✨ Pro Tip:
"""
    print(helpText + random.choice(proTips) + "\n")

###############################################################################
#
# Procedure   : ParseArgs()
#
# Description : Parses command-line arguments.
#
# Input       : -none-
#
# Returns     : object - parsed args
#
###############################################################################

def ParseArgs():

    parser = argparse.ArgumentParser(
        description="CalBoss: Google calendar integration for the command line.  Stay organized. 📅 ✨",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # core features
    parser.add_argument("--today",  action="store_true", help="Show today's schedule.")
    parser.add_argument("--week",   action="store_true", help="View full Monday–Sunday overview.")
    parser.add_argument("--add",    type=str,            help='Add an event (e.g. "Call with Lisa at 1PM").')
    parser.add_argument("--date", type=str, help="Date of event (YYYY-MM-DD)")
    parser.add_argument("--starttime", type=str, help="Start time (e.g. 13:00 or 1PM)")
    parser.add_argument("--endtime", type=str, help="End time (e.g. 14:00 or 2PM)")
    parser.add_argument("--reminder", type=str, help="Reminder before event (e.g. 15m, 1h)")
    parser.add_argument("--remove", type=int,            help="Delete an event by ID.")
    parser.add_argument("--clear",  action="store_true", help="Clear today's events (asks first).")
    parser.add_argument("--note",   nargs=2,             help='Add note to an event. Usage: --note <id> "Your note".')
    parser.add_argument("--repeat", action="store_true", help="Add repeating events (weekly, monthly).")

    # birthday support 
    parser.add_argument("--bday-add",        type=str,            help='Add a birthday (e.g. "Lisa 03/29").')
    parser.add_argument("--bday-remove",     type=str,            help="Remove a birthday by name.")
    parser.add_argument("--bday-show",       action="store_true", help="Show birthdays this month.")
    parser.add_argument("--bday-show-all",   action="store_true", help="Show all saved birthdays.")
    parser.add_argument("--bday-show-week",  action="store_true", help="Show birthdays in the next 7 days.")
    parser.add_argument("--bday-show-today", action="store_true", help="Show today's birthdays.")

    # summary 
    parser.add_argument("--summary",    action="store_true", help="Show usage summary: hours booked vs free.")
    parser.add_argument("--focus",      action="store_true", help="Filter for priority events only.")
    parser.add_argument("--insights",   action="store_true", help="Analyze patterns (best/worst days).")
    parser.add_argument("--vibe-check", action="store_true", help="Show today's time breakdown + free hours.")

    # utility
    parser.add_argument("--export",  action="store_true", help="Save all data to calboss-backup.json.")
    parser.add_argument("--import",  type=str,            help="Load data from a backup file.")
    parser.add_argument("--version", action="store_true", help="Show CalBoss version and exit.")

    # help
    parser.add_argument("--help", action="store_true", help="Show this help message and exit.")

    return parser.parse_args()


###############################################################################
#             
# Procedure   : Main()
#
# Description : Entry point.
#     
# Input       : -none-    
#             
# Returns     : -none-    
#     
###############################################################################

def Main():

    args = ParseArgs()

    if args.help:
        PrintHelp()
        return

    print("🌤️r  Fetching CalBoss command ...\n")

    if args.version:
        print("📆 CalBoss Version " + VERSION)
        return

    if args.today:

        print(f"📅  Today’s Schedule ({datetime.now().strftime('%b %d')})\n")

        service = GetCalendarService()
        events  = FetchTodayEvents(service)

        if not events:
            print("😴  No events scheduled for today.")

        else:
            for event in events:

                start     = event['start'].get('dateTime', event['start'].get('date'))
                summary   = event.get('summary', '(No Title)')
                location  = event.get('location', '')
                startTime = datetime.fromisoformat(start).strftime("%I:%M %p") if 'T' in start else "All Day"

                print(f"🕘 {startTime} - {summary}")

                if location:
                    print(f"📍 {location}")

                print()

    elif args.week:

        print(f"📆  Weekly Schedule Starting {datetime.now().strftime('%b %d')}\n")

        service    = GetCalendarService()
        weekEvents = FetchWeekEvents(service)

        if not weekEvents:
            print("😴  No events scheduled this week.")

        else:

            for day in weekEvents:

                print(f"📅  {day}")

                for event in weekEvents[day]:
                    start    = event['start'].get('dateTime', event['start'].get('date'))
                    summary  = event.get('summary', '(No Title)')
                    location = event.get('location', '')
                    timeStr  = datetime.fromisoformat(start).strftime("%I:%M %p") if 'T' in start else "All Day"

                    print(f"🕘 {timeStr} - {summary}")

                    if location:
                        print(f"📍 {location}")

                    print("")


    elif args.add:
        print("[INFO] Hello world!")

if __name__ == "__main__":
    Main()

