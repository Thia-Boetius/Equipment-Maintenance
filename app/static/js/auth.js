(function () {
    const token = document.body.dataset.token;
    if (!token) return;

    // Decode JWT payload (base64url → JSON)
    function decodeJWT(t) {
        try {
            const base64 = t.split('.')[1]
                .replace(/-/g, '+')
                .replace(/_/g, '/');
            return JSON.parse(atob(base64));
        } catch (e) {
            return null;
        }
    }

    // Verify token is not expired
    function isExpired(payload) {
        if (!payload || !payload.exp) return true;
        return payload.exp * 1000 < Date.now();
    }

    const payload = decodeJWT(token);

    if (isExpired(payload)) {
        window.location.href = '/login';
    }
})();
