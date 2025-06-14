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
#     Date     : 14 June 2025
#     Author   : Daniel Gavin
#     Changes  : Disabled the following for a future release ...  
#              : - Overview & Planning.
#              : - Other.
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

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

from googleapiclient.discovery      import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow      import InstalledAppFlow

VERSION = '1.01'
SCOPES  = ['https://www.googleapis.com/auth/calendar']

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
        calendarId   = 'primary',
        timeMin      = start,
        timeMax      = end,
        singleEvents = True,
        orderBy      = 'startTime'
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
        calendarId   = 'primary',
        timeMin      = start,
        timeMax      = end,
        singleEvents = True,
        orderBy      = 'startTime'
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

    # these came from some random inspirational website on the importance
    # of having a digital calendar ... lost the url.
    proTips = [ "📅 Add your events with --date and --starttime to stay in boss mode.",
      "🔥 Repeating events? Use --repeat and never miss it again.",
      "🧠 Block off 'focus hours' on your calendar to get sh*t done.",
      "☕ Schedule your breaks. No one hustles non-stop without burning out.",
      "📍 Use event notes to track locations, URLs, or secret food spots.",
      "👀 Check your week every Monday. Be proactive, not reactive.",
      #"🧼 Keep a backup with --export — you future self will thank you.",
      "⏰ Reminders aren’t for the forgetful — they’re for the focused.",
      "📆 If it’s not in the calendar, it’s not happening.",
      #"🔎 Use --search to find events fast — one should not have to battle a web gui.",
      #"🧠 Use --search-all to pull past and future events.",
      "🛑 Book a full day with --allday"]

    helpText = """\
CalBoss: Google calendar integration for the command line. 📅 ✨ 

Usage:
  CalBoss [options]

📆 Event Management:
  --today                          Show today's schedule.
  --week                           View full Monday–Sunday overview.
  --add "<event>"                  Add an event (e.g. "Call with Lisa at 1PM").
  --date YYYY-MM-DD                Set date for event (required with --add).
  --starttime HH:MM                Start time (24hr or AM/PM).
  --endtime HH:MM                  End time (24hr or AM/PM).
  --allday                         All day event. 
  --location "<place>"             Include a location with your event.
  --reminder <duration>            Reminder before event (e.g. 15m, 1h).
  --remove <event_id>              Delete an event by ID.
  --note <event_id> "<note>"       Add a note to an existing event.
  --repeat                         Repeat events (e.g. daily, weekly, monthly, yearly).

🎂 Birthday:
  --bday-add "<Name> MM/DD"        Add a birthday (auto-repeats yearly).
  --bday-remove "<Name>"           Remove a birthday.
  --bday-show                      Show birthdays this month.
  --bday-show --all                Show all saved birthdays.

👫 Catch-Up Mode:
  --catchup-suggest "<Name, ...>"  Suggests when to check in with each person.
  --catchup "<Name>" 
       --date YYYY-MM-DD           Schedule a personal check-in. Adds a [Catch-Up] event.
       [--reminder <time>]         (Optional) Set a pre-check-in reminder.
  --catchup-list                   Show upcoming catch-up events.
  --catchup-clear "<Name>"         Remove someone from your catch-up list.
"""

#
# TODO: enable these functions
#

