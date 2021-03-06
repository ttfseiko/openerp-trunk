// Phantomjs openerp helper

function waitFor (ready, callback, timeout, timeoutMessageCallback) {
    timeout = timeout || 10000;
    var start = new Date;

    (function waitLoop() {
        if(new Date - start > timeout) {
            error(timeoutMessageCallback ? timeoutMessageCallback() : "Timeout after "+timeout+" ms");
        } else if (ready()) {
            callback();
        } else {
            setTimeout(waitLoop, 250);
        }
    }());
}

function error(message) {
    console.log('error', message);
    phantom.exit(1);
}
function PhantomTest() {
    var self = this;
    this.options = JSON.parse(phantom.args[phantom.args.length-1]);
    this.inject = this.options.inject || [];
    this.timeout = this.options.timeout ? Math.round(parseFloat(this.options.timeout)*1000 - 5000) : 10000;
    this.origin = 'http://localhost';
    this.origin += this.options.port ? ':' + this.options.port : '';

    // ----------------------------------------------------
    // configure phantom and page
    // ----------------------------------------------------
    phantom.addCookie({
        'domain': 'localhost',
        'name': 'session_id',
        'value': this.options.session_id,
    });
    this.page = require('webpage').create();
    this.page.viewportSize = { width: 1366, height: 768 };
    this.page.onError = function(message, trace) {
        var msg = [message];
        if (trace && trace.length) {
            msg.push.apply(msg, trace.map(function (frame) {
                var result = [' at ', frame.file, ':', frame.line];
                if (frame.function) {
                    result.push(' (in ', frame.function, ')');
                }
                return result.join('');
            }));
            msg.push('(leaf frame on top)')
        }
        error(JSON.stringify(msg.join('\n')));
    };
    this.page.onAlert = function(message) {
        error(message);
    };
    this.page.onConsoleMessage = function(message) {
        console.log(message);
    };
    this.page.onLoadFinished = function(status) {
        if (status === "success") {
            for (var k in self.inject) {
                var found = false;
                var v = self.inject[k];
                var need = v;
                var src = v;
                if (v[0]) {
                    need = v[0];
                    src = v[1];
                    found = self.page.evaluate(function(code) {
                        try {
                            return !!eval(code);
                        } catch (e) {
                            return false;
                        }
                    }, need);
                }
                if(!found) {
                    console.log('Injecting', src, 'needed for', need);
                    if(!self.page.injectJs(src)) {
                        error("Cannot inject " + src);
                    }
                }
            }
        }
    };
    setTimeout(function () {
        self.page.evaluate(function () {
            var message = ("Timeout\nhref: " + window.location.href
                + "\nreferrer: " + document.referrer
                + "\n\n" + document.body.innerHTML).replace(/[^a-z0-9\s~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi, "*");
            error(message);
        });
    }, self.timeout);

    // ----------------------------------------------------
    // run test
    // ----------------------------------------------------
    this.run = function(url_path, code, ready) {
        if(self.options.login) {
            var qp = [];
            qp.push('db=' + self.options.db);
            qp.push('login=' + self.options.login);
            qp.push('key=' + self.options.password);
            qp.push('redirect=' + encodeURIComponent(url_path));
            url_path = "/login?" + qp.join('&');
        }
        var url = self.origin + url_path;
        self.page.open(url, function(status) {
            if (status !== 'success') {
                error("failed to load " + url)
            } else {
                console.log('loaded', url, status);
                // process ready
                waitFor(function() {
                    console.log("PhantomTest.run: wait for condition: " + ready);
                    return self.page.evaluate(function (ready) {
                        var r = false;
                        try {
                            console.log("page.evaluate eval expr:", ready);
                            r = !!eval(ready);
                        } catch(ex) { 
                        }
                        console.log("page.evaluate eval result:", r);
                        return r;
                    }, ready);
                // run test
                }, function() {
                    console.log("PhantomTest.run: condition statified, executing: " + code);
                    self.page.evaluate(function (code) { return eval(code); }, code);
                    console.log("PhantomTest.run: execution launched, waiting for console.log('ok')...");
                });
            }
        });
    };
}

// js mode or jsfile mode
if(phantom.args.length === 1) {
    pt = new PhantomTest();
    pt.run(pt.options.url_path, pt.options.code, pt.options.ready);
}

// vim:et:
