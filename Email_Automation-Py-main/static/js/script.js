// Handle Excel Upload
document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const messageDiv = document.getElementById('message');
    const sendBtn = document.getElementById('sendEmailsBtn');

    messageDiv.textContent = 'Uploading...';
    messageDiv.style.color = 'blue';

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            messageDiv.textContent = data.message;
            messageDiv.style.color = 'green';

            // Show Send Emails button after successful upload
            sendBtn.style.display = 'block';
        } 
        else if (data.error) {
            messageDiv.textContent = data.error;
            messageDiv.style.color = 'red';
        }
    })
    .catch(error => {
        messageDiv.textContent = 'Upload error: ' + error.message;
        messageDiv.style.color = 'red';
    });
});


// Handle Bulk Email Sending
document.getElementById('sendEmailsBtn').addEventListener('click', function () {
    const messageDiv = document.getElementById('message');

    messageDiv.textContent = 'Sending pending emails...';
    messageDiv.style.color = 'blue';

    fetch('/send_bulk_emails', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.results) {
            messageDiv.textContent = '✅ Emails sent successfully!';
            messageDiv.style.color = 'green';

            console.log("Email Results:", data.results);
        } 
        else if (data.message) {
            messageDiv.textContent = data.message;
        }
    })
    .catch(error => {
        messageDiv.textContent = 'Error: ' + error.message;
        messageDiv.style.color = 'red';
    });
});
