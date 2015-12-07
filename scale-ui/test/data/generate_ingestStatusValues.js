var fs = require('fs');
var moment = require('moment');

var outfile = __dirname + '/values.json';

// number of values to generate
var qty = 14*24;

// max files total
var maxfiles = 160;

// min and max file size
var minsize = 40000;
var maxsize = 6000000;

var values = [];

var initialTime = '2015-10-05T00:00:00Z';

for(i = 0; i <= qty; i++) {
	var time = moment.utc(initialTime).add(i,'hours').format('YYYY-MM-DD[T]HH:mm:SS[Z]');
	var files = getRandomInt(0,maxfiles);
	var size = getRandomInt(minsize,maxsize);
	var file = {
		time: time,
		files: files,
		size: size
	};
	values.push(file);
}

fs.writeFile(outfile, JSON.stringify(values, null, 2), function(err) {
        if (err){
            console.log('Error writing file: ' + err);
        }
        else {
            console.log('Wrote JSON file to ' + outfile);
        }
    });

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}