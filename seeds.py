"""
Sample Data Seeder for Help Desk Ticket Tracker
Run with: python seeds.py
This will populate the database with realistic tickets and notes if the database is empty.
"""

from app import app, db
from models import Ticket, TroubleshootingNote
from datetime import datetime, timedelta
import random


SAMPLE_TICKETS = [
    {
        "title": "Employee cannot connect to office Wi-Fi",
        "description": "User in the east wing reports frequent disconnections on the corporate Wi-Fi network, especially during peak hours (2-4 PM). Signal strength appears normal but connection drops every 10-15 minutes.",
        "priority": "High",
        "category": "Network",
        "status": "Open"
    },
    {
        "title": "Laptop fails to start after Windows update",
        "description": "Dell Latitude 5520 shows black screen with blinking cursor after installing the latest Windows 11 cumulative update. Tried safe mode and startup repair with no success. Urgent for finance team member.",
        "priority": "Critical",
        "category": "Hardware",
        "status": "In Progress"
    },
    {
        "title": "Password reset request for VPN access",
        "description": "New contractor needs VPN credentials reset. They can log into the company portal but VPN connection fails with authentication error. They start on Monday.",
        "priority": "Medium",
        "category": "Account Access",
        "status": "Resolved"
    },
    {
        "title": "Network printer not detected by multiple users",
        "description": "HP LaserJet in marketing department shows as offline for 4 users. Other printers on the same floor work fine. Power cycle and driver reinstall attempted by users.",
        "priority": "Low",
        "category": "Hardware",
        "status": "Open"
    },
    {
        "title": "CRM application crashes during login",
        "description": "Salesforce-based internal CRM crashes with 'Memory access violation' error when users try to log in from the office network. Happens on Chrome and Edge. Remote users not affected.",
        "priority": "High",
        "category": "Software",
        "status": "Closed"
    },
    {
        "title": "Email not syncing on mobile devices",
        "description": "Multiple iPhone and Android users report emails stopped syncing since yesterday morning. Webmail works fine. Outlook desktop client also affected for some users.",
        "priority": "Medium",
        "category": "Other",
        "status": "In Progress"
    },
    {
        "title": "Slow internet speeds in Marketing department",
        "description": "Team of 8 people experiencing very slow page loads and file transfers since Monday. Speed test shows 2-3 Mbps down instead of usual 80+ Mbps. Other departments unaffected.",
        "priority": "Medium",
        "category": "Network",
        "status": "Open"
    }
]

SAMPLE_NOTES = {
    1: [  # Wi-Fi ticket
        "Checked AP logs - no obvious errors. Will investigate channel interference tomorrow morning.",
    ],
    2: [  # Laptop ticket
        "Booted into WinRE. SFC /scannow found and repaired corrupted system files. Awaiting user confirmation that it boots normally.",
        "User confirmed successful boot. Marking as resolved after final verification.",
    ],
    3: [  # Password reset
        "Reset VPN password and sent secure link to contractor. They confirmed successful connection.",
    ],
    5: [  # CRM crash
        "Issue was caused by an outdated browser extension. Advised users to disable extensions and clear cache. No further crashes reported.",
        "Root cause identified as conflicting extension. Documented workaround and notified IT security team.",
    ]
}


def seed_database():
    with app.app_context():
        db.create_all()

        if Ticket.query.count() > 0:
            print("Database already contains tickets. Skipping seed to avoid duplicates.")
            return

        print("Seeding sample data...")

        for i, ticket_data in enumerate(SAMPLE_TICKETS, start=1):
            # Add slight variation in creation dates for realism
            created = datetime.utcnow() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            
            ticket = Ticket(
                title=ticket_data["title"],
                description=ticket_data["description"],
                priority=ticket_data["priority"],
                category=ticket_data["category"],
                status=ticket_data["status"],
                created_at=created,
                updated_at=created
            )
            db.session.add(ticket)
            db.session.flush()  # Get the ticket ID immediately

            # Add sample notes for some tickets
            if i in SAMPLE_NOTES:
                for note_text in SAMPLE_NOTES[i]:
                    note_created = created + timedelta(hours=random.randint(1, 48))
                    note = TroubleshootingNote(
                        ticket_id=ticket.id,
                        note=note_text,
                        created_at=note_created
                    )
                    db.session.add(note)

        db.session.commit()
        print(f"Successfully seeded {len(SAMPLE_TICKETS)} tickets with notes!")


if __name__ == '__main__':
    seed_database()