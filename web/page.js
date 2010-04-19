var slingshot, actions = [];

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

/**
 * @param name The contact's name
 * @param num The contact's number
 * @param photo A base64-encoded photo of the contact
 */
function add_contact(name, num, photo) {
  var ct = $('#contact-template').clone().appendTo('#contact-list');
  ct.removeAttr('id');
  ct.find('.contact-name').text(name);
  ct.find('.contact-number').text(num);
  ct.find('.contact-photo').attr('src', 'data:image/png;base64,' + photo);
  ct.show();
}

/**
 * add_message
 */
function add_message(text, num) {
  // TODO: clear out message-list instead of appending to it
  var ct = $('#message-template').clone().appendTo('#message-list');
  ct.removeAttr('id');
  ct.find('.message-text').text(text);
  ct.find('.message-number').text(num);
  ct.show();
}

/**
 * Recieve contacts from the backend and add
 * them to the contact list
 */
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

    /**
     * Start watching for new messages
     */
    setTimeout("watch_status()", 500);
    setTimeout("receive_messages()", 500);
    setTimeout("receive_contacts()", 500);
    setInterval("watch_status()", 50000);
    setInterval("receive_messages()", 50000);

    /**
     * Add a new action and redraw the actions list
     */
    $('#add_action').click(function() {
      var action_text = $('#action_text').val();
      var new_action = eval('action = ' + action_text);
      actions.push(new_action);
      for(var i = 0; i < actions.length; i++) {
        $('#action-list').append("<li>" + actions[i])
      }
      return false;
    });

    /**
     * TODO: replace with actual names
     */
    var data = "Core Selectors Attributes Traversing Manipulation CSS Events Effects Ajax Utilities".split(" ");
    $('#message_to').autocomplete('/contact_list',
      {
        multiple: true
      }
    );

    /**
     * 160 character notifier
     */
    $('#message_text').keyup(
      function() {
        var chars_remaining = 160 - $(this).val().length;
        if(chars_remaining < 0) {
          $('#message_chars').addClass('error-string');
        } else {
          $('#message_chars').removeClass('error-string');
        }
        $('#message_chars_remaining').text(chars_remaining);
      }
    );

  }
);