#📊 Overview & Planning:
#  --insights                       Analyze patterns (best/worst days).
#  --search "<keyword>"             Search upcoming events by keyword in title, notes, or location.
#  --search-all "<keyword>"         Search your full calendar — past, present, future. Total recall.
#  --showids                        Display event IDs in schedule output for reference.
#
#🔧 Other:
#  --export                         Save all data to calboss-backup.json.
#  --import <file>                  Load data from a backup.
#  --version                        Show CalBoss version.
#  --help                           You’re looking at it.
#

    helpText += """
Examples:
  CalBoss --today
  CalBoss --add "Coffee with Sarah" --date 2025-05-24 --starttime 14:00 --endtime 15:00 --reminder 30m
  CalBoss --bday-add "Charmaine 07/03"
  CalBoss --bday-show-all
  CalBoss --catchup-suggest "Lisa, Nick, Aunt Gina"

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
    parser.add_argument("--today",     action="store_true", help="Show today's schedule.")
    parser.add_argument("--week",      action="store_true", help="View full Monday–Sunday overview.")
    parser.add_argument("--add",       type=str,            help='Add an event (e.g. "Call with Lisa at 1PM").')
    parser.add_argument("--date",      type=str,            help="Date of event (YYYY-MM-DD)")
    parser.add_argument("--starttime", type=str,            help="Start time (e.g. 13:00 or 1PM)")
    parser.add_argument("--endtime",   type=str,            help="End time (e.g. 14:00 or 2PM)")
    parser.add_argument("--allday",    action="store_true", help="Add an all-day event (no start or end time needed)")
    parser.add_argument("--location",  type=str,            help="Add a location to your event")
    parser.add_argument("--reminder",  type=str,            help="Reminder before event (e.g. 15m, 1h)")
    parser.add_argument("--remove",    type=str,            help="Remove an event by ID.")
    parser.add_argument("--note",      nargs=2,             help='Add note to an event. Usage: --note <id> "Your note".')
    parser.add_argument("--repeat", choices=["daily", "weekly", "monthly", "yearly"],
                                                            help="Set recurrence frequency for repeating events")

    # birthday
    parser.add_argument("--bday-add",        type=str,            help='Add a birthday (e.g. "Lisa 03/29").')
    parser.add_argument("--bday-remove",     type=str,            help="Remove a birthday by name.")
    parser.add_argument("--bday-show",       action="store_true", help="Show birthdays this month.")
    parser.add_argument("--bday-show-all",   action="store_true", help="Show all saved birthdays.")
    parser.add_argument("--bday-show-today", action="store_true", help="Show today's birthdays.")

    # catch-up
    parser.add_argument("--catchup", type=str, help="Schedule a catch-up event with someone.")
    parser.add_argument("--catchup-suggest", metavar="NAMES", type=str, help='Suggest when to catch up with each person (comma-separated). Example: "Lisa, Nick, Aunt Gina"')
    parser.add_argument("--catchup-list", action="store_true", help="List upcoming catch-up events")
    parser.add_argument("--catchup-clear", type=str, help="Remove all catch-up events for this person")

    # summary 
    parser.add_argument("--summary",    action="store_true", help="Show usage summary: hours booked vs free.")
    parser.add_argument("--focus",      action="store_true", help="Filter for priority events only.")
    parser.add_argument("--insights",   action="store_true", help="Analyze patterns (best/worst days).")
    parser.add_argument("--vibe-check", action="store_true", help="Show today's time breakdown + free hours.")
    parser.add_argument("--search",     type=str,            help="Search events by keyword")
    parser.add_argument("--showids",    action="store_true", help="Display event IDs for reference and deletion.")

    # utility
    parser.add_argument("--export",  action="store_true", help="Save all data to calboss-backup.json.")
    parser.add_argument("--import",  type=str,            help="Load data from a backup file.")
    parser.add_argument("--version", action="store_true", help="Show CalBoss version and exit.")

    # help
    parser.add_argument("--help", action="store_true", help="Show this help message and exit.")

    return parser.parse_args()


##############################################################################
#
# Procedure   : AddEventToGoogleCalendar()
#
# Description : Adds an event to Google Calendar via API.
#             : Supports timed or all-day events.
#             : Optional reminder in 'Xm' or 'Xh' for popup alerts.
#             : Optional location for where the event takes place.
#             : Optional --repeat for recurring events (daily, weekly, etc.).
#
# Input       : summary    - string  - Event description
#             : date       - string  - Event date (YYYY-MM-DD)
#             : startTime  - string  - Start time (HH:MM, 24hr or AM/PM) [optional if allDay]
#             : endTime    - string  - End time (HH:MM, 24hr or AM/PM) [optional if allDay]
#             : reminder   - string  - Optional (e.g. '15m', '1h')
#             : allDay     - boolean - If True, creates an all-day event.
#             : location   - string  - Optional (e.g. "Moe's Backyard")
#             : repeat     - string  - Optional (e.g. 'daily', 'weekly', 'monthly', 'yearly')
#
# Returns     : -none-
#
###############################################################################

def AddEventToGoogleCalendar(summary, date, startTime=None, endTime=None, reminder=None, allDay=False, location=None, repeat=None):

    service = GetCalendarService()

    #
    # allDay: google makes you specify an end time.
    #

    if allDay:
        event = {
            "summary": summary,
            "start"  : {"date": date},
            "end"    : {"date": date},
        }

    #
    # not allDay
    #

    else:
        startTime = f"{date}T{startTime}:00"
        endTime   = f"{date}T{endTime}:00"

        event = {
            "summary": summary,
            "start"  : {"dateTime": startTime, "timeZone": "America/New_York"},
            "end"    : {"dateTime": endTime,   "timeZone": "America/New_York"},
        }

    #
    # location
    #

    if location:
        location = location.strip()
        event["location"] = location
        print(f"\U0001F4CD [INFO] Location set: {location}")

        desc_text = f"Location: {location.strip()}"

        if "description" in event:
            event["description"] += f"\n{desc_text}"
        else:
            event["description"] = desc_text

    #
    # reminder
    #

    if reminder:
        try:
            amount  = int(reminder[:-1])
            unit    = reminder[-1]
            minutes = amount * 60 if unit == 'h' else amount

            event["reminders"] = {
                "useDefault": False,
                "overrides" : [{"method": "popup", "minutes": minutes}]
            }

        except:
            print(f"\u26A0\uFE0F [WARNING] Invalid reminder format: '{reminder}'. Use '15m' or '1h'.")

    #
    # repeat
    #

    if repeat:
        event["recurrence"] = [f"RRULE:FREQ={repeat.upper()}"]
        print(f"🔁 [INFO] Repeat set: {repeat}")

    # create event using google api
    createdEvent = service.events().insert(calendarId='primary', body=event).execute()

    print(f"✅ [INFO] Event created: {createdEvent.get('htmlLink')}")


###############################################################################
#
# Procedure   : FormatTime(time_str)
#
# Description : Takes an ISO 8601 datetime string and makes it human readable. 
#
# Input       : input - Datetime string (e.g., "2025-05-27T14:00:00Z")
#
# Returns     : string - time in format of "HH:MM AM/PM"
#
###############################################################################

def FormatTime(input):

    try:
        dt = datetime.fromisoformat(input.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p")

    except:
        return "❌ [ERROR] Invalid Time"


###############################################################################
#
# Procedure   : GetGoogleCredentials()
#
# Description : Google OAuth2 authentication.
#             : Returns valid credential object for using Google Calendar API.
#             : Uses 'token.pickle' for token caching and refresh logic.
#
# Input       : -none-
#
# Returns     : credentials - Google object to access Calendar API.
#
###############################################################################

def GetGoogleCredentials():

    credentials = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(credentials, token)

    return credentials


###############################################################################
#
# Procedure   : AddNoteToEvent()
#
# Description : Updates description field of existing Google Calendar event.
#
# Input       : eventId - Unique ID of calendar event.
#             : note    - Text string to update. 
#
# Returns     : True  - Event was successfully updated.
#             : False - Error occurs. 
#
###############################################################################

def AddNoteToEvent(eventId, note):

    try:

        credentials = GetGoogleCredentials() 
        service     = build("calendar", "v3", credentials=credentials)

        event = service.events().get(calendarId="primary", eventId=eventId).execute()
        event["description"] = note
        service.events().update(calendarId="primary", eventId=eventId, body=event).execute()

        return True

    except Exception as e:

        print(f"❌ [EXCEPTION] {e}")
        return False


###############################################################################
#
# Procedure   : SaveBirthday()
#
# Description : Saves a birthday to Google Calendar as a 6 AM reminder.
#
# Input       : name  - str : name of person
#             : month - int : month (1–12)
#             : day   - int : day (1–31)
#
# Returns     : -none-
#
###############################################################################

def SaveBirthday(name, month, day):

    service = GetCalendarService()

    now       = datetime.now()
    eventDate = datetime(now.year, month, day, 6, 0, 0)

    event = {
        'summary': f"🎂 {name}'s Birthday",
        'start': {
            'dateTime': eventDate.isoformat(),
            'timeZone': 'America/New_York'
        },
        'end': {
            'dateTime': (eventDate + timedelta(hours=0)).isoformat(),
            'timeZone': 'America/New_York'
        },
        'recurrence': [
            'RRULE:FREQ=YEARLY'
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 0}
            ]
        },
        'colorId': '7'
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"✅ [INFO] Birthday reminder created for {name} on {eventDate.strftime('%Y-%m-%d')}")

    except Exception as e:
        print(f"❌ [ERROR] Failed to create birthday reminder for {name}: {e}")


###############################################################################
#           
# Procedure   : RemoveBirthday()
#   
# Description : Remove a birthday event from Google Calendar.
#
# Input       : name - Name of person
#
# Returns     : -none-
#
###############################################################################

def RemoveBirthday(name):

    service = GetCalendarService()

    targetSummary = f"🎂 {name}'s Birthday"

    try:

        now = datetime.utcnow().isoformat() + 'Z'

        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = now,
            maxResults   = 250,
            singleEvents = False
        ).execute()

        events = eventsResult.get('items', [])

        found = False

        for event in events:
            if event.get('summary') == targetSummary and 'RRULE:FREQ=YEARLY' in str(event.get('recurrence', '')):
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                print(f"🗑️  [INFO] Birthday removed: {name}")
                found = True
                break

        if not found:
            print(f"❌ [INFO] Birthday for {name} not found.")

    except Exception as e:
        print(f"❌ [ERROR] Failed to remove birthday: {e}")


###############################################################################
#
# Procedure   : ShowBirthdaysThisMonth()
#
# Description : Displays birthdays occurring in the current month.
#
# Input       : -none-
#
# Returns     : -none-
#
###############################################################################

def ShowBirthdaysThisMonth():

    service = GetCalendarService()

    now        = datetime.now()
    monthStart = datetime(now.year, now.month, 1).isoformat() + 'Z'
    nextMonth  = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
    monthEnd   = datetime(nextMonth.year, nextMonth.month, 1).isoformat() + 'Z'

    try:
        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = monthStart,
            timeMax      = monthEnd,
            singleEvents = True,
            maxResults   = 100,
            orderBy      = 'startTime'
        ).execute()

        events = eventsResult.get('items', [])

        birthdays = [
            event for event in events
            if event.get('summary', '').startswith("🎂 ")
        ]

        if not birthdays:
            print("😴 No birthdays this month.")
            return

        print("🎉 Birthdays This Month:\n")

        for event in birthdays:
            summary = event.get('summary', '')
            dateStr = event['start'].get('dateTime', event['start'].get('date'))
            dateFormatted = datetime.fromisoformat(dateStr).strftime('%b %d')
            print(f"🎂 {summary[2:]} - {dateFormatted}")

    except Exception as e:
        print(f"❌ [ERROR] Could not retrieve birthdays: {e}")


###############################################################################
#
# Procedure   : ShowTodaysBirthdays()
#
# Description : Displays only birthdays occurring today.
#
# Input       : -none-
#
# Returns     : -none-
#
###############################################################################

def ShowTodaysBirthdays():

    service = GetCalendarService()

    now        = datetime.now()
    todayStart = datetime(now.year, now.month, now.day, 0, 0, 0).isoformat() + 'Z'
    todayEnd   = datetime(now.year, now.month, now.day, 23, 59, 59).isoformat() + 'Z'

    try:
        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = todayStart,
            timeMax      = todayEnd,
            singleEvents = True,
            maxResults   = 20,
            orderBy      ='startTime'
        ).execute()

        events = eventsResult.get('items', [])

        birthdaysToday = [
            event.get('summary', '')[2:]
            for event in events
            if event.get('summary', '').startswith("🎂 ")
        ]

        if not birthdaysToday:
            print("😴 No birthdays today.")
        else:
            print("🎉 Birthdays Today:\n")
            for bday in birthdaysToday:
                print(f"🎂 {bday}")

    except Exception as e:
        print(f"❌ [ERROR] Could not retrieve today's birthdays: {e}")


###############################################################################
#
# Procedure   : ShowBirthdaysThisWeek()
#
# Description : Shows birthdays occurring in the next 7 days.
#
# Input       : -none-
#
# Returns     : -none-
#
###############################################################################

def ShowBirthdaysThisWeek():

    service = GetCalendarService()

    now      = datetime.now()
    nextWeek = now + timedelta(days=7)

    timeMin = now.isoformat() + 'Z'
    timeMax = nextWeek.isoformat() + 'Z'

    try:
        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = timeMin,
            timeMax      = timeMax,
            singleEvents = True,
            orderBy      = 'startTime'
        ).execute()

        events = eventsResult.get('items', [])
        birthdayEvents = [event for event in events if event.get('summary', '').startswith("🎂")]

        if not birthdayEvents:
            print("🎉 No birthdays in the next 7 days.")
            return

        print("🎉 Birthdays This Week:\n")
        for event in birthdayEvents:
            start = event['start'].get('dateTime', event['start'].get('date'))
            dateObj = datetime.fromisoformat(start)
            name = event['summary'].replace("🎂 ", "").replace("'s Birthday", "")
            print(f"🎂 {name}'s Birthday - {dateObj.strftime('%b %d')}")

    except Exception as e:
        print(f"❌ [ERROR] Failed to fetch weekly birthdays: {e}")


###############################################################################
#
# Procedure   : ShowAllBirthdays()
#
# Description : Displays all birthdays on the calendar, grouped by month.
#
# Input       : -none-
#
# Returns     : -none-
#
###############################################################################

def ShowAllBirthdays():

    service = GetCalendarService()                          

    now    = datetime.now()
    future = now.replace(year=now.year + 1)

    timeMin = now.isoformat() + 'Z'
    timeMax = future.isoformat() + 'Z'

    monthEmojis = {
        "January":   "❄️",
        "February":  "💘",
        "March":     "☘️",
        "April":     "🌧️",
        "May":       "🌸",
        "June":      "🌈",
        "July":      "🎆",
        "August":    "🏖️",
        "September": "🍂",
        "October":   "🎃",
        "November":  "🦃",
        "December":  "🎄",
    }

    try:
        eventsResult     = service.events().list(
            calendarId   = 'primary',
            timeMin      = timeMin,
            timeMax      = timeMax,
            singleEvents = True,
            orderBy      = 'startTime'
        ).execute()

        events = eventsResult.get('items', [])
        birthdayEvents = [event for event in events if event.get('summary', '').startswith("🎂")]

        if not birthdayEvents:
            print("🎉 No birthdays found.")
            return

        monthBuckets = {}

        for event in birthdayEvents:

            start     = event['start'].get('dateTime', event['start'].get('date'))
            dateObj   = datetime.fromisoformat(start)
            monthName = dateObj.strftime('%B')
            name      = event['summary'].replace("🎂 ", "").replace("'s Birthday", "").strip()

            if monthName not in monthBuckets:
                monthBuckets[monthName] = []

            monthBuckets[monthName].append((dateObj, name))

        print("🎉 All Birthdays:")

        for month in sorted(monthBuckets.keys(), key=lambda m: datetime.strptime(m, "%B").month):
            emoji = monthEmojis.get(month, "📅")
            print(f"\n{emoji} {month}:")

            sortedBirthdays = sorted(monthBuckets[month], key=lambda x: x[0])

            for dateObj, name in sortedBirthdays:
                print(f"🎂 {name}'s Birthday - {dateObj.strftime('%b %d')}")

    except Exception as e:
        print(f"❌ [ERROR] Failed to fetch all birthdays: {e}")


###############################################################################
#
# Procedure   : ShowWeekSchedule()
#
# Description : Displays the week's schedule in a compact grouped format.
#
# Input       : args - parsed CLI arguments
#
# Returns     : -none-
#
###############################################################################

def ShowWeekSchedule(args):

    service = GetCalendarService()

    now         = datetime.now()
    startOfWeek = now
    endOfWeek   = now + timedelta(days=7)

    eventsResult = service.events().list(
        calendarId   = 'primary',
        timeMin      = startOfWeek.isoformat() + 'Z',
        timeMax      = endOfWeek.isoformat() + 'Z',
        singleEvents = True,
        orderBy      = 'startTime'
    ).execute()

    events = eventsResult.get('items', [])

    if not events:
        print("😴  No events scheduled this week.")
        return

    print(f"\n📆  Weekly Schedule Starting {now.strftime('%b %d')}\n")

    days = {}

    for event in events:

        start   = event['start'].get('dateTime', event['start'].get('date'))
        dateObj = datetime.fromisoformat(start)
        dayStr  = dateObj.strftime('%A (%b %d)')

        if dateObj.date() == (now + timedelta(days=1)).date():
            dayStr = f"Tomorrow ({dateObj.strftime('%b %d')})"

        if dayStr not in days:
            days[dayStr] = []

        timeStr     = FormatTime(start) if 'T' in start else "All Day"
        summary     = event.get('summary', '(No Title)')
        location    = event.get('location', '')
        description = event.get('description', '').strip()
        eventId    = event.get('id', '')

        if summary.startswith('🎂'):
            summary = f"🎂 {summary[2:]}"
        else:
            summary = f"{summary}"

        entry = f"🕘 {timeStr} - {summary}"

        if location:
            entry += f"\n📍 {location}"

        if description:
            entry += f"\n📝 Note: {description}"

        if args.showids and eventId:
            entry += f"\n🆔 Event ID: {eventId}"
        days[dayStr].append(entry)

    for day in sorted(days.keys(), key=lambda d: datetime.strptime(d.split('(')[-1].replace(')', ''), "%b %d")):
        print(f"📅  {day}")
        for entry in days[day]:
            print(entry)
        print()


###############################################################################
#
# Procedure   : AddCatchUpEvent() 
#
# Description : Add a catch-up event to the calendar. 
#
# Input       : name - string - person's name (i.e. John Smith) 
#             : date - string - event date in format YYYY-MM-DD
#
# Returns     : -none-
#
###############################################################################

def AddCatchUpEvent(name, date):   

    service = GetCalendarService() 
  
    startDatetime = datetime.strptime(date + " 20:00", "%Y-%m-%d %H:%M")
    endDatetime   = startDatetime.replace(hour=21)

    event = {
        "summary": f"🤖 Catch-Up: {name}",
        "start": {
            "dateTime": startDatetime.isoformat(),
            "timeZone": "America/New_York"
        },
        "end": {
            "dateTime": endDatetime.isoformat(),
            "timeZone": "America/New_York"
        },
        "description": "Frequency: 18 months"
    }

    try:
        createdEvent = service.events().insert(calendarId='primary', body=event).execute()
        print(f"✅ Catch-Up scheduled with {name} on {date} at 8:00 PM.")

    except Exception as e:
        print(f"❌ [ERROR] Could not schedule catch-up: {e}")


###############################################################################
#
# Procedure   : SuggestCatchUps()
#
# Description : Scan calendar for existing catch-up events.
#             : - If person has past catch-up, suggest follow-up +/- 60 days. 
#             : - If none, suggest a catch-up 6 months from today.
#             : - Shows history for each person.
#
# Input       : names (optional list of names to filter by)
#
# Returns     : -none-
#
###############################################################################

def SuggestCatchUps(names=None):

    service = GetCalendarService()

    now = datetime.utcnow().isoformat() + 'Z'

    try:
        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = '2000-01-01T00:00:00Z',
            maxResults   = 2500,
            singleEvents = True,
            orderBy      = 'startTime',
            q            = "🤖 Catch-Up:"
        ).execute()

        events       = eventsResult.get('items', [])
        latestEvents = {}

        for event in events:

            summary = event.get('summary', '').strip()

            if not summary.startswith("🤖 Catch-Up:"):
                continue

            name  = summary.replace("🤖 Catch-Up:", "").strip()
            start = event['start'].get('dateTime', event['start'].get('date'))

            try:
                dt = datetime.fromisoformat(start)

            except:
                continue

            desc = event.get('description', '').lower()

            frequency = 18

            if 'frequency:' in desc:

                try:
                    freq_str = desc.split("frequency:")[1].split("months")[0].strip()
                    frequency = int(freq_str)

                except:
                    pass

            if name not in latestEvents or dt > latestEvents[name]['date']:
                latestEvents[name] = {'date': dt, 'frequency': frequency}

        print("📬 Suggested Catch-Ups:\n")

        if names:

            for name in names:
                if name in latestEvents:
                    data = latestEvents[name]
                    print(f"🔍 Found past catch-up with {name} on {data['date'].strftime('%b %d, %Y')}")
                    salted = data['date'] + relativedelta(months=data['frequency']) + timedelta(days=random.randint(-60, 60))
                    print(f"👤 {name} — Next suggested catch-up: {salted.strftime('%b %d, %Y')}\n")

                else:
                    print(f"❓ No past catch-up found for {name}.")
                    suggested = datetime.now() + relativedelta(months=6)
                    print(f"👤 {name} — Suggested default catch-up: {suggested.strftime('%b %d, %Y')}\n")

        else:
            for name, data in latestEvents.items():
                salted = data['date'] + relativedelta(months=data['frequency']) + timedelta(days=random.randint(-60, 60))
                print(f"👤 {name} — Next suggested catch-up: {salted.strftime('%b %d, %Y')}")

    except Exception as e:
        print(f"❌ [ERROR] Failed to generate suggestions: {e}")


###############################################################################
#
# Procedure   : ListCatchUps()
#
# Description : Lists upcoming catch-up events.
#
# Input       : -none-
#
# Returns     : -none-
#
###############################################################################

def ListCatchUps():

    service = GetCalendarService()

    now = datetime.now(timezone.utc).isoformat()

    try:
        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = now,
            maxResults   = 100,
            singleEvents = True,
            orderBy      = 'startTime',
            q            = "🤖 Catch-Up:"
        ).execute()

        events = eventsResult.get('items', [])

        if not events:
            print("📭 No upcoming catch-up events.")
            return

        print("📅 Upcoming Catch-Up Events:\n")

        for event in events:

            name  = event.get('summary', '').replace("🤖 Catch-Up: ", "")
            start = event['start'].get('dateTime', event['start'].get('date'))
            dt    = datetime.fromisoformat(start)

            print(f"👤 {name} — {dt.strftime('%b %d, %Y @ %I:%M %p')}")

    except Exception as e:
        print(f"❌ [ERROR] Failed to list catch-ups: {e}")


###############################################################################
#
# Procedure   : ClearCatchUpEvents()
#
# Description : Deletes all future catch-up events for a given name
#
# Input       : name (str)
#
# Returns     : None
#
###############################################################################

def ClearCatchUpEvents(name):

    service = GetCalendarService()

    now = datetime.now(timezone.utc).isoformat()

    try:
        eventsResult = service.events().list(
            calendarId   = 'primary',
            timeMin      = now,
            maxResults   = 2500,
            singleEvents =  True,
            q            = f"🤖 Catch-Up: {name}",
            orderBy      = 'startTime'
        ).execute()

        events = eventsResult.get('items', [])

        if not events:
            print(f"📭 No upcoming catch-up events found for {name}.")
            return

        for event in events:
            service.events().delete(calendarId='primary', eventId=event['id']).execute()

        print(f"🗑️ Cleared all catch-up events for {name}.")

    except Exception as e:
        print(f"❌ [ERROR] Failed to clear catch-ups: {e}")


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

    #
    # --bday-show-today 
    # --bday-show-week
    # takes top priority
    #

    if args.bday_show_today:
        ShowTodaysBirthdays()
        return

    #
    # --bday-show
    #

    elif args.bday_show:
        ShowBirthdaysThisMonth()
        return

    #
    # --today
    #

    if args.today:
        print(f"📅  Today’s Schedule ({datetime.now().strftime('%b %d')}):")

        service = GetCalendarService()
        events = FetchTodayEvents(service)

        if not events:
            print("😴  No events scheduled for today.\n")

        else:
            for event in events:
                start       = event['start'].get('dateTime', event['start'].get('date'))
                summary     = event.get('summary', '(No Title)')
                location    = event.get('location', '')
                timeStr     = FormatTime(start) if 'T' in start else "All Day"
                description = event.get("description", "").strip()

                print(f"🕘 {timeStr} - {summary}")

                if location:
                    print(f"📍 {location}")

                if description:
                    print(f"📝 Note: {description}")

                if args.showids and event.get('id'):
                    print(f"🆔 {event['id']}")
                #print("")

        # now let's show birthdays for today

        today = datetime.now().date()

        birthdayEvents   = service.events().list(
            calendarId   = 'primary',
            timeMin      = datetime.combine(today, datetime.min.time()).isoformat() + 'Z',
            timeMax      = datetime.combine(today, datetime.max.time()).isoformat() + 'Z',
            q            = "🎂",
            singleEvents = True,
            orderBy      = 'startTime'
        ).execute()

        birthdaysToday = birthdayEvents.get('items', [])

        if birthdaysToday:

            print("\n🎉 Birthday(s):")

            for event in birthdaysToday:
                summary = event.get('summary', '(No Title)')
                start   = event['start'].get('dateTime', event['start'].get('date'))
                timeStr = FormatTime(start) if 'T' in start else "All Day"
                print(f"{summary}")

    #
    # --week
    #

    elif args.week:
        ShowWeekSchedule(args)

    #
    # --add
    #

    elif args.add:

        if args.allday:
            if not args.date:
                print("[ERROR] --allday requires --date")
                return

            event = {
                "summary" : args.add,
                "date"    : args.date,
                "allday"  : True,
                "reminder": args.reminder if args.reminder else "none"
            }

            AddEventToGoogleCalendar(
                summary=args.add,
                date=args.date,
                allDay=True,
                reminder=args.reminder,
                location=args.location,
                repeat=args.repeat
            )

            print(f"✅ [INFO] All-day event added: '{args.add}' on {args.date}.")

        else:
            if not args.date or not args.starttime or not args.endtime:
                print("[ERROR] --add requires --date, --starttime, and --endtime (unless --allday is used)")
                return

            event = {
                "summary"  : args.add,
                "date"     : args.date,
                "starttime": args.starttime,
                "endtime"  : args.endtime,
                "reminder" : args.reminder if args.reminder else "none"
            }

            AddEventToGoogleCalendar(
                summary=args.add,
                date=args.date,
                startTime=args.starttime,
                endTime=args.endtime,
                reminder=args.reminder,
                location=args.location,
                repeat=args.repeat
            )

            print(f"✅ [INFO] Event added: '{args.add}' on {args.date} from {args.starttime} to {args.endtime}")

    #
    # --remove
    #

    elif args.remove:
        service = GetCalendarService()

        try:
            service.events().delete(calendarId='primary', eventId=args.remove).execute()
            print(f"🗑️ [INFO] Event {args.remove} deleted.")

        except Exception as e:
            print(f"❌ [ERROR] Could not delete event: {e}")

    #
    # --note
    #

    elif args.note:
        event_id, note_text = args.note
        success = AddNoteToEvent(event_id, note_text)

        if success:
            print(f"📝 [INFO] Note added to event {event_id}: \"{note_text}\"")

        else:
            print(f"❌ [ERROR] Failed to add note to event {event_id}")

    #
    # --bday-add
    #

    if args.bday_add:
        nameDate = args.bday_add.strip().rsplit(' ', 1)

        if len(nameDate) != 2:
            print("❌ [ERROR] Invalid format.")

        else:
            name, dateStr = nameDate

            try:
                month, day = map(int, dateStr.split('/'))
                SaveBirthday(name, month, day)
                print(f"🎂 Birthday added: {name} on {month}/{day}")

            except ValueError:
                print("❌ [ERROR] Invalid date format (Use MM/DD)")

    #
    # --bday-remove
    #

    if args.bday_remove:
        RemoveBirthday(args.bday_remove)

    #
    # --catchup
    # --catch-up-suggest
    # --catchup-list
    # --catchup-clear
    #
    if args.catchup and args.date:
        AddCatchUpEvent(args.catchup, args.date)
        return

    if args.catchup_suggest:
        names = [name.strip() for name in args.catchup_suggest.split(",")]
        SuggestCatchUps(names)
        return

    if args.catchup_list:
        ListCatchUps()
        return

    if args.catchup_clear:
        ClearCatchUpEvents(args.catchup_clear)
        return




if __name__ == "__main__":
    Main()

