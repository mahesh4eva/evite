# Evite App

Evite App is a web application that allows users to create and manage digital invitations for events. Users can create customized invitations, manage guest lists, send invitations via email, and track RSVPs.

## Features

- User authentication (login/logout)
- Create, edit, and delete invitations
- Customize invitations with event details, descriptions, and images
- Manage guest lists
- Send email invitations to guests
- Track RSVP status
- Send reminder emails to guests who haven't responded

## Technologies Used

- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Mail
- Flask-Login
- TinyMCE (rich text editor)
- Flatpickr (date picker)
- Dropzone.js (drag-and-drop file upload)
- Tailwind CSS (styling)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/evite-app.git
   cd evite-app
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables for email configuration:
   ```
   export MAIL_USERNAME=your_email@gmail.com
   export MAIL_PASSWORD=your_email_password
   ```
   On Windows, use `set` instead of `export`.

5. Initialize the database:
   ```
   python
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Create an account or log in if you already have one

4. Create a new invitation by clicking on "Create Invitation" in the navigation bar

5. Fill in the event details, add a custom image if desired, and save the invitation

6. Manage your guest list by adding or removing guests

7. Preview your invitation and send it to your guests

8. Track RSVPs and send reminders as needed

## Customization

- To change the application's styling, modify the Tailwind CSS classes in the HTML templates
- To customize email templates, edit the `email_template.html` and `reminder_email_template.html` files in the `templates` directory

## Deployment

For production deployment:

1. Use a production-ready web server like Gunicorn
2. Set up a production database (e.g., PostgreSQL)
3. Use a transactional email service like SendGrid or Mailgun for sending emails at scale
4. Set up proper error handling and logging
5. Ensure all sensitive information (e.g., secret keys, database credentials) are stored as environment variables

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- Flask documentation
- SQLAlchemy documentation
- Tailwind CSS documentation
- TinyMCE documentation
- Flatpickr documentation
- Dropzone.js documentation
