Overview:

This is a program that will query a database that is filled with exercises, and pick some of the best fitting ones according to user specifications. 

Implementation of Chatbot:

I started with outlining the general prompt of the chatbot, with various steps to run through. Once the chatbot has collected all the user specs and the user confirms them, it will output a query that an if statement will catch, and rather than query chatgpt for a response, the database will be queried. Query string is first parsed for information such as the difficulty and the number of exercises to be stored. This is then put into a query that filters based on some of the user specs. It will only search for exercise that are less than or equal to the specified difficulty. The output from the database is stored in a string, which is then fed to another chatgpt instance that will check if the database response is appropriate given the question it was asked. If it is, then the chatbot will respond with the database response. If not, an error message will be outputted. If at any time the user or chatgpt writes something that is flagged, the entire interaction will be skipped.

Note: I had a hard time determining if the database response was "relevant" to its query, because sometimes the user has a exercise request that is not in the database, but similar ones are. They just might not be exactly what the user asked for, but they are closeish. So, I decided to be pretty lenient, and if the exercises are close to what the user wanted, and worked the muscles they want, it is relevant.

Implementation of Database:
A weavieate collection is created and a schema is formed that matches a JSON file filled with exercise and their info, such as the muscle groups worked, its difficulty, how to perform it, if it can be done at home, etc. Then, the JSON file is read and put into the database.# AI-Powered-Semantic-Search-Agent-Development
