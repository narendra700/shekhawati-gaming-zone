// =========================================================
// ADMIN DASHBOARD JAVASCRIPT
// =========================================================


// =========================================================
// GLOBAL DATA
// =========================================================

let allBookings = [];

let autoRefreshTimer = null;

let knownBookingIds = new Set();

let firstLoadCompleted = false;

let isLoading = false;


// =========================================================
// NOTIFICATION SOUND
// =========================================================

const notificationSound =
    new Audio(
        "/static/notification_tone_2.wav"
    );

notificationSound.volume = 1.0;


// =========================================================
// PLAY NOTIFICATION SOUND
// =========================================================

function playNotificationSound() {

    notificationSound.currentTime = 0;


    notificationSound
        .play()
        .then(function () {

            console.log(
                "🔔 New booking sound played."
            );

        })
        .catch(function (error) {

            console.warn(
                "Notification sound blocked:",
                error
            );

        });

}


// =========================================================
// CHECK NEW BOOKINGS
// =========================================================

function checkForNewBookings(
    bookings
) {

    const currentBookingIds =
        new Set(
            bookings.map(
                function (booking) {

                    return String(
                        booking.id
                    );

                }
            )
        );


    // -----------------------------------------------------
    // FIRST LOAD
    // -----------------------------------------------------

    if (!firstLoadCompleted) {

        knownBookingIds =
            currentBookingIds;

        firstLoadCompleted = true;

        return;

    }


    let newBookingFound = false;


    bookings.forEach(
        function (booking) {

            const bookingId =
                String(
                    booking.id
                );


            if (
                !knownBookingIds.has(
                    bookingId
                )
            ) {

                newBookingFound = true;

            }

        }
    );


    if (newBookingFound) {

        playNotificationSound();

        showNewBookingNotification();

    }


    knownBookingIds =
        currentBookingIds;

}


// =========================================================
// NEW BOOKING NOTIFICATION
// =========================================================

function showNewBookingNotification() {

    const status =
        document.getElementById(
            "status"
        );


    if (status) {

        status.textContent =
            "🔔 New booking received!";

    }


    if (
        "Notification" in window &&
        Notification.permission ===
            "granted"
    ) {

        try {

            new Notification(
                "🎮 New Booking - Shekhawati Gaming Zone",
                {

                    body:
                        "A new booking has been received.",

                    icon:
                        "/favicon.ico"

                }
            );

        }
        catch (error) {

            console.warn(
                "Browser notification error:",
                error
            );

        }

    }

}


// =========================================================
// REQUEST NOTIFICATION PERMISSION
// =========================================================

function requestNotificationPermission() {

    if (
        !("Notification" in window)
    ) {

        return;

    }


    if (
        Notification.permission ===
        "default"
    ) {

        Notification
            .requestPermission()
            .then(
                function (permission) {

                    console.log(
                        "Notification permission:",
                        permission
                    );

                }
            )
            .catch(
                function (error) {

                    console.warn(
                        "Notification permission error:",
                        error
                    );

                }
            );

    }

}


// =========================================================
// LOAD BOOKINGS
// =========================================================

