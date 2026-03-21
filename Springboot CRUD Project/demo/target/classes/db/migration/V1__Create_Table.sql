CREATE TABLE if not exists Products(
    id int PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255),
    description varchar(255),
    price int
);