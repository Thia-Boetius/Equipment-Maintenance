const express = require('express');
const app = express();

const authRoutes        = require('./routes/auth');
const machineRoutes     = require('./routes/machines');
const maintenanceRoutes = require('./routes/maintenance');
const dashboardRoutes   = require('./routes/dashboard');

app.use(express.json());

app.use('/api/auth',        authRoutes);
app.use('/api/machines',    machineRoutes);
app.use('/api/maintenance', maintenanceRoutes);
app.use('/api/dashboard',   dashboardRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

module.exports = app;