async function loadBookings(
    showLoading = true
) {

    if (isLoading) {

        return;

    }


    isLoading = true;


    const status =
        document.getElementById(
            "status"
        );


    const table =
        document.getElementById(
            "bookingTable"
        );


    if (!table) {

        isLoading = false;

        return;

    }


    if (
        showLoading &&
        status
    ) {

        status.textContent =
            "Loading bookings...";

    }


    try {

        const response =
            await fetch(
                "/admin/bookings?_=" +
                Date.now(),
                {

                    method:
                        "GET",

                    cache:
                        "no-store",

                    credentials:
                        "same-origin"

                }
            );


        // -------------------------------------------------
        // LOGIN EXPIRED
        // -------------------------------------------------

        if (
            response.status === 401
        ) {

            window.location.href =
                "/admin/login";

            return;

        }


        if (!response.ok) {

            throw new Error(
                "Server response: " +
                response.status
            );

        }


        const bookings =
            await response.json();


        if (
            !Array.isArray(
                bookings
            )
        ) {

            throw new Error(
                "Invalid booking data."
            );

        }


        // -------------------------------------------------
        // NEW BOOKING CHECK
        // -------------------------------------------------

        checkForNewBookings(
            bookings
        );


        // -------------------------------------------------
        // SAVE GLOBAL BOOKINGS
        // -------------------------------------------------

        allBookings =
            bookings;


        // -------------------------------------------------
        // TOTAL BOOKINGS
        // -------------------------------------------------

        const totalBookings =
            document.getElementById(
                "totalBookings"
            );


        if (totalBookings) {

            totalBookings.textContent =
                bookings.length;

        }


        // -------------------------------------------------
        // STATUS COUNTERS
        // -------------------------------------------------

        updateStatusCounters(
            bookings
        );


        // -------------------------------------------------
        // FILTER VALUES
        // -------------------------------------------------

        const searchInput =
            document.getElementById(
                "searchInput"
            );


        const dateFilter =
            document.getElementById(
                "dateFilter"
            );


        const searchText =
            searchInput
                ? searchInput.value
                    .trim()
                    .toLowerCase()
                : "";


        const selectedDate =
            dateFilter
                ? dateFilter.value
                : "";


        if (
            searchText ||
            selectedDate
        ) {

            filterBookings();

        }
        else {

            displayBookings(
                bookings
            );

        }


        if (
            showLoading &&
            status
        ) {

            status.textContent =
                "Bookings loaded successfully.";

        }

    }
    catch (error) {

        console.error(
            "Booking Error:",
            error
        );


        if (status) {

            status.textContent =
                "Unable to load bookings.";

        }

    }
    finally {

        isLoading = false;

    }

}


// =========================================================
// MANUAL REFRESH
// =========================================================

function manualRefresh() {

    const status =
        document.getElementById(
            "status"
        );


    if (status) {

        status.textContent =
            "🔄 Refreshing bookings...";

    }


    loadBookings(false);

}


// =========================================================
// STATUS COUNTERS
// =========================================================

function updateStatusCounters(
    bookings
) {

    let pendingCount = 0;

    let confirmedCount = 0;

    let completedCount = 0;

    let cancelledCount = 0;


    bookings.forEach(
        function (booking) {

            const bookingStatus =
                booking.status ||
                "Pending";


            if (
                bookingStatus ===
                "Pending"
            ) {

                pendingCount++;

            }

            else if (
                bookingStatus ===
                "Confirmed"
            ) {

                confirmedCount++;

            }

            else if (
                bookingStatus ===
                "Completed"
            ) {

                completedCount++;

            }

            else if (
                bookingStatus ===
                "Cancelled"
            ) {

                cancelledCount++;

            }

        }
    );


    setText(
        "pendingBookings",
        pendingCount
    );


    setText(
        "confirmedBookings",
        confirmedCount
    );


    setText(
        "completedBookings",
        completedCount
    );


    setText(
        "cancelledBookings",
        cancelledCount
    );

}


// =========================================================
// SAFE TEXT SETTER
// =========================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (element) {

        element.textContent =
            value;

    }

}


// =========================================================
// DISPLAY BOOKINGS
// =========================================================

function displayBookings(
    bookings
) {

    const table =
        document.getElementById(
            "bookingTable"
        );


    if (!table) {

        return;

    }


    table.innerHTML = "";


    if (
        bookings.length === 0
    ) {

        table.innerHTML = `

            <tr>

                <td
                    colspan="10"
                    class="empty"
                >
                    No bookings found.
                </td>

            </tr>

        `;

        return;

    }


    bookings.forEach(
        function (booking) {

            const row =
                document.createElement(
                    "tr"
                );


            const currentStatus =
                booking.status ||
                "Pending";


            row.innerHTML = `

                <td>
                    ${escapeHtml(
                        booking.id
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.name
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.mobile
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.service
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.date
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.time
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.received_at ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        booking.message ||
                        "-"
                    )}
                </td>

                <td>

                    <select
                        class="status-select"
                        data-id="${Number(
                            booking.id
                        )}"
                    >

                        <option
                            value="Pending"
                            ${
                                currentStatus ===
                                "Pending"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Pending
                        </option>

                        <option
                            value="Confirmed"
                            ${
                                currentStatus ===
                                "Confirmed"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Confirmed
                        </option>

                        <option
                            value="Completed"
                            ${
                                currentStatus ===
                                "Completed"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Completed
                        </option>

                        <option
                            value="Cancelled"
                            ${
                                currentStatus ===
                                "Cancelled"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Cancelled
                        </option>

                    </select>

                </td>

                <td>

                    <button
                        class="view-btn"
                        data-id="${Number(
                            booking.id
                        )}"
                    >
                        👁️ View
                    </button>

                    <button
                        class="delete-btn"
                        data-id="${Number(
                            booking.id
                        )}"
                    >
                        🗑️ Delete
                    </button>

                </td>

            `;


            table.appendChild(
                row
            );

        }
    );


    // =====================================================
    // STATUS EVENTS
    // =====================================================

    table
        .querySelectorAll(
            ".status-select"
        )
        .forEach(
            function (select) {

                select.addEventListener(
                    "change",
                    function () {

                        updateStatus(
                            this.dataset.id,
                            this.value
                        );

                    }
                );

            }
        );


    // =====================================================
    // VIEW EVENTS
    // =====================================================

    table
        .querySelectorAll(
            ".view-btn"
        )
        .forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        viewBooking(
                            this.dataset.id
                        );

                    }
                );

            }
        );


    // =====================================================
    // DELETE EVENTS
    // =====================================================

    table
        .querySelectorAll(
            ".delete-btn"
        )
        .forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        deleteBooking(
                            this.dataset.id
                        );

                    }
                );

            }
        );

}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// =========================================================
// VIEW BOOKING
// =========================================================

