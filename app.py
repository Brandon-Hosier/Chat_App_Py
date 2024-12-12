from flask import Flask, render_template, request, redirect, url_for, session  # Import Flask modules
from flask_sqlalchemy import SQLAlchemy  # For database management
from werkzeug.security import generate_password_hash, check_password_hash  # For secure password handling

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your_secret_key'  # Secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatapp.db'  # Database location and type

# Initialize database
db = SQLAlchemy(app)

# User model to store user credentials in the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user
    username = db.Column(db.String(150), nullable=False, unique=True)  # Username field
    password = db.Column(db.String(150), nullable=False)  # Password field

# Route to handle user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Check if the form is submitted
        username = request.form['username']  # Get username from the form
        password = request.form['password']  # Get password from the form
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Changed to correct hashing method


        if User.query.filter_by(username=username).first():  # Check if the username already exists
            return "Username already exists!"  # Display error if username exists
        
        new_user = User(username=username, password=hashed_password)  # Create a new user record
        db.session.add(new_user)  # Add the user to the database
        db.session.commit()  # Commit the transaction
        return redirect(url_for('login'))  # Redirect to the login page after successful registration

    return render_template('register.html')  # Render the registration form template

# Route to handle user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Check if the form is submitted
        username = request.form['username']  # Get username from the form
        password = request.form['password']  # Get password from the form

        user = User.query.filter_by(username=username).first()  # Query the database for the user
        if user and check_password_hash(user.password, password):  # Validate the user credentials
            session['user'] = username  # Save the username in the session to track login
            return redirect(url_for('home'))  # Redirect to the home page if login is successful
        else:
            return "Invalid credentials!"  # Display error message if login fails
    
    return render_template('login.html')  # Render the login form template

# Route to display the home page after login
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))  # Redirect to login page if not authenticated

    if request.method == 'POST':  # Check if the form is submitted
        room_code = request.form['room_code']  # Get the room code from the form
        return redirect(url_for('chat', room_code=room_code))  # Redirect to the chat room page
    return render_template('index.html')  # Render the home page template

# Route to display the chat room
@app.route('/chat/<room_code>')
def chat(room_code):
    return render_template('chat.html', room_code=room_code)  # Pass the room code to the template

# Route to log out the user
@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from the session
    return redirect(url_for('login'))  # Redirect to the login page

if __name__ == '__main__':
    # Ensure the application context is active when creating the database tables
    with app.app_context():
        db.create_all()  # Create the database tables (if not already created)
    app.run(debug=True)  # Run the app in debug mode for easier development
