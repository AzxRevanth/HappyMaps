const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const app = express();
const PORT = 5000;

app.use(cors({
  origin: '*' // Or specify your frontend URL
}));

// MongoDB connection
mongoose.connect('mongodb+srv://piyushrathi105:19QXv6uNNlARGBiy@cluster0.grxmynq.mongodb.net/HappyMaps?retryWrites=true&w=majority&appName=Cluster0');


// Connection event listeners (ADD THESE RIGHT AFTER mongoose.connect)
mongoose.connection.on('connected', () => {
  console.log("✅ MongoDB connected!");
});

mongoose.connection.on('error', (err) => {
  console.error("❌ MongoDB connection error:", err);
});

// Define your schema and model
const emotionSchema = new mongoose.Schema({
  place: String,
  latitude: String,
  longitude: String,
  score: String,
});

const Emotion = mongoose.model('Emotion', emotionSchema, 'emotion');

// Routes
app.get('/', (req, res) => {
  res.send('✅ Emotion API is running. Use /api/emotion to get data.');
});

app.get('/api/emotion', async (req, res) => {
  try {
    const data = await Emotion.find();
    res.json(data);
  } catch (error) {
    console.error("Error fetching emotion data:", error);
    res.status(500).json({ error: "Server error" });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});