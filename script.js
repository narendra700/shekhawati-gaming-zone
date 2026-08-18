// =========================
// MOBILE MENU
// =========================

const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector("nav");

if (menuToggle && nav) {
    menuToggle.addEventListener("click", function () {
        nav.classList.toggle("active");
    });
}


// =========================
// BOOKING FORM
// =========================

const bookingForm = document.getElementById("bookingForm");

if (bookingForm) {

    bookingForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const mobile = document.getElementById("mobile").value.trim();
        const service = document.getElementById("service").value;
        const date = document.getElementById("date").value;
        const time = document.getElementById("time").value;
        const message = document.getElementById("message").value.trim();

        if (!name || !mobile || !service || !date || !time) {
            alert("Please fill all required fields.");
            return;
        }

        try {

            // Send booking to Flask backend
            const response = await fetch("/booking", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    mobile: mobile,
                    service: service,
                    date: date,
                    time: time,
                    message: message
                })

            });

            const result = await response.json();

            if (!result.success) {
                alert("Booking save nahi hui. Please try again.");
                return;
            }


            // =========================
            // OPEN WHATSAPP
            // =========================

            const whatsappNumber = "918000671700";

            const whatsappMessage =
`🎮 SHEKHAWATI GAMING ZONE - BOOKING REQUEST

👤 Name: ${name}
📱 Mobile: ${mobile}
🎮 Service: ${service}
📅 Date: ${date}
⏰ Time: ${time}
📝 Message: ${message || "No special request"}

Please confirm my booking.`;

            const whatsappURL =
                "https://wa.me/" +
                whatsappNumber +
                "?text=" +
                encodeURIComponent(whatsappMessage);

            window.location.href = whatsappURL;

        } catch (error) {

            console.error("Booking Error:", error);

            alert(
                "Backend se connection nahi ho pa raha. " +
                "Please make sure Flask server is running."
            );

        }

    });

}