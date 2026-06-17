const express         = require('express');
const router          = require('express').Router();
const db              = require('../config/db');
const { verifyToken } = require('../middlewares/auth');
const { validate }    = require('../middlewares/validate');

const taskSchema = {
    Machine_ID:  { type: 'number', required: true },
    Type_ID:     { type: 'number' },
    Status_ID:   { type: 'number' },
    Date:        { type: 'date',   required: true },
    Remark:      { type: 'string', maxLength: 1000 },
    Price:       { type: 'number', min: 0 },
    Assigned_to: { type: 'number' },
};

// GET /api/maintenance — all tasks with joined details
router.get('/', verifyToken, async (req, res) => {
    try {
        const [rows] = await db.query(`
            SELECT t.*,
                   m.Machine_number, m.Model,
                   c.Name        AS type,
                   s.Description AS status,
                   CONCAT(e.First_name, ' ', e.Last_name) AS assigned_to
            FROM Maintenance_task t
            LEFT JOIN Machine  m ON t.Machine_ID  = m.Machine_ID
            LEFT JOIN Category c ON t.Type_ID     = c.Category_ID
            LEFT JOIN Status   s ON t.Status_ID   = s.Status_ID
            LEFT JOIN Employee e ON t.Assigned_to = e.Employee_ID
            ORDER BY t.Date DESC
        `);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET /api/maintenance/:id
router.get('/:id', verifyToken, async (req, res) => {
    try {
        const [rows] = await db.query(
            `SELECT t.*,
                    m.Machine_number, m.Model,
                    c.Name        AS type,
                    s.Description AS status,
                    CONCAT(e.First_name, ' ', e.Last_name) AS assigned_to
             FROM Maintenance_task t
             LEFT JOIN Machine  m ON t.Machine_ID  = m.Machine_ID
             LEFT JOIN Category c ON t.Type_ID     = c.Category_ID
             LEFT JOIN Status   s ON t.Status_ID   = s.Status_ID
             LEFT JOIN Employee e ON t.Assigned_to = e.Employee_ID
             WHERE t.Task_ID = ?`,
            [req.params.id]
        );
        if (rows.length === 0) return res.status(404).json({ error: 'Task not found' });
        res.json(rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// POST /api/maintenance
router.post('/', verifyToken, validate(taskSchema), async (req, res) => {
    const { Machine_ID, Type_ID, Status_ID, Date, Remark, Price, Assigned_to } = req.body;
    try {
        const [result] = await db.query(
            `INSERT INTO Maintenance_task (Machine_ID, Type_ID, Status_ID, Date, Remark, Price, Assigned_to)
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [Machine_ID, Type_ID, Status_ID, Date, Remark, Price, Assigned_to]
        );
        res.status(201).json({ Task_ID: result.insertId });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
