// Hamburger menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main');
    const body = document.body;

    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('open');
            hamburgerBtn.classList.toggle('active');
        });

        // Close menu when a nav item is clicked — navigate in same tab to avoid opening new tabs on some mobile browsers
        const navItems = document.querySelectorAll('.nav-item, .logout-btn');
        navItems.forEach(item => {
            item.addEventListener('click', function(e) {
                // If this is an anchor, navigate using location.assign to force same-tab navigation
                const href = (this.getAttribute && this.getAttribute('href')) || this.href;
                if (href && href !== '#' && !href.startsWith('javascript:')) {
                    e.preventDefault();
                    // Close menu first for smoother UX
                    sidebar.classList.remove('open');
                    hamburgerBtn.classList.remove('active');
                    // Use location.assign so the navigation happens in the same tab
                    window.location.assign(href);
                    return;
                }

                // Fallback: just close the menu
                sidebar.classList.remove('open');
                hamburgerBtn.classList.remove('active');
            });
        });

        // Close menu when clicking outside (anywhere on the page)
        document.addEventListener('click', function(event) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnHamburger = hamburgerBtn.contains(event.target);
            
            // Close menu if clicking outside sidebar and not on hamburger button
            if (!isClickInsideSidebar && !isClickOnHamburger && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                hamburgerBtn.classList.remove('active');
            }
        });

        // Also close on any touch event outside sidebar (for better mobile UX)
        document.addEventListener('touchstart', function(event) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnHamburger = hamburgerBtn.contains(event.target);
            
            if (!isClickInsideSidebar && !isClickOnHamburger && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                hamburgerBtn.classList.remove('active');
            }
        }, { passive: true });

        // Close on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                hamburgerBtn.classList.remove('active');
            }
        });
    }
});
