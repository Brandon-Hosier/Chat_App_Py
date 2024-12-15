from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room, send
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Used for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatapp.db'  # Database path
db = SQLAlchemy(app)  # Initialize the database
socketio = SocketIO(app)  # Initialize Socket.IO for real-time messaging

# Database model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user
    username = db.Column(db.String(150), nullable=False, unique=True)  # Username
    password = db.Column(db.String(150), nullable=False)  # Hashed password

# Route: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None  # Feedback message for the user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Hash the password

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            message = "Username already exists!"
        else:
            # Add the new user to the database
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            message = "Account successfully created! Please log in."

    return render_template('register.html', message=message)

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None  # Feedback message for the user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find the user in the database
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = username  # Save username in session
            return redirect(url_for('home'))
        else:
            message = "Invalid username or password!"

    return render_template('login.html', message=message)

# Route: Home (Join Chat Room)
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:  # Redirect to login if user is not logged in
        return redirect(url_for('login'))

    if request.method == 'POST':
        room_code = request.form['room_code']
        return redirect(url_for('chat', room_code=room_code))

    return render_template('index.html', username=session['user'])

# Route: Chat Room
@app.route('/chat/<room_code>', methods=['GET', 'POST'])
def chat(room_code):
    if 'user' not in session:  # Redirect to login if user is not logged in
        return redirect(url_for('login'))

    if request.method == 'POST':
        message = request.form['message']  # This will capture both text and emoji from the input field
        socketio.emit('message', {'room': room_code, 'username': session['user'], 'message': message})
    
    return render_template('chat.html', room_code=room_code, username=session['user'])

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('user', None)  # Clear the session
    return redirect(url_for('login'))

# Socket.IO: Handle user joining a room
@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data['room']
    join_room(room)  # Add the user to the room
    send(f'{username} has joined the room!', to=room)

# Socket.IO: Handle messages in the room
@socketio.on('message')
def handle_message(data):
    room = data['room']  # Extract the room name
    username = data['username']  # Extract the username
    message = f"{username}: {data['message']}"  # Format the message
    send(message, to=room)  # Send the message to the room

# Socket.IO: Handle user leaving a room
@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)  # Remove the user from the room
    send(f'{username} has left the room.', to=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    socketio.run(app, debug=True)  # Run the app with Socket.IO enabled