function viewBooking(
    id
) {

    const booking =
        allBookings.find(
            function (item) {

                return Number(
                    item.id
                ) === Number(id);

            }
        );


    if (!booking) {

        alert(
            "Booking details not found."
        );

        return;

    }


    setText(
        "viewId",
        booking.id || "-"
    );


    setText(
        "viewName",
        booking.name || "-"
    );


    setText(
        "viewMobile",
        booking.mobile || "-"
    );


    setText(
        "viewService",
        booking.service || "-"
    );


    setText(
        "viewDate",
        booking.date || "-"
    );


    setText(
        "viewTime",
        booking.time || "-"
    );


    setText(
        "viewReceivedAt",
        booking.received_at || "-"
    );


    setText(
        "viewStatus",
        booking.status || "Pending"
    );


    setText(
        "viewMessage",
        booking.message || "-"
    );


    const modal =
        document.getElementById(
            "bookingModal"
        );


    if (modal) {

        modal.style.display =
            "flex";

    }

}


// =========================================================
// CLOSE MODAL
// =========================================================

function closeBookingModal() {

    const modal =
        document.getElementById(
            "bookingModal"
        );


    if (modal) {

        modal.style.display =
            "none";

    }

}


// =========================================================
// MODAL CLICK
// =========================================================

window.addEventListener(
    "click",
    function (event) {

        const modal =
            document.getElementById(
                "bookingModal"
            );


        if (
            event.target ===
            modal
        ) {

            closeBookingModal();

        }

    }
);


// =========================================================
// ESC KEY
// =========================================================

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key ===
            "Escape"
        ) {

            closeBookingModal();

        }

    }
);


// =========================================================
// FILTER BOOKINGS
// =========================================================

function filterBookings() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );


    const dateFilter =
        document.getElementById(
            "dateFilter"
        );


    const searchText =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";


    const selectedDate =
        dateFilter
            ? dateFilter.value
            : "";


    const filteredBookings =
        allBookings.filter(
            function (booking) {

                const name =
                    String(
                        booking.name ||
                        ""
                    ).toLowerCase();


                const mobile =
                    String(
                        booking.mobile ||
                        ""
                    ).toLowerCase();


                const service =
                    String(
                        booking.service ||
                        ""
                    ).toLowerCase();


                const message =
                    String(
                        booking.message ||
                        ""
                    ).toLowerCase();


                const receivedAt =
                    String(
                        booking.received_at ||
                        ""
                    ).toLowerCase();


                const matchesSearch =
                    !searchText ||

                    name.includes(
                        searchText
                    ) ||

                    mobile.includes(
                        searchText
                    ) ||

                    service.includes(
                        searchText
                    ) ||

                    message.includes(
                        searchText
                    ) ||

                    receivedAt.includes(
                        searchText
                    );


                const matchesDate =
                    !selectedDate ||

                    booking.date ===
                    selectedDate;


                return (
                    matchesSearch &&
                    matchesDate
                );

            }
        );


    displayBookings(
        filteredBookings
    );


    const status =
        document.getElementById(
            "status"
        );


    if (
        status &&
        (
            searchText ||
            selectedDate
        )
    ) {

        status.textContent =
            filteredBookings.length +
            " booking(s) found.";

    }

}


