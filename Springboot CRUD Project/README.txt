Before running the project, be sure to change the 'spring.datasource.password' value found in the 'src/main/resources/application.properties' file to the password you set up pgAdmin with.

Upon running the project, go to hoppscotch.io. Here, you can access the database using http://localhost:8080/

http://localhost:8080/ with the GET method returns a list of every item in the database.

http://localhost:8080/ with the POST method lets you add an item to the database.
Request body format:

{
   "name" : "product name",
   "description" : "product description"
   "price" : Any integer (no quote marks)
}

http://localhost:8080/{id} with the GET method returns a single item from the database if an item with the corresponding ID exists.

http://localhost:8080/{id} with the DELETE method deletes the item with the correponding ID if it exists.

A update item function can be implemented from the ProductService.java and ProductController.java files.

The SQL script can be found at src/main/resources/db/migration, called 'V1__Create_Table.sql.
To ensure that changes to the script are reflected in the program, be sure to delete the old table before updating it.

