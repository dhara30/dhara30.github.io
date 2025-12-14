from flask import Flask, render_template, request, send_file, url_for
import qrcode
from ics import Calendar, Event
from datetime import datetime
import os
import io
from ics.alarm import DisplayAlarm
from datetime import timedelta

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form
    event_type = data.get('event_type', '').strip()
    
    # Debug: Print event type to console
    print(f"DEBUG: Event Type = '{event_type}'")
    print(f"DEBUG: Platform Link = '{data.get('platform_link')}'")
    print(f"DEBUG: Access Code = '{data.get('access_code')}'")
    
    # Create Calendar Event
    c = Calendar()
    e = Event()
    
    # Basic Details
    title = f"{event_type} Invitation"
    if event_type == 'Wedding':
        title = f"Wedding: {data.get('bride_groom_names')}"
    elif event_type == 'Birthday':
        title = f"Birthday: {data.get('celebrant_name')}"
    elif event_type == 'Concert':
        title = f"Concert: {data.get('performer_name')}"
    elif event_type == 'Corporate':
        comp = data.get('company_name')
        title = f"Event: {comp}" if comp else "Corporate Event"
        
    e.name = title
    
    # Date and Time (Assuming input is ISO format YYYY-MM-DDTHH:MM)
    # For simplicity in this prototype, we'll just use the current time if not provided or handle it simply.
    # In a real app, we'd need a date picker in the form.
    # The user request didn't explicitly ask for a date picker in the table, but it's implied for an event.
    # I will add a generic date/time field to the form and use it here.
    event_date = data.get('event_date')
    if event_date:
        try:
            e.begin = event_date
        except:
            pass # Fallback or error handling
            

    # Get platform details (always retrieve from form)
    platform_link = data.get('platform_link', '').strip()
    access_code = data.get('access_code', '').strip()
    
    # Description with Online access details
    base_desc = data.get('description', f"You are invited to a {event_type}!")
    
    # Add platform details when Join Link or Access Code is provided
    if platform_link or access_code:
        base_desc = base_desc + "\n\n"
        if platform_link:
            base_desc += f"Join Link: {platform_link}\n"
        if access_code:
            base_desc += f"Access Code: {access_code}\n"
    
    e.description = base_desc
    
    # Set URL field for Online events (shows prominently in iPhone Calendar)
    if event_type == 'Online' and platform_link:
        e.url = platform_link
    
    # Location Logic
    location = data.get('venue')
    if not location:
        if event_type == 'Wedding':
            location = data.get('reception_venue')
        elif event_type == 'Online':
            # For online events, show access info in location
            if platform_link and access_code:
                location = f"{platform_link} (Code: {access_code})"
            elif platform_link:
                location = platform_link
            elif access_code:
                location = f"Access Code: {access_code}"
            
    e.location = location if location else 'TBD'

    # Alarm / Reminder Logic
    reminder_minutes = data.get('reminder')
    if reminder_minutes:
        try:
            minutes = int(reminder_minutes)
            alarm = DisplayAlarm(trigger=timedelta(minutes=-minutes))
            e.alarms.append(alarm)
        except ValueError:
            pass

    c.events.add(e)
    
    # Save ICS file
    ics_filename = f"invite_{datetime.now().strftime('%Y%m%d%H%M%S')}.ics"
    ics_path = os.path.join('static', ics_filename)
    with open(ics_path, 'w') as f:
        f.write(c.serialize())
        
    # Generate QR Code
    # The QR code will contain the content of the ICS file (VEVENT) for direct scanning if small enough,
    # or a link to the file if we were hosting it. 
    # Since this is local, we'll try to encode the VEVENT data.
    # However, VEVENT data can be large. 
    # Let's encode a simple text summary + the fact that it's an event.
    # Or better, just the VEVENT block.
    
    qr_data = c.serialize()
    # If too long, QR code generation might fail or be too dense.
    # For this prototype, let's assume it fits or we just encode the title and date.
    # Actually, the requirement is "QR code will create event on the user's calander".
    # The standard way is to encode the VEVENT data.
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    qr_filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    qr_path = os.path.join('static', qr_filename)
    img.save(qr_path)
    
    return render_template('result.html', qr_image=qr_filename, ics_file=ics_filename, event_title=title)

if __name__ == '__main__':
    app.run(debug=True)
