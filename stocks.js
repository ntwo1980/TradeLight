(function () {
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

    function renderTech(stock)
    {
        var postBody = $('.post-body');

        $('<h3>技术面</h3>').appendTo(postBody)

        var techTable = $([
            '<table>',
                '<thead>',
                    '<tr>',
                        '<th>指标</th>',
                        '<th>数值</th>',
                        '<th>备注</th>',
                    '</tr>',
                '</thead>',
            '</table>'].join('')).appendTo(postBody);

        var techIndicators = [
            ['close', '收盘价', ''],
            ['close_count', '250日内交易日数量', ''],
            ['ma42', '42日均线', ''],
            ['ma120', '120日均线', ''],
            ['ma250', '250日均线', ''],
            ['max10', '10内最高价', ''],
            ['min10', '10内最低价', ''],
            ['atr10', 'ATR10', ''],
            ['l_slop', '22日EMA斜率', ''],
            ['l_pvalue', '22日EMA斜率pvalue', ''],
            ['l_stderror', '22日EMA斜率stderror', '']
        ];


        $($.map(techIndicators, function(indicator){
            return [
                '<tr>',
                    '<td>', indicator[1], '</td>',
                    '<td>', stock[indicator[0]], '</td>',
                    '<td>', indicator[2], '</td>',
                '</tr>',
            ].join('');
        }).join('')).appendTo(techTable)
    }

    function renderFund(stock)
    {
        var postBody = $('.post-body');

        $('<h3>基本面</h3>').appendTo(postBody)

        var fundTable = $([
            '<table>',
                '<thead>',
                    '<tr>',
                        '<th>指标</th>',
                        '<th>数值</th>',
                        '<th>排序值</th>',
                    '</tr>',
                '</thead>',
            '</table>'].join('')).appendTo(postBody);

        var fundIndicators = [
            ['mc', '总市值', ''],
            ['cmc', '流通市值', ''],
            ['pe', '市盈率', ''],
            ['pe_lyr', '静态市盈率', ''],
            ['pb', '市净率', ''],
            ['ps', '市销率', ''],
            ['pcf', '市现率', ''],
            ['iop', '运营利润增长率', ''],
        ];

        $($.map(fundIndicators, function(indicator){
            return [
                '<tr>',
                    '<td>', indicator[1], '</td>',
                    '<td>', stock[indicator[0]], '</td>',
                    '<td>', indicator[2], '</td>',
                '</tr>',
            ].join('');
        }).join('')).appendTo(fundTable)
    }

    window.onload = function(){
        var urlVars = getUrlVars(),
            code = urlVars['code'];

        $.getJSON(['../uploads/stocks/', code, '.json'].join(''))
        .done(function(stock) {
            $('.post-title').text([stock.code, ' - ', stock.name].join(''));
            renderTech(stock)
            renderFund(stock)
        })
        .fail(function(jqxhr) {
            if(jqxhr.status == 404)
                $('.post-title').text('Not Found');
        })
    };
})();
