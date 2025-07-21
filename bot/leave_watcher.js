const fs = require('fs');
const path = require('path');

// Export a function that starts watching for the leave signal
module.exports = function(voiceConnection, jsActivePath) {
    const leaveSignalPath = path.join(__dirname, 'leave_signal.txt');

    function disconnectFromVoice() {
        if (voiceConnection && voiceConnection.disconnect) {
            voiceConnection.disconnect();
            console.log('Listener.js: Disconnected from voice due to leave signal.');
            if (jsActivePath && fs.existsSync(jsActivePath)) {
                fs.unlink(jsActivePath, () => {});
            }
        }
    }

    fs.watchFile(leaveSignalPath, (curr, prev) => {
        if (curr.size > 0) {
            fs.readFile(leaveSignalPath, 'utf8', (err, data) => {
                if (!err && data.trim() === 'leave') {
                    disconnectFromVoice();
                    fs.unlink(leaveSignalPath, () => {});
                }
            });
        }
    });
};
