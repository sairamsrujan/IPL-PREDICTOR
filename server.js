const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const axios = require('axios');
const { MongoClient } = require('mongodb');
const path=require('path');
const bcrypt = require('bcryptjs'); // For password hashing
const jwt = require('jsonwebtoken'); 

const app = express();
const PORT = 3000;

app.use(express.static(path.join(__dirname,'public')));

// MongoDB Configuration
const MONGO_URI = 'mongodb://localhost:27017';
const DATABASE_NAME = 'IPL';
const COLLECTION_NAME = 'cd';
const COLLECTION_NAME_1="users";

// Connect to MongoDB
let db, collection,userCollection;
MongoClient.connect(MONGO_URI)
  .then(client => {
    db = client.db(DATABASE_NAME);
    collection = db.collection(COLLECTION_NAME);
    console.log('Connected to MongoDB');
    usersCollection = db.collection(COLLECTION_NAME_1);  // Corrected this line
    console.log('Connected to Users Collection');
  })
  .catch(error => {
    console.error('Error connecting to MongoDB:', error);
  });

// Middleware
app.use(bodyParser.json());
app.use(cors());


app.post('/signup', async (req, res) => {
  const { username, password } = req.body;

  try {
    // Check if the user already exists
    const existingUser = await usersCollection.findOne({ username });
    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    // Hash the password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Insert new user into the database
    const newUser = { username, password: hashedPassword };
    await usersCollection.insertOne(newUser);

    // Send response
    res.status(200).json({ message: 'User registered successfully' });
  } catch (error) {
    console.error('Error during signup:', error);
    res.status(500).json({ error: 'An error occurred while signing up' });
  }
});

// Login Route
app.post('/login', async (req, res) => {
  const { username, password } = req.body;

  try {
    // Find user by username
    const user = await usersCollection.findOne({ username });
    if (!user) {
      return res.status(400).json({ error: 'Invalid username or password' });
    }

    // Compare password with hashed password
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ error: 'Invalid username or password' });
    }

    // Generate JWT token
    const token = jwt.sign({ userId: user._id, username: user.username }, 'your_jwt_secret', { expiresIn: '1h' });

    // Send response with token
    res.status(200).json({ message: 'Login successful', token });
  } catch (error) {
    console.error('Error during login:', error);
    res.status(500).json({ error: 'An error occurred while logging in' });
  }
});


// Route to handle predictions
app.get('/', (req, res) => {
  res.redirect("/login.html");
});

// POST Route for predictions
app.post('/predict', async (req, res) => {
  try {
    // Log incoming request
    console.log('Received data from frontend:', req.body);

    // Insert input data into MongoDB
    const inputData = {
      ...req.body,
      timestamp: new Date(), // Add a timestamp for tracking
    };

    await collection.insertOne(inputData);
    console.log('Data inserted into MongoDB:', inputData);

    // Forward the request to Flask (ensure Flask is running and accessible at localhost:5000)
    const flaskResponse = await axios.post('http://localhost:5000/predict', req.body);

    // Log Flask's response
    console.log('Response from Flask:', flaskResponse.data);

    // Assuming Flask returns the following structure:
    // { "batting_team": { "lr1": probability_batting }, "bowling_team": { "lr": probability_bowling } }

    // Get the batting and bowling team probabilities
    const battingTeamProbability = flaskResponse.data.batting_team ? flaskResponse.data.batting_team.winning_probability : undefined;
    const bowlingTeamProbability = flaskResponse.data.bowling_team ? flaskResponse.data.bowling_team.winning_probability : undefined;

    // Prepare response in the format expected by frontend
    const response = {
      batting_team: {
        winning_probability: battingTeamProbability, // Probability of batting team winning
      },
      bowling_team: {
        winning_probability: bowlingTeamProbability, // Probability of bowling team winning
      },
    };

    // Log the response before sending
    console.log('Returning response to frontend:', response);

    // Send the response with win percentages for both teams
    res.status(200).json(response);

  } catch (error) {
    console.error('Error while connecting to Flask or MongoDB:', error.message || error);

    // Send error message to frontend
    res.status(500).json({
      error: 'Failed to fetch prediction from Flask or save data to MongoDB. Please check the backend logs for details.',
    });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Node.js server is running on http://localhost:${PORT}`);
});
