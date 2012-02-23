/*
Copyright (c) 2011, OpenERP S.A.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

niv = (function() {
    var lib = {};

    /*
     * Unmodified John Resig's inheritance
     */
    /*
     * Simple JavaScript Inheritance By John Resig http://ejohn.org/ MIT
     * Licensed.
     */
    // Inspired by base2 and Prototype
    (function() {
        var initializing = false, fnTest = /xyz/.test(function() {
            xyz;
        }) ? /\b_super\b/ : /.*/;
        // The base Class implementation (does nothing)
        this.Class = function() {
        };

        // Create a new Class that inherits from this class
        this.Class.extend = function(prop) {
            var _super = this.prototype;

            // Instantiate a base class (but only create the instance,
            // don't run the init constructor)
            initializing = true;
            var prototype = new this();
            initializing = false;

            // Copy the properties over onto the new prototype
            for ( var name in prop) {
                // Check if we're overwriting an existing function
                prototype[name] = typeof prop[name] == "function"
                        && typeof _super[name] == "function"
                        && fnTest.test(prop[name]) ? (function(name, fn) {
                    return function() {
                        var tmp = this._super;

                        // Add a new ._super() method that is the same method
                        // but on the super-class
                        this._super = _super[name];

                        // The method only need to be bound temporarily, so we
                        // remove it when we're done executing
                        var ret = fn.apply(this, arguments);
                        this._super = tmp;

                        return ret;
                    };
                })(name, prop[name]) : prop[name];
            }

            // The dummy class constructor
            function Class() {
                // All construction is actually done in the init method
                if (!initializing && this.init)
                    this.init.apply(this, arguments);
            }

            // Populate our constructed prototype object
            Class.prototype = prototype;

            // Enforce the constructor to be what we expect
            Class.prototype.constructor = Class;

            // And make this class extendable
            Class.extend = arguments.callee;

            return Class;
        };
    }).call(lib);

    lib.DestroyableMixin = {
        isDestroyed : function() {
            return this.__destroyable_destroyed;
        },
        destroy : function() {
            this.__destroyable_destroyed = true;
        }
    };

    lib.ParentedMixin = _.extend({}, lib.DestroyableMixin, {
        __parented_mixin : true,
        setParent : function(parent) {
            if (this.getParent()) {
                if (this.getParent().__parented_mixin) {
                    this.getParent().__parented_children = _.without(this
                            .getParent().getChildren(), this);
                }
                this.__parented_parent = undefined;
            }
            this.__parented_parent = parent;
            if (parent && parent.__parented_mixin) {
                if (!parent.__parented_children)
                    parent.__parented_children = [];
                parent.__parented_children.push(this);
            }
        },
        getParent : function() {
            return this.__parented_parent;
        },
        getChildren : function() {
            return this.__parented_children ? _.clone(this.__parented_children)
                    : [];
        },
        destroy : function() {
            _.each(this.getChildren(), function(el) {
                el.destroy();
            });
            this.setParent(undefined);
            lib.DestroyableMixin.destroy.call(this);
        }
    });

    /*
     * We steal backbone's events :)
     */
    // (c) 2010-2012 Jeremy Ashkenas, DocumentCloud Inc.
    // Backbone may be freely distributed under the MIT license.
    // For all details and documentation:
    // http://backbonejs.org
    lib.EventDispatcher = lib.Class.extend({

        // Bind an event, specified by a string name, `ev`, to a `callback`
        // function. Passing `"all"` will bind the callback to all events fired.
        on : function(events, callback, context) {
            var ev;
            events = events.split(/\s+/);
            var calls = this._callbacks || (this._callbacks = {});
            while (ev = events.shift()) {
                // Create an immutable callback list, allowing traversal during
                // modification. The tail is an empty object that will always be
                // used
                // as the next node.
                var list = calls[ev] || (calls[ev] = {});
                var tail = list.tail || (list.tail = list.next = {});
                tail.callback = callback;
                tail.context = context;
                list.tail = tail.next = {};
            }
            return this;
        },

        // Remove one or many callbacks. If `context` is null, removes all
        // callbacks
        // with that function. If `callback` is null, removes all callbacks for
        // the
        // event. If `ev` is null, removes all bound callbacks for all events.
        off : function(events, callback, context) {
            var ev, calls, node;
            if (!events) {
                delete this._callbacks;
            } else if (calls = this._callbacks) {
                events = events.split(/\s+/);
                while (ev = events.shift()) {
                    node = calls[ev];
                    delete calls[ev];
                    if (!callback || !node)
                        continue;
                    // Create a new list, omitting the indicated event/context
                    // pairs.
                    while ((node = node.next) && node.next) {
                        if (node.callback === callback
                                && (!context || node.context === context))
                            continue;
                        this.on(ev, node.callback, node.context);
                    }
                }
            }
            return this;
        },

        // Trigger an event, firing all bound callbacks. Callbacks are passed
        // the
        // same arguments as `trigger` is, apart from the event name.
        // Listening for `"all"` passes the true event name as the first
        // argument.
        trigger : function(events) {
            var event, node, calls, tail, args, all, rest;
            if (!(calls = this._callbacks))
                return this;
            all = calls['all'];
            (events = events.split(/\s+/)).push(null);
            // Save references to the current heads & tails.
            while (event = events.shift()) {
                if (all)
                    events.push({
                        next : all.next,
                        tail : all.tail,
                        event : event
                    });
                if (!(node = calls[event]))
                    continue;
                events.push({
                    next : node.next,
                    tail : node.tail
                });
            }
            // Traverse each list, stopping when the saved tail is reached.
            rest = slice.call(arguments, 1);
            while (node = events.pop()) {
                tail = node.tail;
                args = node.event ? [ node.event ].concat(rest) : rest;
                while ((node = node.next) !== tail) {
                    node.callback.apply(node.context || this, args);
                }
            }
            return this;
        },
        bind: function() {
            return this.on.apply(this, arguments);
        },
        unbind: function() {
            return this.on.apply(this, arguments);
        }
    });

    return lib;
})();
