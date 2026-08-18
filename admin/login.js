// =========================
// ADMIN LOGIN
// =========================

const loginForm =
    document.getElementById("loginForm");

const loginMessage =
    document.getElementById("loginMessage");


loginForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        // =========================
        // GET LOGIN DETAILS
        // =========================

        const username =
            document.getElementById("username")
                .value
                .trim();

        const password =
            document.getElementById("password")
                .value;


        // =========================
        // BASIC VALIDATION
        // =========================

        if (!username || !password) {

            loginMessage.textContent =
                "Please enter username and password.";

            return;
        }


        loginMessage.textContent =
            "Logging in...";


        try {

            // =========================
            // SEND LOGIN REQUEST
            // =========================

            const response =
                await fetch(
                    "/admin/login",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            username: username,
                            password: password
                        })
                    }
                );


            const result =
                await response.json();


            // =========================
            // LOGIN SUCCESS
            // =========================

            if (
                response.ok &&
                result.success
            ) {

                loginMessage.textContent =
                    "Login successful.";


                // Open admin dashboard

                window.location.href =
                    "/admin";


                return;
            }


            // =========================
            // LOGIN FAILED
            // =========================

            loginMessage.textContent =
                "Invalid username or password.";


        } catch (error) {

            console.error(
                "Login Error:",
                error
            );


            loginMessage.textContent =
                "Unable to connect to the server.";

        }

    }
);