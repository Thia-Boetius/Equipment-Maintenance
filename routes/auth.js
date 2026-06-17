const express          = require('express');
const router           = express.Router();
const jwt              = require('jsonwebtoken');
const db               = require('../config/db');
const { validate }     = require('../middlewares/validate');

const loginSchema = {
    email:    { type: 'string', required: true, maxLength: 255 },
    password: { type: 'string', required: true, maxLength: 255 },
};

// POST /api/auth/login
router.post('/login', validate(loginSchema), async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password are required' });
    }

    try {
        const [rows] = await db.query(
            'SELECT * FROM Employee WHERE email = ?', [email]
        );
        if (rows.length === 0) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        const employee = rows[0];
        const token = jwt.sign(
            { id: employee.Employee_ID, email },
            process.env.JWT_SECRET || 'secret',
            { expiresIn: '8h' }
        );

        res.json({ token, employee });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// POST /api/auth/logout
router.post('/logout', (req, res) => {
    res.json({ message: 'Logged out successfully' });
});

module.exports = router;
