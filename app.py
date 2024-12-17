from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room, send
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatapp.db'  
db = SQLAlchemy(app)  # Initialise the database
socketio = SocketIO(app)  # Initialise Socket.IO for real-time messaging


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user
    username = db.Column(db.String(150), nullable=False, unique=True)  # Username
    password = db.Column(db.String(150), nullable=False)  # Hashed password


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Hash the password

        # Checks if username already exists
        if User.query.filter_by(username=username).first():
            message = "Username already exists!"
        else:
            # Adds the new user to the database
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            message = "Account successfully created! Please log in."

    return render_template('register.html', message=message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Finds the user in the database
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = username  # Saves username in session
            return redirect(url_for('home'))
        else:
            message = "Invalid username or password!"

    return render_template('login.html', message=message)


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:  # Redirects to login if user is not logged in
        return redirect(url_for('login'))

    if request.method == 'POST':
        room_code = request.form['room_code']
        return redirect(url_for('chat', room_code=room_code))

    return render_template('index.html', username=session['user'])


@app.route('/chat/<room_code>')
def chat(room_code):
    if 'user' not in session:  
        return redirect(url_for('login'))

    return render_template('chat.html', room_code=room_code, username=session['user'])


@app.route('/logout')
def logout():
    session.pop('user', None) 
    return redirect(url_for('login'))


@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data['room']
    join_room(room)  # Adds the user to the room
    send(f'{username} has joined the room!', to=room)


@socketio.on('message')
def handle_message(data):
    room = data['room']  # Extract the room name
    username = data['username']  # Extract the username
    message = f"{username}: {data['message']}"  # Formats the message
    send(message, to=room)  # Sends the message to the room


@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)  # Removes the user from the room
    send(f'{username} has left the room.', to=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    socketio.run(app, debug=True)  # Runs the app with Socket.IO enabled
