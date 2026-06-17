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