// =========================================================
// CLEAR FILTERS
// =========================================================

function clearFilters() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );


    const dateFilter =
        document.getElementById(
            "dateFilter"
        );


    if (searchInput) {

        searchInput.value =
            "";

    }


    if (dateFilter) {

        dateFilter.value =
            "";

    }


    displayBookings(
        allBookings
    );


    const status =
        document.getElementById(
            "status"
        );


    if (status) {

        status.textContent =
            "Bookings loaded successfully.";

    }

}


// =========================================================
// UPDATE STATUS
// =========================================================

async function updateStatus(
    id,
    newStatus
) {

    try {

        const response =
            await fetch(
                `/admin/bookings/${id}/status`,
                {

                    method:
                        "PUT",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            status:
                                newStatus

                        })

                }
            );


        if (
            response.status ===
            401
        ) {

            window.location.href =
                "/admin/login";

            return;

        }


        const result =
            await response.json();


        if (
            !response.ok ||
            !result.success
        ) {

            alert(
                result.message ||
                "Failed to update booking status."
            );

            return;

        }


        allBookings.forEach(
            function (booking) {

                if (
                    Number(
                        booking.id
                    ) === Number(id)
                ) {

                    booking.status =
                        newStatus;

                }

            }
        );


        updateStatusCounters(
            allBookings
        );


        filterBookings();


        const status =
            document.getElementById(
                "status"
            );


        if (status) {

            status.textContent =
                "Booking status updated successfully.";

        }

    }
    catch (error) {

        console.error(
            "Status Update Error:",
            error
        );


        alert(
            "Unable to connect to the server."
        );

    }

}


// =========================================================
// DELETE BOOKING
// =========================================================

async function deleteBooking(
    id
) {

    const confirmDelete =
        confirm(
            "Are you sure you want to delete this booking?"
        );


    if (!confirmDelete) {

        return;

    }


    try {

        const response =
            await fetch(
                `/admin/bookings/${id}`,
                {

                    method:
                        "DELETE",

                    credentials:
                        "same-origin"

                }
            );


        if (
            response.status ===
            401
        ) {

            window.location.href =
                "/admin/login";

            return;

        }


        const result =
            await response.json();


        if (
            !response.ok ||
            !result.success
        ) {

            alert(
                result.message ||
                "Failed to delete booking."
            );

            return;

        }


        allBookings =
            allBookings.filter(
                function (booking) {

                    return Number(
                        booking.id
                    ) !== Number(id);

                }
            );


        knownBookingIds.delete(
            String(id)
        );


        const totalBookings =
            document.getElementById(
                "totalBookings"
            );


        if (totalBookings) {

            totalBookings.textContent =
                allBookings.length;

        }


        updateStatusCounters(
            allBookings
        );


        filterBookings();


        const status =
            document.getElementById(
                "status"
            );


        if (status) {

            status.textContent =
                "Booking deleted successfully.";

        }

    }
    catch (error) {

        console.error(
            "Delete Error:",
            error
        );


        alert(
            "Unable to connect to the server."
        );

    }

}


// =========================================================
// LOGOUT
// =========================================================

async function logoutAdmin() {

    const confirmLogout = confirm(
        "Are you sure you want to logout?"
    );

    if (!confirmLogout) {
        return;
    }

    try {

        const response = await fetch("/admin/logout", {
            method: "POST",
            credentials: "same-origin"
        });

        if (!response.ok) {
            alert("Failed to logout.");
            return;
        }

        if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
        }

        // Redirect to admin login
        window.location.replace("/admin/login");

    } catch (error) {

        console.error("Logout Error:", error);

        alert("Unable to connect to the server.");
    }
}


// =========================================================
// DOM READY
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const searchInput =
            document.getElementById(
                "searchInput"
            );


        const dateFilter =
            document.getElementById(
                "dateFilter"
            );


        if (searchInput) {

            searchInput.addEventListener(
                "input",
                filterBookings
            );

        }


        if (dateFilter) {

            dateFilter.addEventListener(
                "change",
                filterBookings
            );

        }


        requestNotificationPermission();

    }
);


// =========================================================
// INITIAL LOAD
// =========================================================

loadBookings(true);


// =========================================================
// AUTO REFRESH
// EVERY 5 SECONDS
// =========================================================

autoRefreshTimer =
    setInterval(
        function () {

            loadBookings(false);

        },
        5000
    );