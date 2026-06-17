const express         = require('express');
const router          = express.Router();
const db              = require('../config/db');
const { verifyToken } = require('../middlewares/auth');

// GET /api/dashboard — summary counts and recent tasks
router.get('/', verifyToken, async (req, res) => {
    try {
        const [[{ total_machines }]] = await db.query('SELECT COUNT(*) AS total_machines FROM Machine');
        const [[{ total_tasks }]]    = await db.query('SELECT COUNT(*) AS total_tasks FROM Maintenance_task');

        const [machines_by_status] = await db.query(`
            SELECT s.Description AS status, COUNT(*) AS count
            FROM Machine m
            LEFT JOIN Status s ON m.Status_ID = s.Status_ID
            GROUP BY s.Description
        `);

        const [tasks_by_status] = await db.query(`
            SELECT s.Description AS status, COUNT(*) AS count
            FROM Maintenance_task t
            LEFT JOIN Status s ON t.Status_ID = s.Status_ID
            GROUP BY s.Description
        `);

        const [recent_tasks] = await db.query(`
            SELECT t.Task_ID, t.Date, t.Price, t.Remark,
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
            LIMIT 10
        `);

        res.json({ total_machines, total_tasks, machines_by_status, tasks_by_status, recent_tasks });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
