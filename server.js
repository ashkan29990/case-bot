const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());

app.get('/search', async (req, res) => {
    const query = req.query.q;
    if (!query) {
        return res.status(400).json({ error: 'query required' });
    }
    
    try {
        const response = await axios.get('https://edaalat.org/request/cases', {
            params: { q: query },
            headers: { 
                'Referer': 'https://edaalat.org/',
                'User-Agent': 'Mozilla/5.0'
            },
            timeout: 30000
        });
        res.json(response.data);
    } catch (error) {
        console.error('Error:', error.message);
        res.status(500).json({ error: 'Server error: ' + error.message });
    }
});

app.get('/', (req, res) => {
    res.json({ status: 'OK', message: 'Case search proxy is running' });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
