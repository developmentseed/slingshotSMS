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

function receive_messages() {
  slingshot.receive({}, function(data) {
    try {
      $('#message_count').text('(' + data.length + ')');
      for(var i = 0; i < data.length; i++) {
        add_message(data[i].text, data[i].sender);
      }
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

function add_message(text, num) {
  var ct = $('#message-template').clone().appendTo('#message-list');
  ct.removeAttr('id');
  ct.find('.message-text').text(text);
  ct.find('.message-number').text(num);
  ct.show();
}

function receive_contacts() {
  slingshot.contacts({}, function(data) {
      for(var i = 0; i < data.length; i++) {
        add_contact(data[i].FN, data[i].TEL, data[i].PHOTO);
      }
  });
}


$(document).ready(
  function() {
    slingshot = new SlingshotSMS();
    setTimeout("watch_status()", 500);
    setTimeout("receive_messages()", 500);
    setTimeout("receive_contacts()", 500);
    setInterval("watch_status()", 50000);
    setInterval("receive_messages()", 50000);

    $('#add_action').click(function() {
      var action_text = $('#action_text').val();
      var new_action = eval('action = ' + action_text);
      new_action();
      return false;
    });


    var data = "Core Selectors Attributes Traversing Manipulation CSS Events Effects Ajax Utilities".split(" ");
    
    $('#message_to').autocomplete('/contact_list',
      {
        multiple: true
      }
    );
  }
);
