document.addEventListener("DOMContentLoaded", () => {

    const bell = document.getElementById("bell_icon");
    const dropdown = document.getElementById("notification-dropdown");

    bell.addEventListener("click", (e) => {
        e.stopPropagation();

        if(dropdown.style.display === "block"){
            dropdown.style.display = "none";
        } else {
            dropdown.style.display = "block";
        }
    });

    document.addEventListener("click", () => {
        dropdown.style.display = "none";
    });

});

console.log("notifications.js loaded");