const express      = require('express');
const router       = express.Router();
const db           = require('../config/db');
const { verifyToken } = require('../middlewares/auth');

// GET /api/machines — all machines with joined Brand, Status, Category
router.get('/', verifyToken, async (req, res) => {
    try {
        const [rows] = await db.query(`
            SELECT m.*, b.Name AS brand, s.Description AS status, c.Name AS category
            FROM Machine m
            LEFT JOIN Brand    b ON m.Brand_ID    = b.Brand_ID
            LEFT JOIN Status   s ON m.Status_ID   = s.Status_ID
            LEFT JOIN Category c ON m.Category_ID = c.Category_ID
        `);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/machines/:id
router.get('/:id', verifyToken, async (req, res) => {
    try {
        const [rows] = await db.query(
            `SELECT m.*, b.Name AS brand, s.Description AS status, c.Name AS category
             FROM Machine m
             LEFT JOIN Brand    b ON m.Brand_ID    = b.Brand_ID
             LEFT JOIN Status   s ON m.Status_ID   = s.Status_ID
             LEFT JOIN Category c ON m.Category_ID = c.Category_ID
             WHERE m.Machine_ID = ?`,
            [req.params.id]
        );
        if (rows.length === 0) return res.status(404).json({ error: 'Machine not found' });
        res.json(rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// POST /api/machines
router.post('/', verifyToken, async (req, res) => {
    const { Machine_number, Year, Model, Chasis_number, Plate_number, Mileage, Brand_ID, Status_ID, Category_ID } = req.body;
    try {
        const [result] = await db.query(
            `INSERT INTO Machine (Machine_number, Year, Model, Chasis_number, Plate_number, Mileage, Brand_ID, Status_ID, Category_ID)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [Machine_number, Year, Model, Chasis_number, Plate_number, Mileage, Brand_ID, Status_ID, Category_ID]
        );
        res.status(201).json({ Machine_ID: result.insertId });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
