from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' 
socketio = SocketIO(app)

# Dictionary to track active rooms
rooms = {}

@app.route('/', methods=['GET', 'POST'])
def home():
    print("Rendering index.html") 
    if request.method == 'POST':
        room_code = request.form['room_code']
        return redirect(url_for('chat', room_code=room_code))
    return render_template('index.html')


@app.route('/chat/<room_code>')
def chat(room_code):
    return render_template('chat.html', room_code=room_code)


@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(f'{username} has joined the room!', to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = f"{data['username']}: {data['message']}"
    send(message, to=room)

@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(f'{username} has left the room.', to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

