USE user_management;
SELECT * FROM users;
DESCRIBE users;


CREATE TABLE users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    firstName VARCHAR(50),
    lastName VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE
);



CREATE TABLE rental_units (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),  -- Foreign key to 'users' table
    title VARCHAR(255) NOT NULL,
    description TEXT,
    feature VARCHAR(255),  -- Comma-separated list of features
    price DECIMAL(10, 2) NOT NULL,
    post_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(username)
);

CREATE TABLE reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),  -- Foreign key to 'users' table
    rental_id INT,  -- Foreign key to 'rental_units' table
    rating ENUM('Excellent', 'Good', 'Fair', 'Poor') NOT NULL,
    description TEXT,
    review_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(username),
    FOREIGN KEY (rental_id) REFERENCES rental_units(rental_id),
    UNIQUE (user_id, rental_id)  -- Ensures one review per user per rental
);

use rental_management;
SELECT * FROM rental_management;
SELECT feature, MAX(price) AS max_price 
FROM rental_units 
GROUP BY feature;


SELECT r.user_id, r.title
FROM rental_units r
JOIN reviews rv ON r.rental_id = rv.rental_id
WHERE rv.rating = 'Poor'
AND NOT EXISTS (
    SELECT 1
    FROM reviews rv2
    WHERE rv2.rental_id = rv.rental_id AND rv2.rating != 'Poor'
);





SELECT 
    r.rental_id, 
    r.title, 
    r.description, 
    r.feature, 
    r.price
FROM 
    rental_units r
JOIN 
    reviews rv 
ON 
    r.rental_id = rv.rental_id
WHERE 
    r.user_id = 'user123'  -- Replace 'user123' with the actual user_id
GROUP BY 
    r.rental_id, r.title, r.description, r.feature, r.price
HAVING 
    COUNT(CASE WHEN rv.rating NOT IN ('Excellent', 'Good') THEN 1 END) = 0;
