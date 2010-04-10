/**
 * SlingshotSMS
 * (c) Tom MacWright 2010
 */

var SlingshotSMS = function(opts) {
	this.init(opts);
}

SlingshotSMS.prototype = {
  init: function() {
    console.log('not implemented');
  },
  /**
   * send a message from SlingshotSMS
   * to a cell phone
   */
  send: function(options) {
    $.extend(
      { format: 'json' },
      options
    );
    $.getJSON(
      '/send', options,
      function(data) {
        console.log('not implemented')
      }
    );
    console.log('not implemented');
  },
  /**
   * pull a list of messages from the server
   */
  receive: function(options) {
    $.extend(
      { limit: 200, format: 'json' },
      options
    );
    $.getJSON(
      '/list', options,
      function(data) {
        console.log('not implemented')
      }
    );
    console.log('not implemented');
  }
};
