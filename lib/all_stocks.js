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

    function waitForJquery(callback){
        if(!window.$)
            setTimeout(function(){
                waitForJquery(callback)
            }, 100);
        else
            callback();

    }

    function hideRows()
    {
        var trs = $('table').find("tr:not(:first)"),
            hideDown = $('#hideDown').is(":checked"),
            hideMA = $('#hideMA').is(":checked");

        var hideTrs = $.grep(trs, function(tr){
            if(!hideDown && !hideMA)
                return false;

            var tds = $(tr).find("td");
            if(hideDown)
            {
                var slopTd = tds[3],
                    slop = parseFloat($(slopTd).text());

                if(isNaN(slop) || slop < -15)
                    return true;
            }

            if(hideMA)
            {
                var maTd = tds[4],
                    ma = parseFloat($(maTd).text());

                if(isNaN(ma) || ma < 0)
                    return true;
            }

            return false;
        });

        trs.show();
        $(hideTrs).hide();
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

            $('#hideDown').change(hideRows);

            $('#hide').show();
        })
    });
})();
