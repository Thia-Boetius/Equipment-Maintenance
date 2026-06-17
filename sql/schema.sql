-- Equipment Maintenance database schema

CREATE TABLE IF NOT EXISTS Brand (
    Brand_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name     VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Category (
    Category_ID  INT AUTO_INCREMENT PRIMARY KEY,
    Name         VARCHAR(100) NOT NULL,
    Discription  VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Status (
    Status_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Description VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Department (
    Department_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name          VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Position (
    Position_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Name          VARCHAR(100) NOT NULL,
    Department_ID INT,
    FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID)
);

CREATE TABLE IF NOT EXISTS Employee (
    Employee_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_name  VARCHAR(100) NOT NULL,
    Last_name   VARCHAR(100) NOT NULL DEFAULT '',
    Position_id INT,
    User_UID    VARCHAR(255),
    FOREIGN KEY (Position_id) REFERENCES Position(Position_ID)
);

CREATE TABLE IF NOT EXISTS Machine (
    Machine_ID     INT AUTO_INCREMENT PRIMARY KEY,
    Machine_number VARCHAR(100) NOT NULL,
    Year           DECIMAL(4,0),
    Model          VARCHAR(100),
    Chasis_number  VARCHAR(100),
    Plate_number   VARCHAR(50),
    Mileage        DECIMAL(10,2),
    Brand_ID       INT,
    Status_ID      INT,
    Category_ID    INT,
    FOREIGN KEY (Brand_ID)    REFERENCES Brand(Brand_ID),
    FOREIGN KEY (Status_ID)   REFERENCES Status(Status_ID),
    FOREIGN KEY (Category_ID) REFERENCES Category(Category_ID)
);

CREATE TABLE IF NOT EXISTS Maintenance_task (
    Task_ID     INT AUTO_INCREMENT PRIMARY KEY,
    Machine_ID  INT,
    Type_ID     INT,
    Status_ID   INT,
    Date        DATE NOT NULL,
    Remark      TEXT,
    Price       FLOAT,
    Assigned_to INT,
    FOREIGN KEY (Machine_ID)  REFERENCES Machine(Machine_ID),
    FOREIGN KEY (Type_ID)     REFERENCES Category(Category_ID),
    FOREIGN KEY (Status_ID)   REFERENCES Status(Status_ID),
    FOREIGN KEY (Assigned_to) REFERENCES Employee(Employee_ID)
);

-- ── Seed data ────────────────────────────────────────────────────────────────

INSERT INTO Brand (Name) VALUES
    ('Toyota'),
    ('Mitsubishi'),
    ('Honda'),
    ('Hitachi'),
    ('Doosan');

INSERT INTO Category (Name, Discription) VALUES
    ('Preventive',  'Scheduled maintenance to prevent breakdowns'),
    ('Corrective',  'Repairs after a failure has occurred'),
    ('Inspection',  'Routine inspection and check-up'),
    ('Oil Change',  'Engine oil and filter replacement'),
    ('Tire Service','Tire rotation, replacement, or repair');

INSERT INTO Status (Description) VALUES
    ('Active'),
    ('Inactive'),
    ('Pending'),
    ('Completed'),
    ('Cancelled');

INSERT INTO Department (Name) VALUES
    ('Operations'),
    ('Logistics'),
    ('Maintenance'),
    ('Administration');

INSERT INTO Position (Name, Department_ID) VALUES
    ('Mechanic',          3),
    ('Fleet Manager',     2),
    ('Technician',        3),
    ('Operations Manager',1),
    ('Administrator',     4);

INSERT INTO Employee (First_name, Last_name, Position_id) VALUES
    ('John',  'Doe',    1),
    ('Jane',  'Smith',  2),
    ('Carlos','Perez',  3),
    ('Maria', 'Johnson',4),
    ('Thia',  'Boetius',5);

INSERT INTO Machine (Machine_number, Year, Model, Chasis_number, Plate_number, Mileage, Brand_ID, Status_ID, Category_ID) VALUES
    ('M-001', 2019, 'Land Cruiser', 'JT3HJ85J9P0123456', 'ABC-001', 45230.5, 1, 1, 2),
    ('M-002', 2020, 'L200',         'MMBJNKB40JD123456', 'ABC-002', 31500.0, 2, 1, 2),
    ('M-003', 2018, 'CR-V',         'JHLRD68526C123456', 'ABC-003', 62000.0, 3, 2, 1),
    ('M-004', 2021, 'ZX135US',      'HCMSCELA2N1234567', 'ABC-004',  8200.0, 4, 1, 3),
    ('M-005', 2017, 'DX85R',        'DKFWB123456789012', 'ABC-005', 12400.0, 5, 3, 3);

INSERT INTO Maintenance_task (Machine_ID, Type_ID, Status_ID, Date, Remark, Price, Assigned_to) VALUES
    (1, 4, 4, '2024-01-15', 'Oil and filter replaced',          85.00, 1),
    (1, 3, 4, '2024-03-10', 'Routine inspection completed',     50.00, 3),
    (2, 1, 4, '2024-02-20', 'Scheduled 30,000 km service',     150.00, 1),
    (3, 2, 5, '2024-04-05', 'Cancelled – parts unavailable',     0.00, 2),
    (4, 3, 4, '2024-05-01', 'Hydraulic system check passed',    75.00, 3),
    (5, 5, 4, '2024-05-18', 'Tires rotated and pressure set',   60.00, 1),
    (2, 4, 3, '2024-06-01', 'Oil change scheduled',             85.00, NULL),
    (3, 1, 3, '2024-06-10', 'Annual preventive service due',   200.00, 2);
