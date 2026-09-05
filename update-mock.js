const fs = require('fs');
const path = require('path');

const mockPath = path.join(__dirname, 'src', 'data', 'mock-data.ts');
let data = fs.readFileSync(mockPath, 'utf8');

// Min/Max bounds for Trivandrum
const MIN_LAT = 8.4800;
const MAX_LAT = 8.5600;
const MIN_LNG = 76.9000;
const MAX_LNG = 76.9800;

data = data.replace(/x:\s*(\d+),\s*y:\s*(\d+)/g, (match, xStr, yStr) => {
    const x = parseInt(xStr);
    const y = parseInt(yStr);
    
    // Scale X to LNG
    const lng = MIN_LNG + ((x - 0) / 900) * (MAX_LNG - MIN_LNG);
    // Scale Y to LAT
    const lat = MAX_LAT - ((y - 0) / 400) * (MAX_LAT - MIN_LAT);
    
    return `x: ${x}, y: ${y}, lat: ${lat.toFixed(5)}, lng: ${lng.toFixed(5)}`;
});

// Update Hospitals/Facilities to Kerala names
data = data.replace(/'City General Hospital'/g, "'KIMS Health Hospital'");
data = data.replace(/'South Telecom Tower'/g, "'BSNL Central Exchange'");
data = data.replace(/'Municipal Water Plant'/g, "'Trivandrum Water Works'");
data = data.replace(/'Hospital'/g, "'KIMS Health Hospital'");
data = data.replace(/'Telecom Tower'/g, "'BSNL Exchange'");
data = data.replace(/'Water Plant'/g, "'Water Treatment Plant'");

fs.writeFileSync(mockPath, data);
console.log('Updated mock-data.ts with Kerala coordinates and facilities.');
