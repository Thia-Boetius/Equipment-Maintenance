document.addEventListener("DOMContentLoaded", () => {
    const bell = document.getElementById("bell_icon");
    const dropdown = document.getElementById("notification-dropdown");
    const MARGIN = 8;

    function hideDropdown() {
        dropdown.style.display = 'none';
        dropdown.style.position = '';
        dropdown.style.left = '';
        dropdown.style.top = '';
        dropdown.style.right = '';
    }

    function openAndPosition() {
        // show first to allow measurements
        dropdown.style.display = 'block';

        // constrain width
        const maxWidth = Math.min(window.innerWidth - MARGIN * 2, 320);
        dropdown.style.width = maxWidth + 'px';

        const bellRect = bell.getBoundingClientRect();

        // calculate left so dropdown stays on screen
        let left = Math.round(bellRect.right - maxWidth);
        if (left < MARGIN) left = MARGIN;
        if (left + maxWidth > window.innerWidth - MARGIN) left = window.innerWidth - maxWidth - MARGIN;

        // calculate top; place below bell, or above if not enough space
        let top = Math.round(bellRect.bottom + 6);
        const dropdownHeight = dropdown.offsetHeight;
        if (top + dropdownHeight > window.innerHeight - MARGIN) {
            // place above
            top = Math.max(MARGIN, Math.round(bellRect.top - dropdownHeight - 6));
        }

        dropdown.style.position = 'fixed';
        dropdown.style.left = left + 'px';
        dropdown.style.top = top + 'px';
        dropdown.style.right = 'auto';
    }

    bell.addEventListener('click', (e) => {
        e.stopPropagation();
        if (dropdown.style.display === 'block') {
            hideDropdown();
        } else {
            openAndPosition();
        }
    });

    // Close when clicking outside
    document.addEventListener('click', () => {
        hideDropdown();
    });

    // Keep dropdown open when clicking inside it
    dropdown.addEventListener('click', (e) => { e.stopPropagation(); });

    // Reposition on resize/orientation change
    window.addEventListener('resize', () => { if (dropdown.style.display === 'block') openAndPosition(); });
    window.addEventListener('orientationchange', () => { if (dropdown.style.display === 'block') openAndPosition(); });
});