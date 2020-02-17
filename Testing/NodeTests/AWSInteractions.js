var AWS = require("aws-sdk");

// Create S3 service object
s3 = new AWS.S3({apiVersion: '2006-03-01'});

// Create the parameters for calling listObjects
var bucketParams = {
  Bucket : 'pci-effciency-project-test',
  StartAfter : 'generator0001/2020-02-17 22:55.json',
  Prefix : 'generator0001',
};

// Call S3 to obtain a list of the objects in the bucket
s3.listObjectsV2(bucketParams, function(err, data) {
  if (err) {
    console.log("Error", err);
  } else {
    console.log("Success", data);
  }
});
