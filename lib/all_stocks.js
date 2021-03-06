(function () {
    var titles = ['代码', '名称', '评分', '斜率', '涨幅',
                  '高于42日均线', '高于120日均线', '高于250日均线',
                  '低于10日高价ATR', '市净率', '盈利增速排名',
                  '盈利增速' ,'上期盈利增速',  '市盈率'],
        favoriteIndexes;

    function toDecimal(x) {
            if (typeof x === 'string')
                return x;
            var f = parseFloat(x);
            if (isNaN(f)) {
                return x;
            }

            return f.toFixed(2);
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

    function filterRows(event)
    {
        var showFavorite = $('#showFavorite').is(":checked"),
            showIndexPrefix = 'showIndex_',
            showIndexes = _($(':checkbox:checked')
                            .map(function() { return this.id; }).get())
                            .filter(function(id){
                                return id.indexOf(showIndexPrefix) === 0;
                            })
                            .map(function(id){
                                return 'index' + id.substring(showIndexPrefix.length)
                            })
                            .value();

        if(event &&
            (event.target.id == 'showFavorite' || event.target.id.indexOf(showIndexPrefix) === 0))
        {
            $('#hideDown, #hideMA, #hideIopDown, #hideGem')
                .prop('checked', !showFavorite && !showIndexes.length);
        }

        var hideDown = $('#hideDown').is(":checked"),
            hideMA = $('#hideMA').is(":checked");
            hideIopDown = $('#hideIopDown').is(":checked"),
            hideGem = $('#hideGem').is(":checked"),
            trs = $('table').find("tr:not(:first)"),
            selectors = [],
            hideClass = 'hide',
            dotHideClass = '.' + hideClass;

        trs.removeClass(hideClass).show();
        if(hideDown)
            selectors.push('.down');

        if(hideMA)
            selectors.push('.belowMa');

        if(hideIopDown)
            selectors.push('.iopDown');

        if(hideGem)
            selectors.push('.gem');

        if(showFavorite && !showIndexes.length)
            selectors.push('.notFavorite');

        if(showIndexes.length)
        {
            trs.each(function(){
                var $this = $(this);

                if(showFavorite && !$this.hasClass('notFavorite'))
                {
                    // pass
                }
                else
                {
                    var containsIndex = _.some(showIndexes,
                        function(index) {
                            return $this.hasClass(index);
                        }
                    );

                    if(!containsIndex)
                    {
                        $this.addClass(hideClass);
                    }
                }
            });

            selectors.push(dotHideClass);
        }

        if(selectors.length)
            $(selectors.join(', ')).hide();
    }

    function _markRows(trChunks, index, favorites, stocksIndex, promise)
    {
        var trs = trChunks[index];
        if(_.isUndefined(trs))
        {
            promise.resolve();
            return;
        }

        _.forEach(trs, function(tr){
            var tr = $(tr),
                tds = tr.find("td");

            var code = $(tds[0]).text();
            if (favorites.indexOf(code) == -1)
                tr.addClass('notFavorite');
            if(code.indexOf('300') == 0)
                tr.addClass('gem');
            var indexes = _.get(stocksIndex, code);
            _.forEach(indexes, function(index){
                tr.addClass("index" + index);
            });

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
        });

        _.defer(_.partial(_markRows, trChunks, ++index, favorites, stocksIndex, promise));
    }

    function markRows()
    {
        var trs = $('table').find("tr:not(:first)").get(),
            chunks =_.chunk(trs, 100),
            doneChunksCount = 0,
            favorites = getFavoritesFromLocalStorage(),
            dfd = $.Deferred(),
            stocksIndex = {};

            _.reduce(favoriteIndexes, function(si, data, index){
                _.forEach(data.stocks, function(stock){
                    indexes = _.get(si, stock, []);
                    indexes.push(index);
                    _.set(si, stock, indexes);
                });

                return si;
            }, stocksIndex);

            _markRows(chunks, 0, favorites, stocksIndex, dfd);

        return dfd.promise();
    }

    function showToolbar()
    {

        var showToolbar = $([
            '<div id="show">显示：',
            '<input id="showFavorite" type="checkbox"><label for="showFavorite">收藏</label>',
            '</div>'
        ].join(''));


        var cbs = _(favoriteIndexes)
                    .chain()
                    .map(function(value, key){
                        var indexName = value.name,
                            inputId = "showIndex_" + key;

                        return '<input id="' + inputId + '" type="checkbox"><label for="' + inputId +  '">' + indexName + '</label>';
                    })
                    .value().join('');

        $(cbs).appendTo(showToolbar);

        var hideToolbar = $([
            '<div id="hide">隐藏：',
            '<input id="hideDown" type="checkbox" checked="checked"><label for="hideDown">斜率小于-15</label>',
            '<input id="hideMA" type="checkbox" checked="checked"><label for="hideMA">低于均线</label>',
            '<input id="hideIopDown" type="checkbox" checked="checked"><label for="hideIopDown">盈利下降</label>',
            '<input id="hideGem" type="checkbox" checked="checked"><label for="hideGem">创业板</label>',
            '</div>'
        ].join(''));

        $('.post-body').prepend(showToolbar);
        $('.post-body').prepend(hideToolbar);

        $(':checkbox').change(_.debounce(
            function(event){
                $('.dataTables_filter').prepend('<span class="loading" style="margin-right:200px;">loading...</span>');
                _.defer(function(){
                    filterRows(event);
                    $('.loading').remove();
                });
            }
            , 1000));
    }

    function addFavoriteStar()
    {
        var tds = $('table').find('td:first-child').get(),
            favorites = getFavoritesFromLocalStorage(),
            favoriteHtml = '<li class="fa fa-fw fa-star" style="color:orange" />'
            notFavoriteHtml = '<li class="fa fa-fw fa-star-o" style="color:orange" />';

        _.forEach(_.chunk(tds, 100), function(tds_chunk){
            (function(){
                var thoseTds = tds_chunk;
                _.defer(function(){
                    _.forEach(thoseTds, function(td){
                        var code = $(td).text(),
                            html = favorites.indexOf(code) == -1 ? notFavoriteHtml : favoriteHtml;

                        $(html).appendTo(td);
                    });
                });
            })();
        });
    }

    function toogleFavorite(event)
    {
        var target = $(event.target);

        if(target.hasClass('fa-star-o') || target.hasClass('fa-star'))
        {
            var favorites = getFavoritesFromLocalStorage(),
                td = target.parent(),
                code = td.text();

            if(target.hasClass('fa-star-o'))
            {
                if(favorites.indexOf(code) == -1)
                {
                    favorites.push(code);
                    saveFavoritesIntoLocalStorage(favorites);
                }

                td.addClass('favorite');
                target.removeClass('fa-star-o').addClass('fa-star');
                td.parent().removeClass('notFavorite');
            }
            else if(target.hasClass('fa-star'))
            {
                var index = favorites.indexOf(code);
                if(index != -1)
                {
                    favorites.splice(index, 1);
                    saveFavoritesIntoLocalStorage(favorites);
                }

                target.removeClass('fa-star').addClass('fa-star-o');
                td.parent().addClass('notFavorite');
            }
        }
    }

    function getFavoritesFromLocalStorage()
    {
        var favorites = localStorage.getItem('favorites');
        if(!favorites)
            favorites = []
        else
            favorites = JSON.parse(favorites);

        return favorites;
    }

    function saveFavoritesIntoLocalStorage(favorites)
    {
        localStorage.setItem('favorites', JSON.stringify(favorites));
    }

    waitForJsLib(function(){
        $.getScript( "../../lib/stocks/datatables.js" )
        .done(function( script, textStatus ) {
            $(function(){
                $('table th').each(function(index, item){
                    $(item).attr('title', titles[index]);
                });

                $('table').DataTable(
                    {
                        paging: false,
                        fixedHeader: true,
                        order: [[2, 'desc'], [3, 'desc']],
                        searchDelay: 200,
                        columnDefs: [
                            {width: '55px', targets: 0},
                            {width: '40px', targets: 1}
                        ]
                    });

                $.getJSON('index_stocks.json')
                .done(function(indexes){
                    favoriteIndexes = indexes;
                    _.defer(addFavoriteStar);
                    showToolbar();
                    _.defer(function(){markRows().then(filterRows)});
                    $(document).click(toogleFavorite);
                });
            });
        })
    });
})();
