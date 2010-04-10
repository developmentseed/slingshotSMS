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

function add_contact(name, num, photo) {
  var ct = $('#contact-template').clone().appendTo('#contact-list');
  ct.removeAttr('id');
  ct.find('.contact-name').text(name);
  ct.find('.contact-number').text(num);
  ct.find('.contact-photo').attr('src', 'data:image/png;base64,' + photo);
  ct.show();
}

function recieve_contacts() {
  slingshot.contacts({}, function(data) {
      for(var i = 0; i < data.length; i++) {
        add_contact(data[i].FN, data[i].TEL, data[i].PHOTO);
      }
  });
}


$(window).ready(
  function() {
    slingshot = new SlingshotSMS();
    setTimeout("watch_status()", 500);
    setTimeout("recieve_messages()", 500);
    setTimeout("recieve_contacts()", 500);
    setInterval("watch_status()", 50000);
    setInterval("recieve_messages()", 50000);
  }
);
