const Imap = require('./node_modules/imap');
const { simpleParser } = require('./node_modules/mailparser');

const imap = new Imap({
  user: 'Clawcliff@gmail.com',
  password: 'zpon bjsp dnfx tkdy',
  host: 'imap.gmail.com',
  port: 993,
  tls: true,
  tlsOptions: { rejectUnauthorized: false }
});

function openInbox(cb) {
  imap.openBox('INBOX', false, cb);
}

imap.once('ready', function() {
  openInbox(function(err, box) {
    if (err) { console.log(JSON.stringify({ error: 'OPENBOX: ' + err.message })); imap.end(); return; }

    imap.search(['UNSEEN'], function(err, results) {
      if (err) { console.log(JSON.stringify({ error: 'SEARCH: ' + err.message })); imap.end(); return; }

      if (!results || results.length === 0) {
        console.log(JSON.stringify({ count: 0, messages: [] }));
        imap.end();
        return;
      }

      const messages = [];
      let parsed_count = 0;
      const f = imap.fetch(results, { bodies: '', markSeen: true });

      f.on('message', function(msg, seqno) {
        let buffer = '';
        msg.on('body', function(stream) {
          stream.on('data', function(chunk) { buffer += chunk.toString('utf8'); });
          stream.once('end', function() {
            simpleParser(buffer, (err, parsed) => {
              parsed_count++;
              if (err) { messages.push({ error: err.message }); return; }
              messages.push({
                from: parsed.from ? parsed.from.text : 'unknown',
                subject: parsed.subject || '(no subject)',
                date: parsed.date ? parsed.date.toISOString() : 'unknown',
                text: (parsed.text || '').substring(0, 600)
              });
            });
          });
        });
      });

      f.once('error', function(err) { console.log(JSON.stringify({ error: 'FETCH: ' + err.message })); });
      f.once('end', function() {
        setTimeout(() => {
          console.log(JSON.stringify({ count: results.length, messages }));
          imap.end();
        }, 4000);
      });
    });
  });
});

imap.once('error', function(err) { console.log(JSON.stringify({ error: 'IMAP: ' + err.message })); });
imap.connect();
