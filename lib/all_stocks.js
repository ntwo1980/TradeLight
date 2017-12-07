(function () {
    var titles = ['代码', '名称', '评分', '斜率', '高于42日均线',
                  '低于10日高价ATR', '市净率', 'ROIC', '盈利增速排名',
                  '盈利增速' ,'上期盈利增速',  '市盈率'], hideRowsTimer;

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

    function waitForJsLib(callback){
        if(!window.$ || !window._)
            setTimeout(function(){
                waitForJsLib(callback)
            }, 100);
        else
            callback();

    }

    function hideRows()
    {
        var trs = $('table').find("tr:not(:first)"),
            hideDown = $('#hideDown').is(":checked"),
            hideMA = $('#hideMA').is(":checked");
            hideIopDown = $('#hideIopDown').is(":checked"),
            hideGem = $('#hideGem').is(":checked"),
            selectors = [];

        trs.show();
        if(hideDown)
            selectors.push('.down');

        if(hideMA)
            selectors.push('.belowMa');

        if(hideIopDown)
            selectors.push('.iopDown');

        if(hideGem)
            selectors.push('.gem');

        if(selectors.length)
            $(selectors.join(', ')).hide();
    }

    function markRows()
    {
        $('table').find("tr:not(:first)").each(function(index, tr){
            var tr = $(tr),
                tds = tr.find("td");

            var slopTd = tds[3],
                slop = parseFloat($(slopTd).text());
            if(isNaN(slop) || slop < -15)
                tr.addClass('down');

            var maTd = tds[4],
                ma = parseFloat($(maTd).text());
            if(isNaN(ma) || ma < 0)
                tr.addClass('belowMa');

            var iopTd = tds[9],
                iop = parseFloat($(iopTd).text()),
                prevIopTd = tds[10],
                prevIop = parseFloat($(prevIopTd).text());
            if(!isNaN(iop) && !isNaN(prevIop) && iop < prevIop * 0.9)
                tr.addClass('iopDown');

            var codeTd = tds[0],
                code = $(codeTd).text();
            if(code.indexOf('300') == 0)
                tr.addClass('gem');
        });
    }

    waitForJsLib(function(){
        $.getScript( "../../lib/stocks/datatables.js" )
        .done(function( script, textStatus ) {
            $('table th').each(function(index, item){
                $(item).attr('title', titles[index]);
            });


            $('table').DataTable(
                {
                    paging: false,
                    fixedHeader: true,
                    order: [[2, 'desc'], [3, 'desc']],
                    searchDelay: 200
                });

            markRows();
            $('#hideDown, #hideMA, #hideIopDown, #hideGem')
                .change(
                    function(){
                        clearTimeout(hideRowsTimer);
                        hideRowsTimer = setTimeout(hideRows, 1000);
                    });

            $('#hide').show();
            hideRows();
        })
    });
})();
