from app import app as application

# Expose the Flask application as a WSGI callable for platforms like Vercel
# Many WSGI servers look for a module-level variable called `app`.
app = application
