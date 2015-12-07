var fs = require('fs');

var outfile = __dirname + '/hosts.json';

// number of hosts to generate
var qty = 45; 

// max jobs total
var maxtotal = 10;

// max checkin seconds
var maxseconds = 600; 

var hosts = [];



for(i = 1; i <= qty; i++) {
	var total = getRandomInt(0,maxtotal);
	var errors = getRandomInt(0,total);
	var host = {
		id: i,
		hostname: 'node-' + i + '.cluster.demo',
		errors: errors,
		total: total
	}
	hosts.push(host);
}

fs.writeFile(outfile, JSON.stringify(hosts, null, 2), function(err) {
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