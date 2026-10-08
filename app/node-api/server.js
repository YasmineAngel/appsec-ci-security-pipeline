// Practice app - FIXED version (was deliberately vulnerable). Never deploy.
const http = require("http");
const _ = require("lodash");

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");
  // FIX 5: read the input as a number instead of running it as code with eval().
  const n = Number(url.searchParams.get("n") || "0");
  res.end(_.toString(n * 2));
});

server.listen(3000);