document.addEventListener('DOMContentLoaded', () => {
    const socket = io();  // Establish Socket.IO connection
    const deathSound = document.getElementById('deathSound');
    const alarmButton = document.getElementById('alarmButton');
    let alarmPlaying = false;

    alarmButton.addEventListener('click', () => {
        if (alarmPlaying) {
            deathSound.pause();
            deathSound.currentTime = 0;
            alarmPlaying = false;
            alarmButton.disabled = true;
            document.body.classList.remove('blinking-border');
        }
    });

    // Client-side Socket.IO event handlers
    socket.on('connect', () => {
        console.log('Connected to server'); // Log when client connects
    });

    socket.on('connect_error', (error) => {
        console.error('Socket.IO connection error:', error);
    });

    socket.on('face_position', (data) => {
        // No longer need to handle face position for this scenario
    });

    socket.on('death_detected', (data) => {
        // Play death sound
        if (!alarmPlaying) {
            deathSound.play().catch(error => {
                console.log('Playback failed:', error);
            });
            alarmPlaying = true;
            alarmButton.disabled = false;

            // Toggle blinking border on the body element
            document.body.classList.add('blinking-border');
        }
    });

    // Example: Emit a test event from client to server
    socket.emit('test_client_to_server', { message: 'Hello from client' });

    // Example: Respond to a test event from server to client
    socket.on('test_server_to_client', (data) => {
        console.log('Server says:', data.message);
    });
});
