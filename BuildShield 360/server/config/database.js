const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/buildshield360';
    await mongoose.connect(mongoUri, { serverSelectionTimeoutMS: 3000 });
    console.log('MongoDB connected:', mongoose.connection.host);
    return true;
  } catch (err) {
    console.warn('MongoDB unavailable:', err.message);
    console.warn('Using in-memory store. Set MONGODB_URI to use MongoDB.');
    return false;
  }
};

function isConnected() {
  return mongoose.connection.readyState === 1;
}

module.exports = connectDB;
module.exports.isConnected = isConnected;
