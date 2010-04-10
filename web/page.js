var slingshot;

function watch_status() {
  slingshot.status(function(data) {
    try {
      $('#status').text('Port: ' + data.port).removeClass('error-string');
    }
    catch(e) {
      $('#status').text('The server is offline').addClass('error-string');
    }
  });
}

function recieve_messages() {
  slingshot.receive({}, function(data) {
    try {
      $('#message_count').text('(' + data.length + ')');
    }
    catch(e) {
      $('#status').text('The server is offline').addClass('error-string');
    }
  });
}


$(window).ready(
  function() {
    slingshot = new SlingshotSMS();
    setTimeout("watch_status()", 500);
    setTimeout("recieve_messages()", 500);
    setInterval("watch_status()", 50000);
    setInterval("recieve_messages())", 50000);
  }
);
