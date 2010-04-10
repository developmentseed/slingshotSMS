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
      { format: 'json' },
      options
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
      { limit: 200, format: 'json' },
      options
    );
    $.getJSON(
      '/list', options, callback
    );
    console.log('not implemented');
  },

  /**
   * get the modem's status
   */
  status: function(callback) {
    console.log(callback);
    $.getJSON(
      '/status', callback
    );
  }
};
