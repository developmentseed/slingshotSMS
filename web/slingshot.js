/**
 * SlingshotSMS
 * (c) Tom MacWright 2010
 */

var SlingshotSMS = function(opts) {
	this.init(opts);
}

SlingshotSMS.prototype = {
  /**
   * Create instance of 
   * SlingshotSMS controller
   */
  init: function() {
    console.log('not implemented');
  },

  /**
   * send a message from SlingshotSMS
   * to a cell phone
   */
  send: function(options, callback) {
    $.extend(
      { format: 'json' }, options
    );
    $.getJSON(
      '/send', options, callback
    );
    console.log('not implemented');
  },

  /**
   * pull a list of messages from the server
   */
  receive: function(options, callback) {
    $.extend(
      options, { limit: 200, format: 'json' }
    );
    $.getJSON(
      '/list', options, callback
    );
  },

  /**
   * get the modem's status
   */
  status: function(callback) {
    $.getJSON(
      '/status', callback
    );
  },

  /**
   * pull a list of contacts from the server
   */
  contacts: function(options, callback) {
    $.extend(
      options, { limit: 200, format: 'json' }
    );
    $.getJSON(
      '/contact_list', options, callback
    );
  },
};

var Message = function(opts) {
	this.init(opts);
}

Message.prototype = {
  /**
   * Create instance of 
   * SlingshotSMS controller
   */
  init: function(text, sender) {
    this.text = text;
    this.sender = sender;
  },

  forward: function(num) {
    console.log('stub');
  },

  reply: function(text) {
    console.log('stub');
  },

  remove: function() {
    console.log('stub');
  },

  tag: function() {
    console.log('stub');
  },
}
