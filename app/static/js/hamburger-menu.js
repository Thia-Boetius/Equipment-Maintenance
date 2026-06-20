// Hamburger menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main');
    const body = document.body;

    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            hamburgerBtn.classList.toggle('active');
        });

        // Close menu when a nav item is clicked
        const navItems = document.querySelectorAll('.nav-item, .logout-btn');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                sidebar.classList.remove('open');
                hamburgerBtn.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnHamburger = hamburgerBtn.contains(event.target);
            
            if (!isClickInsideSidebar && !isClickOnHamburger && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                hamburgerBtn.classList.remove('active');
            }
        });
    }
});
