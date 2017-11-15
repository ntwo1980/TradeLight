(function () {
    function toDecimal(x) {
            if (typeof x === 'string')
                return x;
            var f = parseFloat(x);
            if (isNaN(f)) {
                return x;
            }
            f = Math.round(x*100)/100;
            return f;
    }

    function getUrlVars()
    {
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for(var i = 0; i < hashes.length; i++)
        {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    }

    function waitForJquery(callback)
    {
        if(!window.$)
        {
            setTimeout(function() {  waitForJquery(callback) }, 100);
        }
        else
        {
            callback();
        }
    }

    waitForJquery(function(){
        $.getScript( "../../lib/stocks/datatables.js" )
        .done(function( script, textStatus ) {
            $('table').DataTable(
                {
                    paging: false,
                    fixedHeader: true,
                    order: [[2, 'desc'], [3, 'desc']],
                    searchDelay: 200
                });
        })
    });
})();
