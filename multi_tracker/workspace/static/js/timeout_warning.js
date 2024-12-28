document.addEventListener("DOMContentLoaded", function () {
    const sessionTimeout = 900; // 15 minutes in seconds
    const warningTime = sessionTimeout - 60; // Show warning 1 minute before timeout

    // Timer for showing the logout warning
    const warningTimer = setTimeout(() => {
        const stayLoggedIn = confirm(
            "You will be logged out due to inactivity in 1 minute. Click OK to stay logged in."
        );
        if (stayLoggedIn) {
            // Make an AJAX call to refresh the session
            fetch("/session_timeout_warning/", { method: "GET", credentials: "same-origin" })
                .then(response => {
                    if (response.ok) {
                        alert("Session refreshed successfully!");
                        window.location.reload(); // Reload the page to reset timers
                    } else {
                        alert("Unable to refresh session. Please log back in.");
                    }
                })
                .catch(() => alert("Failed to refresh session. Please log back in."));
        }
    }, warningTime * 1000);

    // Timer for automatic logout
    const logoutTimer = setTimeout(() => {
        window.location.href = "/accounts/logout/";
    }, sessionTimeout * 1000);
});
