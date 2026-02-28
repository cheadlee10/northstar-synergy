const fs = require('fs');
const path = require('path');
const extract = require('pdf-extract');

const pdfPath = 'C:\\Users\\chead\\.openclaw\\media\\inbound\\ee9a9d73-f87e-4307-bc84-395a9d29deb7.pdf';

const processor = extract.create();

processor.on('complete', (data) => {
  console.log(data.text);
  process.exit(0);
});

processor.on('error', (err) => {
  console.error('Error extracting PDF:', err.message);
  process.exit(1);
});

const stream = fs.createReadStream(pdfPath);
stream.pipe(processor);
