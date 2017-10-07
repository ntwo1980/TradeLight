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
            ['close', '收盘价', toDecimal, ''],
            ['ret', '涨跌幅', toDecimal, function(stock){return '排序值：' + toDecimal(stock['ret_r']);}],
            ['var', 'VAR', undefined, function(stock){return '排序值：' + toDecimal(stock['var_r'])}],
            ['ma42', '42日均线', toDecimal, function(stock){ return '收盘价高于均线' + toDecimal(((stock['close'] - stock['ma42']) / stock['ma42']) * 100) + '%' ;}],
            ['ma120', '120日均线', toDecimal, function(stock){ return '收盘价高于均线' + toDecimal(((stock['close'] - stock['ma120']) / stock['ma120']) * 100) + '%'; }],
            ['ma250', '250日均线', toDecimal, function(stock){ return '收盘价高于均线' + toDecimal(((stock['close'] - stock['ma250']) / stock['ma250']) * 100) + '%'; }],
            ['max10', '10内最高价', toDecimal, function(stock){ return stock['max10'] === stock['close'] ? '新高' : '收盘价低于最高价' + toDecimal(((stock['max10'] - stock['close']) / stock['max10']) * 100) + '%'; }],
            ['min10', '10内最低价', toDecimal, function(stock){ return stock['min10'] === stock['close'] ? '新低' : '收盘价高于最低价' + toDecimal(((stock['close'] - stock['min10']) / stock['min10']) * 100) + '%'; }],
            [function(stock){ return (stock['max10'] / stock['min10'] - 1) * 100; }, '最高价高于最低价（%）', toDecimal, ''],
            ['atr10', 'ATR10', toDecimal,
                function(stock){
                    var highVsLow = (stock['max10'] / stock['min10']) - 1;

                    if(stock['max10'] === stock['close']) return '新高';

                    return '最高价下跌' +
                        (highVsLow < 0.05 ? '' : '<span style="font-size:150%; padding: 0 5px;">') +
                        toDecimal((stock['max10'] - stock['close']) / stock['atr10']) +
                        (highVsLow < 0.05 ? '' : '</span>') + '个atr10';
                }],
            ['l_slop', '22日EMA斜率', toDecimal, function(stock){ return stock['l_pvalue'] < 0.001 && stock['l_stderror'] < 7 ? '' : '无效';}],
            ['l_pvalue', '22日EMA斜率pvalue', undefined, ''],
            ['l_stderror', '22日EMA斜率stderror', undefined, '']
        ];


        $($.map(techIndicators, function(indicator){
            var indicatorName = indicator[1],
                indicatorValue = typeof indicator[0] === 'function' ? indicator[0](stock) : stock[indicator[0]],
                indicatorRemark = typeof indicator[3] === 'function' ? indicator[3](stock) : indicator[3];

            if(indicator[2])
                indicatorValue = indicator[2](indicatorValue);

            return [
                '<tr>',
                    '<td>', indicatorName, '</td>',
                    '<td>', indicatorValue, '</td>',
                    '<td>', indicatorRemark, '</td>',
                '</tr>',
            ].join('');
        }).join('')).appendTo(techTable)
    }

    function renderFund(stock)
    {
        var postBody = $('.post-body');

        $('<h3>基本面</h3>').appendTo(postBody)

        $('<p>数据日期：'+ stock['stat_date'] + '</p>').appendTo(postBody);

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
            ['score', '评分', function(stock){ return true; }],
            ['mc', '总市值', function(stock){ return true; }],
            ['cmc', '流通市值', function(stock){ return true; }],
            ['pe', '市盈率', function(stock){ return stock['pe'] > 0 }],
            ['pe_lyr', '静态市盈率', function(stock){ return stock['pe_lyr'] > 0; }],
            ['peg', 'PEG', function(stock){ return stock['pe'] > 0 && stock['iop'] > 0;}],
            ['pb', '市净率', function(stock){ return true; }],
            ['ps', '市销率', function(stock){ return true; }],
            ['pcf', '市现率', function(stock){ return stock['pcf'] > 0; }],
            ['iop', '营业利润同比增长率', function(stock){ return true; }],     // negative iop need rank
            ['ir', '营业收入同比增长率', function(stock){ return true; }],
            ['inp', '净利润同比增长率', function(stock){ return true; }],
            ['inps', '归属母公司股东净利润同比增长率', function(stock){ return true; }],
            ['roic', '投入资本金回报率', function(stock){ return true; }],
        ];

        $($.map(fundIndicators, function(indicator){
            return [
                '<tr>',
                    '<td>', indicator[1], '</td>',
                    '<td>', toDecimal(stock[indicator[0]]), '</td>',
                    '<td>', toDecimal(indicator[2](stock) ? stock[indicator[0] + '_r'] : 'N/A'), '</td>',
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
