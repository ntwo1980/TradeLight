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
            ['ma42', '42日均线', function(stock){ return '收盘价高于均线' + toDecimal(((stock['close'] - stock['ma42']) / stock['ma42']) * 100) + '%' }],
            ['ma120', '120日均线', function(stock){ return '收盘价高于均线' + toDecimal(((stock['close'] - stock['ma120']) / stock['ma120']) * 100) + '%' }],
            ['ma250', '250日均线', function(stock){ return '收盘价高于均线' + toDecimal(((stock['close'] - stock['ma250']) / stock['ma250']) * 100) + '%' }],
            ['max10', '10内最高价', function(stock){ return '收盘价低于最高价' + toDecimal(((stock['max10'] - stock['close']) / stock['max10']) * 100) + '%' }],
            ['min10', '10内最低价', function(stock){ return '收盘价高于最低价' + toDecimal(((stock['close'] - stock['min10']) / stock['min10']) * 100) + '%' }],
            ['atr10', 'ATR10', function(stock){ return '最高价下跌<span style="font-size:150%; padding: 0 5px;">' + toDecimal((stock['max10'] - stock['close']) / stock['atr10']) + '</span>个atr10' }],
            ['l_slop', '22日EMA斜率', function(stock){ return stock['l_pvalue'] < 0.001 && stock['l_stderror'] < 7 ? '' : '无效' }],
            ['l_pvalue', '22日EMA斜率pvalue', ''],
            ['l_stderror', '22日EMA斜率stderror', '']
        ];


        $($.map(techIndicators, function(indicator){
            return [
                '<tr>',
                    '<td>', indicator[1], '</td>',
                    '<td>', toDecimal(stock[indicator[0]]), '</td>',
                    '<td>', typeof indicator[2] === 'function' ? indicator[2](stock) : indicator[2], '</td>',
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
            ['mc', '总市值', true],
            ['cmc', '流通市值', true],
            ['pe', '市盈率', true],
            ['pe_lyr', '静态市盈率', true],
            ['pb', '市净率', true],
            ['ps', '市销率', true],
            ['pcf', '市现率', true],
            ['iop', '营业利润同比增长率', false],     // negative iop need rank
            ['ir', '营业收入同比增长率', false],
            ['inp', '净利润同比增长率', false],
            ['inps', '归属母公司股东净利润同比增长率', false],
        ];

        $($.map(fundIndicators, function(indicator){
            return [
                '<tr>',
                    '<td>', indicator[1], '</td>',
                    '<td>', toDecimal(stock[indicator[0]]), '</td>',
                    '<td>', toDecimal(stock[indicator[0]] >=0 || !stock[indicator[0]] ? stock[indicator[0] + '_r'] : 'N/A'), '</td>',
                '</tr>',
            ].join('');
        }).join('')).appendTo(fundTable)
    }

    window.onload = function(){
        var urlVars = getUrlVars(),
            code = urlVars['code'];

        $.getJSON(['../uploads/r_stocks/', code, '.json'].join(''))
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
