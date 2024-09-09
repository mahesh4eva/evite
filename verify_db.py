from app import app, db, Guest, Invitation

with app.app_context():
    invitations = Invitation.query.all()
    
    if not invitations:
        print("No invitations found in the database.")
    else:
        for invitation in invitations:
            print(f"Invitation: {invitation.event_name} (ID: {invitation.id})")
            guests = Guest.query.filter_by(invitation_id=invitation.id).all()
            
            if guests:
                for guest in guests:
                    print(f"  - Guest: {guest.name}, Email: {guest.email}, RSVP: {guest.rsvp}")
            else:
                print("  No guests for this invitation")
            
            print()  # Empty line for readability