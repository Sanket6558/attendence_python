// Initialize tracking interval variable
let trackingInterval;
let empId;

document.getElementById('admin-button').addEventListener('click', function () {
    document.getElementById('initial-buttons').style.display = 'none';
    document.getElementById('register-section').style.display = 'block';
});

document.getElementById('employee-button').addEventListener('click', function () {
    document.getElementById('initial-buttons').style.display = 'none';
    document.getElementById('login-section').style.display = 'block';
});

document.getElementById('admin-register-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    const adminPassword = formData.get('admin_password');
    if (adminPassword !== 'admin123') {
        document.getElementById('register-message').textContent = 'Invalid Admin Password';
        return;
    }
    fetch('/register', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('register-message').textContent = data.message;
        if (data.status === 'success') {
            document.getElementById('register-section').style.display = 'none';
            document.getElementById('initial-buttons').style.display = 'block';
        }
    });
});

document.getElementById('login-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('login-message').textContent = data.message;
        if (data.status === 'success') {
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('attendance-section').style.display = 'block';
            empId = formData.get('emp_id');
        }
    });
});

document.getElementById('mark-attendance').addEventListener('click', function () {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            const location = position.coords.latitude + ',' + position.coords.longitude;
            const formData = new FormData();
            formData.append('emp_id', empId);
            formData.append('location', location);
            fetch('/mark_attendance', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('attendance-message').textContent = data.message;
                if (data.status === 'success') {
                    document.getElementById('sign-out-section').style.display = 'block';
                    document.getElementById('time-spent-section').style.display = 'none';

                    // Start tracking employee's location continuously
                    trackingInterval = setInterval(function () {
                        navigator.geolocation.getCurrentPosition(function (position) {
                            const currentLocation = position.coords.latitude + ',' + position.coords.longitude;
                            const updateFormData = new FormData();
                            updateFormData.append('emp_id', empId);
                            updateFormData.append('location', currentLocation);
                            fetch('/update_location', {
                                method: 'POST',
                                body: updateFormData
                            })
                            .then(response => response.json())
                            .then(data => {
                                console.log(data.message);  // Log location update status
                            });
                        });
                    }, 30000);  // Check location every 30 seconds
                }
            });
        });
    } else {
        document.getElementById('attendance-message').textContent = 'Geolocation is not supported by this browser.';
    }
});

document.getElementById('sign-out').addEventListener('click', function () {
    clearInterval(trackingInterval);  // Stop tracking location
    const formData = new FormData();
    formData.append('emp_id', empId);
    fetch('/sign_out', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('sign-out-message').textContent = data.message;
        if (data.status === 'success') {
            document.getElementById('sign-out-section').style.display = 'none';
            document.getElementById('time-spent-section').style.display = 'block';
            document.getElementById('time-spent').textContent = data.time_spent;
        }
    });
});
