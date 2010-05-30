/**
 * SlingshotSMS
 * (c) Development Seed 2010
 */

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
    return this;
  },

  reply: function(text) {
    console.log('stub');
    return this;
  },

  remove: function() {
    console.log('stub');
    return this;
  },

  tag: function() {
    console.log('stub');
    return this;
  },
}
