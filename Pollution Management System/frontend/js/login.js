function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("error");

    // Clear previous errors
    errorDiv.classList.add('d-none');
    errorDiv.textContent = '';

    fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.message === "Login successful") {

            // Save user info (temporary storage)
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("role", data.role);
            localStorage.setItem("name", data.name);
            localStorage.setItem("email", email);

            // Show success message
            errorDiv.classList.remove('alert-danger');
            errorDiv.classList.add('alert-success');
            errorDiv.innerHTML = '<i class="fas fa-check-circle me-2"></i>Login successful! Redirecting...';
            errorDiv.classList.remove('d-none');

            // Redirect based on role
            setTimeout(() => {
                if (data.role === "ADMIN") {
                    window.location.href = "authority.html";
                } else {
                    window.location.href = "citizen.html";
                }
            }, 1000);

        } else {
            errorDiv.classList.remove('alert-success');
            errorDiv.classList.add('alert-danger');
            errorDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>' + data.message;
            errorDiv.classList.remove('d-none');
        }
    })
    .catch(err => {
        errorDiv.classList.remove('alert-success');
        errorDiv.classList.add('alert-danger');
        errorDiv.innerHTML = '<i class="fas fa-times-circle me-2"></i>Server error. Please try again.';
        errorDiv.classList.remove('d-none');
    });
}
