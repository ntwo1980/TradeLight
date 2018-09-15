# -*- coding: utf-8 -*-
from __future__ import division
import datetime as dt
import pandas as pd
import numpy as np
import myutils as u
import six
from dateutil.relativedelta import *
try:
    from kuanke.user_space_api import *
except:
    pass
from jqdata import *
from scipy import stats

today = dt.datetime.today()
today_dt = dt.date.today()
today_str = today.strftime("%Y-%m-%d")
all_indexes = None

industries = ['HY401', 'HY402', 'HY403', 'HY404', 'HY405', 'HY406', 'HY407', 'HY408', 'HY409', 'HY410', 'HY411', 'HY412', 'HY413', 'HY414', 'HY415', 'HY416', 'HY417', 'HY418', 'HY419', 'HY420', 'HY421', 'HY422', 'HY423', 'HY424', 'HY425', 'HY426', 'HY427', 'HY428', 'HY429', 'HY432', 'HY433', 'HY434', 'HY435', 'HY436', 'HY437', 'HY438', 'HY439', 'HY440', 'HY441', 'HY442', 'HY443', 'HY444', 'HY445', 'HY446', 'HY447', 'HY448', 'HY449', 'HY450', 'HY451', 'HY452', 'HY453', 'HY454', 'HY455', 'HY457', 'HY458', 'HY459', 'HY460', 'HY461', 'HY462', 'HY463', 'HY464', 'HY465', 'HY466', 'HY467', 'HY468', 'HY469', 'HY470', 'HY471', 'HY472', 'HY473', 'HY474', 'HY476', 'HY477', 'HY478', 'HY479', 'HY480', 'HY481', 'HY483', 'HY484', 'HY485', 'HY486', 'HY487', 'HY488', 'HY489', 'HY491', 'HY492', 'HY493', 'HY494', 'HY496', 'HY497', 'HY500', 'HY501', 'HY504', 'HY505', 'HY506', 'HY509', 'HY510', 'HY511', 'HY512', 'HY513', 'HY514', 'HY515', 'HY516', 'HY517', 'HY518', 'HY519', 'HY520', 'HY521', 'HY523', 'HY524', 'HY525', 'HY526', 'HY527', 'HY528', 'HY529', 'HY530', 'HY531', 'HY570', 'HY571', 'HY572', 'HY573', 'HY574', 'HY576', 'HY578', 'HY579', 'HY587', 'HY588', 'HY591', 'HY593', 'HY595', 'HY596', 'HY597', 'HY598', 'HY601']

indexes = ['000001.XSHG', '000002.XSHG', '000003.XSHG', '000004.XSHG', '000005.XSHG', '000006.XSHG', '000007.XSHG', '000008.XSHG', '000009.XSHG', '000010.XSHG', '000011.XSHG', '000012.XSHG', '000013.XSHG', '000015.XSHG', '000016.XSHG', '000017.XSHG', '000018.XSHG', '000019.XSHG', '000020.XSHG', '000021.XSHG', '000022.XSHG', '000025.XSHG', '000026.XSHG', '000027.XSHG', '000028.XSHG', '000029.XSHG', '000030.XSHG', '000031.XSHG', '000032.XSHG', '000033.XSHG', '000034.XSHG', '000035.XSHG', '000036.XSHG', '000037.XSHG', '000038.XSHG', '000039.XSHG', '000040.XSHG', '000041.XSHG', '000042.XSHG', '000043.XSHG', '000044.XSHG', '000045.XSHG', '000046.XSHG', '000047.XSHG', '000048.XSHG', '000049.XSHG', '000050.XSHG', '000051.XSHG', '000052.XSHG', '000053.XSHG', '000054.XSHG', '000055.XSHG', '000056.XSHG', '000057.XSHG', '000058.XSHG', '000059.XSHG', '000060.XSHG', '000061.XSHG', '000062.XSHG', '000063.XSHG', '000064.XSHG', '000065.XSHG', '000066.XSHG', '000067.XSHG', '000068.XSHG', '000069.XSHG', '000070.XSHG', '000071.XSHG', '000072.XSHG', '000073.XSHG', '000074.XSHG', '000075.XSHG', '000076.XSHG', '000077.XSHG', '000078.XSHG', '000079.XSHG', '000090.XSHG', '000091.XSHG', '000092.XSHG', '000093.XSHG', '000094.XSHG', '000095.XSHG', '000096.XSHG', '000097.XSHG', '000098.XSHG', '000099.XSHG', '000100.XSHG', '000101.XSHG', '000102.XSHG', '000103.XSHG', '000104.XSHG', '000105.XSHG', '000106.XSHG', '000107.XSHG', '000108.XSHG', '000109.XSHG', '000110.XSHG', '000111.XSHG', '000112.XSHG', '000113.XSHG', '000114.XSHG', '000115.XSHG', '000116.XSHG', '000117.XSHG', '000118.XSHG', '000119.XSHG', '000120.XSHG', '000121.XSHG', '000122.XSHG', '000123.XSHG', '000125.XSHG', '000126.XSHG', '000128.XSHG', '000129.XSHG', '000130.XSHG', '000131.XSHG', '000132.XSHG', '000133.XSHG', '000134.XSHG', '000135.XSHG', '000136.XSHG', '000137.XSHG', '000138.XSHG', '000139.XSHG', '000141.XSHG', '000142.XSHG', '000145.XSHG', '000146.XSHG', '000147.XSHG', '000148.XSHG', '000149.XSHG', '000150.XSHG', '000151.XSHG', '000152.XSHG', '000153.XSHG', '000155.XSHG', '000158.XSHG', '000159.XSHG', '000160.XSHG', '000161.XSHG', '000162.XSHG', '000300.XSHG', '000801.XSHG', '000802.XSHG', '000803.XSHG', '000804.XSHG', '000805.XSHG', '000806.XSHG', '000807.XSHG', '000808.XSHG', '000809.XSHG', '000810.XSHG', '000811.XSHG', '000812.XSHG', '000813.XSHG', '000814.XSHG', '000815.XSHG', '000816.XSHG', '000817.XSHG', '000818.XSHG', '000819.XSHG', '000820.XSHG', '000821.XSHG', '000822.XSHG', '000823.XSHG', '000824.XSHG', '000825.XSHG', '000826.XSHG', '000827.XSHG', '000828.XSHG', '000829.XSHG', '000830.XSHG', '000831.XSHG', '000832.XSHG', '000833.XSHG', '000838.XSHG', '000839.XSHG', '000840.XSHG', '000841.XSHG', '000842.XSHG', '000843.XSHG', '000844.XSHG', '000846.XSHG', '000847.XSHG', '000849.XSHG', '000850.XSHG', '000851.XSHG', '000852.XSHG', '000853.XSHG', '000855.XSHG', '000901.XSHG', '000902.XSHG', '000903.XSHG', '000904.XSHG', '000905.XSHG', '000906.XSHG', '000907.XSHG', '000908.XSHG', '000909.XSHG', '000910.XSHG', '000911.XSHG', '000912.XSHG', '000913.XSHG', '000914.XSHG', '000915.XSHG', '000916.XSHG', '000917.XSHG', '000918.XSHG', '000919.XSHG', '000920.XSHG', '000921.XSHG', '000922.XSHG', '000923.XSHG', '000925.XSHG', '000926.XSHG', '000927.XSHG', '000928.XSHG', '000929.XSHG', '000930.XSHG', '000931.XSHG', '000932.XSHG', '000933.XSHG', '000934.XSHG', '000935.XSHG', '000936.XSHG', '000937.XSHG', '000938.XSHG', '000939.XSHG', '000940.XSHG', '000941.XSHG', '000942.XSHG', '000943.XSHG', '000944.XSHG', '000945.XSHG', '000946.XSHG', '000947.XSHG', '000948.XSHG', '000949.XSHG', '000950.XSHG', '000951.XSHG', '000952.XSHG', '000953.XSHG', '000954.XSHG', '000955.XSHG', '000956.XSHG', '000957.XSHG', '000958.XSHG', '000959.XSHG', '000960.XSHG', '000961.XSHG', '000962.XSHG', '000963.XSHG', '000964.XSHG', '000965.XSHG', '000966.XSHG', '000967.XSHG', '000968.XSHG', '000969.XSHG', '000970.XSHG', '000971.XSHG', '000972.XSHG', '000973.XSHG', '000974.XSHG', '000975.XSHG', '000976.XSHG', '000977.XSHG', '000978.XSHG', '000979.XSHG', '000980.XSHG', '000981.XSHG', '000982.XSHG', '000983.XSHG', '000984.XSHG', '000985.XSHG', '000986.XSHG', '000987.XSHG', '000988.XSHG', '000989.XSHG', '000990.XSHG', '000991.XSHG', '000992.XSHG', '000993.XSHG', '000994.XSHG', '000995.XSHG', '000996.XSHG', '000997.XSHG', '000998.XSHG', '000999.XSHG', '399001.XSHE', '399002.XSHE', '399003.XSHE', '399004.XSHE', '399005.XSHE', '399006.XSHE', '399007.XSHE', '399008.XSHE', '399009.XSHE', '399010.XSHE', '399011.XSHE', '399012.XSHE', '399013.XSHE', '399015.XSHE', '399100.XSHE', '399101.XSHE', '399102.XSHE', '399103.XSHE', '399106.XSHE', '399107.XSHE', '399108.XSHE', '399231.XSHE', '399232.XSHE', '399233.XSHE', '399234.XSHE', '399235.XSHE', '399236.XSHE', '399237.XSHE', '399238.XSHE', '399239.XSHE', '399240.XSHE', '399241.XSHE', '399242.XSHE', '399243.XSHE', '399244.XSHE', '399248.XSHE', '399249.XSHE', '399298.XSHE', '399299.XSHE', '399300.XSHE', '399301.XSHE', '399302.XSHE', '399303.XSHE', '399305.XSHE', '399306.XSHE', '399307.XSHE', '399310.XSHE', '399311.XSHE', '399312.XSHE', '399313.XSHE', '399314.XSHE', '399315.XSHE', '399316.XSHE', '399317.XSHE', '399318.XSHE', '399319.XSHE', '399320.XSHE', '399321.XSHE', '399322.XSHE', '399324.XSHE', '399326.XSHE', '399328.XSHE', '399330.XSHE', '399332.XSHE', '399333.XSHE', '399335.XSHE', '399337.XSHE', '399339.XSHE', '399341.XSHE', '399344.XSHE', '399346.XSHE', '399348.XSHE', '399350.XSHE', '399351.XSHE', '399352.XSHE', '399353.XSHE', '399355.XSHE', '399356.XSHE', '399357.XSHE', '399358.XSHE', '399359.XSHE', '399360.XSHE', '399361.XSHE', '399362.XSHE', '399363.XSHE', '399364.XSHE', '399365.XSHE', '399366.XSHE', '399367.XSHE', '399368.XSHE', '399369.XSHE', '399370.XSHE', '399371.XSHE', '399372.XSHE', '399373.XSHE', '399374.XSHE', '399375.XSHE', '399376.XSHE', '399377.XSHE', '399378.XSHE', '399379.XSHE', '399380.XSHE', '399381.XSHE', '399382.XSHE', '399383.XSHE', '399384.XSHE', '399385.XSHE', '399386.XSHE', '399387.XSHE', '399388.XSHE', '399389.XSHE', '399390.XSHE', '399391.XSHE', '399392.XSHE', '399393.XSHE', '399394.XSHE', '399395.XSHE', '399396.XSHE', '399397.XSHE', '399398.XSHE', '399399.XSHE', '399400.XSHE', '399401.XSHE', '399402.XSHE', '399403.XSHE', '399404.XSHE', '399405.XSHE', '399406.XSHE', '399407.XSHE', '399408.XSHE', '399409.XSHE', '399410.XSHE', '399411.XSHE', '399412.XSHE', '399413.XSHE', '399415.XSHE', '399416.XSHE', '399417.XSHE', '399418.XSHE', '399419.XSHE', '399420.XSHE', '399423.XSHE', '399427.XSHE', '399428.XSHE', '399429.XSHE', '399431.XSHE', '399432.XSHE', '399433.XSHE', '399434.XSHE', '399435.XSHE', '399436.XSHE', '399437.XSHE', '399438.XSHE', '399439.XSHE', '399440.XSHE', '399441.XSHE', '399481.XSHE', '399550.XSHE', '399551.XSHE', '399552.XSHE', '399553.XSHE', '399554.XSHE', '399555.XSHE', '399556.XSHE', '399557.XSHE', '399602.XSHE', '399604.XSHE', '399606.XSHE', '399608.XSHE', '399610.XSHE', '399611.XSHE', '399612.XSHE', '399613.XSHE', '399614.XSHE', '399615.XSHE', '399616.XSHE', '399617.XSHE', '399618.XSHE', '399619.XSHE', '399620.XSHE', '399621.XSHE', '399622.XSHE', '399623.XSHE', '399624.XSHE', '399625.XSHE', '399626.XSHE', '399627.XSHE', '399628.XSHE', '399629.XSHE', '399630.XSHE', '399631.XSHE', '399632.XSHE', '399633.XSHE', '399634.XSHE', '399635.XSHE', '399636.XSHE', '399637.XSHE', '399638.XSHE', '399639.XSHE', '399640.XSHE', '399641.XSHE', '399642.XSHE', '399643.XSHE', '399644.XSHE', '399645.XSHE', '399646.XSHE', '399647.XSHE', '399648.XSHE', '399649.XSHE', '399650.XSHE', '399651.XSHE', '399652.XSHE', '399653.XSHE', '399654.XSHE', '399655.XSHE', '399656.XSHE', '399657.XSHE', '399658.XSHE', '399659.XSHE', '399660.XSHE', '399661.XSHE', '399662.XSHE', '399663.XSHE', '399664.XSHE', '399665.XSHE', '399666.XSHE', '399667.XSHE', '399668.XSHE', '399669.XSHE', '399670.XSHE', '399671.XSHE', '399672.XSHE', '399673.XSHE', '399674.XSHE', '399675.XSHE', '399676.XSHE', '399677.XSHE', '399678.XSHE', '399679.XSHE', '399680.XSHE', '399681.XSHE', '399682.XSHE', '399683.XSHE', '399684.XSHE', '399685.XSHE', '399686.XSHE', '399687.XSHE', '399688.XSHE', '399689.XSHE', '399701.XSHE', '399702.XSHE', '399703.XSHE', '399704.XSHE', '399705.XSHE', '399706.XSHE', '399707.XSHE', '399802.XSHE', '399803.XSHE', '399804.XSHE', '399805.XSHE', '399806.XSHE', '399807.XSHE', '399808.XSHE', '399809.XSHE', '399810.XSHE', '399811.XSHE', '399812.XSHE', '399813.XSHE', '399814.XSHE', '399817.XSHE', '399901.XSHE', '399903.XSHE', '399904.XSHE', '399905.XSHE', '399907.XSHE', '399908.XSHE', '399909.XSHE', '399910.XSHE', '399911.XSHE', '399912.XSHE', '399913.XSHE', '399914.XSHE', '399915.XSHE', '399916.XSHE', '399917.XSHE', '399918.XSHE', '399919.XSHE', '399920.XSHE', '399922.XSHE', '399925.XSHE', '399926.XSHE', '399927.XSHE', '399928.XSHE', '399929.XSHE', '399930.XSHE', '399931.XSHE', '399932.XSHE', '399933.XSHE', '399934.XSHE', '399935.XSHE', '399936.XSHE', '399937.XSHE', '399938.XSHE', '399939.XSHE', '399941.XSHE', '399942.XSHE', '399943.XSHE', '399944.XSHE', '399945.XSHE', '399946.XSHE', '399947.XSHE', '399948.XSHE', '399949.XSHE', '399950.XSHE', '399951.XSHE', '399952.XSHE', '399953.XSHE', '399954.XSHE', '399956.XSHE', '399957.XSHE', '399958.XSHE', '399959.XSHE', '399960.XSHE', '399961.XSHE', '399962.XSHE', '399963.XSHE', '399964.XSHE', '399965.XSHE', '399966.XSHE', '399967.XSHE', '399968.XSHE', '399969.XSHE', '399970.XSHE', '399971.XSHE', '399972.XSHE', '399973.XSHE', '399974.XSHE', '399975.XSHE', '399976.XSHE', '399977.XSHE', '399978.XSHE', '399979.XSHE', '399980.XSHE', '399982.XSHE', '399983.XSHE', '399986.XSHE', '399987.XSHE', '399989.XSHE', '399990.XSHE', '399991.XSHE', '399992.XSHE', '399993.XSHE', '399994.XSHE', '399995.XSHE', '399996.XSHE', '399997.XSHE']

cyclical_industries = ['801020', '801050', '801711']

class TradeScheduler:
    def __init__(self, g, context, trade_func):
        self.g = g
        self.trade_func = trade_func
        self.context = context
        g.if_trade = False

    def trade(self):
        trade = False

        if not hasattr(self.g, 'trade_count'):
            self.g.trade_count = 0

        if(self.need_trade()):
            self.g.if_trade = True
            trade = True
            if self.trade_func is not None:
                self.trade_func()
        else:
            self.g.if_trade = False

        self.g.trade_count += 1

        return trade

class MonthDayTradeScheduler(TradeScheduler):
    def __init__(self, g, context, trade_func, day):
        TradeScheduler.__init__(self, g, context, trade_func)
        self.day = day

    def need_trade(self):
        if self.day == 'all':
            return True

        today = self.context.current_dt.date()
        if self.day > 0:
            yesterday = self.context.previous_date
            scheduled_trade_day = today.replace(day=self.day)

            return yesterday < scheduled_trade_day <= today
        elif self.day < 0:
            current_year = today.year
            current_month = today.month

            scheduled_trade_day = None
            for day in range(1, 20):
                next_month_first_day = (today + relativedelta(months=+1)).replace(day=day)

                try:
                    scheduled_trade_day = shift_trading_day(next_month_first_day, -1)
                except:
                    continue
                else:
                    break

            return yesterday < scheduled_trade_day <= today
        else:
            return False

class SpringFestival():
    def __init__(self):
        sprint_festival_str = ['2001-2-5', '2001-1-24', '2002-2-12', '2003-2-1', '2004-1-22', '2005-2-9', '2006-1-29', '2007-2-18', '2008-2-7', '2009-1-26', '2010-2-14', '2011-2-3', '2012-1-23', '2013-2-10', '2014-1-31', '2015-2-19', '2016-2-8', '2017-1-28', '2018-2-16', '2019-2-5', '2020-1-25', '2021-2-12', '2022-2-1', '2023-1-22', '2024-2-10', '2025-1-29', '2026-2-17', '2027-2-6', '2028-1-26', '2029-2-13', '2030-2-3', '2031-1-23', '2032-2-11', '2033-1-31', '2034-2-19', '2035-2-8', '2036-1-28', '2037-2-15', '2038-2-4', '2039-1-24', '2040-2-12', '2041-2-1', '2042-1-22', '2043-2-10', '2044-1-30', '2045-2-17', '2046-2-6', '2047-1-26', '2048-2-14', '2049-2-2']
        self.sprint_festivals = {int(d[:4]): dt.datetime.strptime(d, "%Y-%m-%d") for d in sprint_festival_str}

    def get_spring_festival_day(self, year):
        return self.sprint_festivals[year].date()

class SpringFestivalTradeScheduler(TradeScheduler):
    def __init__(self, g, context, trade_func, offset):
        TradeScheduler.__init__(self, g, context, trade_func)
        self.offset = offset
        sprint_festival_str = ['2001-2-5', '2001-1-24', '2002-2-12', '2003-2-1', '2004-1-22', '2005-2-9', '2006-1-29', '2007-2-18', '2008-2-7', '2009-1-26', '2010-2-14', '2011-2-3', '2012-1-23', '2013-2-10', '2014-1-31', '2015-2-19', '2016-2-8', '2017-1-28', '2018-2-16', '2019-2-5', '2020-1-25', '2021-2-12', '2022-2-1', '2023-1-22', '2024-2-10', '2025-1-29', '2026-2-17', '2027-2-6', '2028-1-26', '2029-2-13', '2030-2-3', '2031-1-23', '2032-2-11', '2033-1-31', '2034-2-19', '2035-2-8', '2036-1-28', '2037-2-15', '2038-2-4', '2039-1-24', '2040-2-12', '2041-2-1', '2042-1-22', '2043-2-10', '2044-1-30', '2045-2-17', '2046-2-6', '2047-1-26', '2048-2-14', '2049-2-2']
        self.sprint_festivals = {int(d[:4]): dt.datetime.strptime(d, "%Y-%m-%d") for d in sprint_festival_str}

    def need_trade(self):
        today = self.context.current_dt.date()
        if self.offset > 0:
            yesterday = self.context.previous_date
            current_year = today.year
            sprint_festival = self.sprint_festivals[current_year]
            scheduled_trade_day = (sprint_festival + relativedelta(days=-self.offset)).date()

            return yesterday < scheduled_trade_day <= today
        else:
            return False

class WeekDayTradeScheduler(TradeScheduler):
    def __init__(self, g, context, trade_func, weekday):
        TradeScheduler.__init__(self, g, context, trade_func)
        self.weekday = weekday

    def need_trade(self):
        if self.weekday == 'all':
            return True

        if self.weekday <=0 or self.weekday >= 6:
            return False

        today = self.context.current_dt

        return today.weekday() + 1 == self.weekday  # Monday weekday is 1

class EverydayTradeScheduler(TradeScheduler):
    def __init__(self, g, context, trade_func, interval):
        TradeScheduler.__init__(self, g, context, trade_func)
        self.interval = interval

    def need_trade(self):
        return self.g.trade_count % self.interval == 0

class SecuritySelector:
    def get_stocks(self):
        return self.stocks

class StockIndicesSecuritySelector(SecuritySelector):
    def __init__(self, indices, date, exclude_gem = True):
        if isinstance(indices, six.string_types):
            self.indices = list(indices)
        else:
            self.indices = indices

        stocks = set()
        for index in indices:
            stocks.update(get_index_stocks(index, date))

        if exclude_gem:
            stocks = [s for s in stocks if not str(s).startswith('300')]

        self.stocks = list(stocks)

class FosterSecuirtySelector(SecuritySelector):
    def __init__(self, stocks, date, lar, pe, otr, prr):
        df = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.pe_ratio,
                                    income.operating_profit,income.total_profit,income.operating_revenue,
                                    balance.total_liability,balance.total_assets
            ).filter(
                balance.total_liability / balance.total_assets < lar,
                valuation.pe_ratio < pe,
                income.operating_profit / income.total_profit > otr,
                income.operating_profit / income.operating_revenue > prr,
                indicator.code.in_(stocks)
            ), date)

        self.stocks = list(df.code)

class NotNewSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date):
        past_stocks = get_all_securities(date=shift_trading_day(date, -120))

        self.stocks = list(set(stocks).intersection(set(past_stocks.index)))

class NotSTSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date):
        st = get_extras('is_st', stocks, end_date=date, count = 1, df=True)
        st=st.iloc[0]

        self.stocks=list(st[st==False].index)

class NotBlackListSecuritySelector(SecuritySelector):
    def __init__(self, stocks):
        blacklist = {'002087.XSHE'}

        self.stocks = list(set(stocks) - blacklist)

class NotIndustrySecuritySelector(SecuritySelector):
     def __init__(self, stocks, date, industries):
        exclude_stocks = {s for industry in industries for s in get_industry_stocks(industry, date=date)}
        self.stocks = list(set(stocks) - exclude_stocks)

class IndustrySecuritySelector(SecuritySelector):
     def __init__(self, stocks, date, industries):
        industry_stocks = {s for industry in industries for s in get_industry_stocks(industry, date=date)}
        self.stocks = list(set(stocks) & industry_stocks)

class FundamentalSecuritySelector1(SecuritySelector):
    def __init__(self, stocks, date, mc, pb, iop, roic):
        fundamentals = get_fundamentals(query(valuation.code,
                indicator.inc_operation_profit_year_on_year,
                indicator.gross_profit_margin,
                valuation.pb_ratio,
                valuation.pe_ratio,
                valuation.market_cap,
                income.net_profit,
                income.income_tax_expense,
                income.financial_expense,
                balance.total_owner_equities,
                balance.shortterm_loan,
                balance.longterm_loan,
                balance.non_current_liability_in_one_year,
                balance.bonds_payable,
                balance.longterm_account_payable,
            ).filter(
                indicator.code.in_(stocks)
            ), date)

        fundamentals.fillna(0, inplace=True)
        fundamentals['mc_r'] = fundamentals['market_cap'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['gpm_r'] = fundamentals['gross_profit_margin'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pb_r'] = fundamentals['pb_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['iop_r'] = fundamentals['inc_operation_profit_year_on_year'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['ROIC'] = ((fundamentals['net_profit'] + fundamentals['income_tax_expense'] + fundamentals['financial_expense'])
                    / (fundamentals['total_owner_equities'] + fundamentals['shortterm_loan'] + fundamentals['longterm_loan'] +
                      fundamentals['non_current_liability_in_one_year'] + fundamentals['bonds_payable'] +  fundamentals['longterm_account_payable']))
        fundamentals['ROIC_r'] = fundamentals['ROIC'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['peg'] = fundamentals['pe_ratio'] / fundamentals['inc_operation_profit_year_on_year']
        fundamentals['peg_r'] = fundamentals['peg'].rank(ascending = True, method = 'max', pct=True)

        fundamentals1 = fundamentals[(fundamentals['mc_r'] >= mc[0]) \
                                & (fundamentals['mc_r'] <= mc[1]) \
                                & (fundamentals['pb_r'] >= pb[0]) \
                                & (fundamentals['pb_r'] <= pb[1]) \
                                & (fundamentals['iop_r'] >= iop[0]) \
                                & (fundamentals['iop_r'] <= iop[1]) \
                                & (fundamentals['gpm_r'] >= 0.1) \
                                & (fundamentals['ROIC_r'] >= roic[0]) \
                                & (fundamentals['ROIC_r'] <= roic[1])]

        fundamentals2 = fundamentals[(fundamentals['mc_r'] >= mc[0]) \
                                & (fundamentals['mc_r'] <= mc[1]) \
                                & (fundamentals['peg_r'] >= 0) \
                                & (fundamentals['peg_r'] <= 0.4) \
                                & (fundamentals['iop_r'] >= iop[0]) \
                                & (fundamentals['iop_r'] <= iop[1]) \
                                & (fundamentals['gpm_r'] >= 0.1) \
                                & (fundamentals['ROIC_r'] >= roic[0]) \
                                & (fundamentals['ROIC_r'] <= roic[1])]

        fundamentals1 = fundamentals1.set_index(['code'])
        fundamentals2 = fundamentals2.set_index(['code'])

        #self.stocks = set(fundamentals1.index) | set(fundamentals2.index)
        self.stocks = set(fundamentals1.index)

class FundamentalSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date, mc, pe, pb, ps, iop, facr, statDate=None):
        if not statDate:
            fundamentals = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.pe_ratio, valuation.pb_ratio, valuation.ps_ratio, valuation.pcf_ratio, indicator.inc_operation_profit_year_on_year, balance.fixed_assets, balance.total_assets, balance.total_liability, cash_flow.cash_and_equivalents_at_end, income.total_profit, income.financial_expense, income.asset_impairment_loss, balance.long_deferred_expense, indicator.statDate
                ).filter(
                    indicator.inc_operation_profit_year_on_year > iop,
                    #indicator.inc_net_profit_year_on_year > 0,
                    cash_flow.goods_sale_and_service_render_cash > 0,
                    indicator.code.in_(stocks)
                ), date)
        else:
            fundamentals = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.pe_ratio, valuation.pb_ratio, valuation.ps_ratio, valuation.pcf_ratio, indicator.inc_operation_profit_year_on_year, balance.fixed_assets, balance.total_assets, balance.total_liability, cash_flow.cash_and_equivalents_at_end, income.total_profit, income.financial_expense, income.asset_impairment_loss, balance.long_deferred_expense, indicator.statDate
                ).filter(
                    indicator.inc_operation_profit_year_on_year > iop,
                    #indicator.inc_net_profit_year_on_year > 0
                    cash_flow.goods_sale_and_service_render_cash > 0,
                    indicator.statDate == statDate,
                    indicator.code.in_(stocks)
                ), date)

        fundamentals['facr'] = fundamentals['fixed_assets'] / fundamentals['total_assets']
        fundamentals['ev_ebitda'] = (fundamentals['market_cap'] * 100000000 + fundamentals['total_liability'] -                                          fundamentals['cash_and_equivalents_at_end']) / (fundamentals['total_profit'] + fundamentals['financial_expense'] +                          fundamentals['asset_impairment_loss'] + fundamentals['long_deferred_expense'])
        fundamentals['mc_r'] = fundamentals['market_cap'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pe_r'] = fundamentals['pe_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pb_r'] = fundamentals['pb_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['ps_r'] = fundamentals['ps_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pcf_r'] = fundamentals['pcf_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['facr_r'] = fundamentals['facr'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['ev_ebitda_r'] = fundamentals['ev_ebitda'].rank(ascending = True, method = 'max', pct=True)

        fundamentals = fundamentals[(fundamentals['mc_r'] >= mc[0]) \
                                & (fundamentals['mc_r'] <= mc[1]) \
                                & (fundamentals['pe_r'] >= pe[0]) \
                                & (fundamentals['pe_r'] <= pe[1]) \
                                & (fundamentals['pb_r'] >= pb[0]) \
                                & (fundamentals['pb_r'] <= pb[1]) \
                                & (fundamentals['ps_r'] >= ps[0]) \
                                & (fundamentals['ps_r'] <= ps[1]) \
                                & (fundamentals['facr_r'] >= facr[0]) \
                                & (fundamentals['facr_r'] <= facr[1])]

        fundamentals = fundamentals.set_index(['code'])

        self.stocks = list(fundamentals.index)

class FundamentalSecuritySelector2(SecuritySelector):
    def __init__(self, stocks, date, statDate=None):
        if not statDate:
            fundamentals = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.pe_ratio, valuation.pb_ratio, valuation.ps_ratio, valuation.pcf_ratio, indicator.inc_operation_profit_year_on_year, balance.fixed_assets, balance.total_assets, balance.total_liability, cash_flow.cash_and_equivalents_at_end, income.total_profit, income.financial_expense, income.asset_impairment_loss, balance.long_deferred_expense, indicator.statDate
                ).filter(
                    #indicator.inc_net_profit_year_on_year > 0,
                    cash_flow.goods_sale_and_service_render_cash > 0,
                    indicator.code.in_(stocks)
                ), date)

        fundamentals['iop_r'] = fundamentals['inc_operation_profit_year_on_year'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['ps_r'] = fundamentals['ps_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pe_r'] = fundamentals['pe_ratio'].rank(ascending = True, method = 'max', pct=True)

        fundamentals = fundamentals[(fundamentals['iop_r'] >= 0.5) \
                                & (fundamentals['iop_r'] <= 1)  \
                                & (fundamentals['pe_r'] >= 0) \
                                & (fundamentals['pe_r'] <= 0.5)\
                                & (fundamentals['ps_r'] >= 0.5) \
                                & (fundamentals['ps_r'] <= 1)]

        fundamentals = fundamentals.set_index(['code'])

        self.stocks = list(fundamentals.index)

class ValueFundamentalSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date, mc, pe, pb, ps, pcf, iop):
        fundamentals = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.pe_ratio, valuation.pb_ratio, valuation.ps_ratio, valuation.pcf_ratio, indicator.inc_operation_profit_year_on_year, balance.long_deferred_expense, indicator.statDate
            ).filter(
                valuation.pe_ratio > 0,
                indicator.code.in_(stocks)
            ), date)

        fundamentals['mc_r'] = fundamentals['market_cap'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pe_r'] = fundamentals['pe_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pb_r'] = fundamentals['pb_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['ps_r'] = fundamentals['ps_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pcf_r'] = fundamentals['pcf_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['iop_r'] = fundamentals['inc_operation_profit_year_on_year'].rank(ascending = True, method = 'max', pct=True)

        fundamentals = fundamentals[(fundamentals['mc_r'] >= mc[0]) \
                                & (fundamentals['mc_r'] <= mc[1]) \
                                & (fundamentals['pe_r'] >= pe[0]) \
                                & (fundamentals['pe_r'] <= pe[1]) \
                                & (fundamentals['pb_r'] >= pb[0]) \
                                & (fundamentals['pb_r'] <= pb[1]) \
                                & (fundamentals['ps_r'] >= ps[0]) \
                                & (fundamentals['ps_r'] <= ps[1]) \
                                & (fundamentals['pcf_r'] >= pcf[0]) \
                                & (fundamentals['pcf_r'] <= pcf[1]) \
                                & (fundamentals['iop_r'] >= iop[0]) \
                                & (fundamentals['iop_r'] <= iop[1])]

        fundamentals = fundamentals.set_index(['code'])

        self.stocks = list(fundamentals.index)

class TestFundamentalSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date):
        fundamentals = get_fundamentals(query(valuation.code,
                indicator.inc_operation_profit_year_on_year,
                valuation.pb_ratio,
                valuation.market_cap,
                income.net_profit,
                income.income_tax_expense,
                income.financial_expense,
                balance.total_owner_equities,
                balance.shortterm_loan,
                balance.longterm_loan,
                balance.non_current_liability_in_one_year,
                balance.bonds_payable,
                balance.longterm_account_payable
            ).filter(
                valuation.pe_ratio > 0,
                indicator.code.in_(stocks)
            ), date)

        fundamentals.fillna(0, inplace=True)
        fundamentals['mc_r'] = fundamentals['market_cap'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['ROIC'] = ((fundamentals['net_profit'] + fundamentals['income_tax_expense'] + fundamentals['financial_expense'])
                    / (fundamentals['total_owner_equities'] + fundamentals['shortterm_loan'] + fundamentals['longterm_loan'] +
                      fundamentals['non_current_liability_in_one_year'] + fundamentals['bonds_payable'] +  fundamentals['longterm_account_payable']))
        fundamentals['ROIC_r'] = fundamentals['ROIC'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['pb_r'] = fundamentals['pb_ratio'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['iop_r'] = fundamentals['inc_operation_profit_year_on_year'].rank(ascending = True, method = 'max', pct=True)

        fundamentals = fundamentals[(fundamentals['mc_r'] <= 0.8)
                                & (fundamentals['pb_r'] <= 0.4)
                                & (fundamentals['ROIC_r'] >= 0.6)
                                & (fundamentals['iop_r'] >= 0.6 )]

        fundamentals = fundamentals.set_index(['code'])

        self.stocks = list(fundamentals.index)

class PegSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date, peg):
        fundamentals = get_fundamentals(query(
                indicator.code,
                indicator.inc_net_profit_to_shareholders_year_on_year,
                indicator.inc_revenue_year_on_year,
                valuation.pe_ratio
            ).filter(
                indicator.inc_net_profit_to_shareholders_year_on_year > 0,
                indicator.inc_revenue_year_on_year > 0,
                valuation.pe_ratio > 0,
                valuation.pe_ratio < 50,
                indicator.code.in_(stocks)
            ), date)

        fundamentals['peg_pro'] = fundamentals['pe_ratio'] / fundamentals['inc_net_profit_to_shareholders_year_on_year']
        fundamentals['peg_re'] = fundamentals['pe_ratio'] / fundamentals['inc_revenue_year_on_year']

        fundamentals['peg_pro_r'] = fundamentals['peg_pro'].rank(ascending = True, method = 'max', pct=True)
        fundamentals['peg_re_r'] = fundamentals['peg_re'].rank(ascending = True, method = 'max', pct=True)

        fundamentals = fundamentals[(fundamentals['peg_pro_r'] <= peg)]

        fundamentals = fundamentals.set_index(['code'])

        self.stocks = list(fundamentals.index)

class IndustryFundamentalSecuritySelector(SecuritySelector):
    def __init__(self, stocks, date, mc, pb):
        df_industry = pd.DataFrame(columns=['code', 'industry'])

        for industry in industries:
            stocks_industry = pd.DataFrame(get_industry_stocks(industry), columns=['code'])
            stocks_industry['industry'] = industry
            if len(stocks_industry) > 0:
                df_industry = df_industry.append(stocks_industry, ignore_index=True)

        stocks_industry = set(df_industry['code'])

        fundamentals = get_fundamentals(query(valuation.code, valuation.market_cap, valuation.pb_ratio, indicator.inc_operation_profit_year_on_year, cash_flow.goods_sale_and_service_render_cash
                    ).filter(valuation.code.in_(set(stocks) & stocks_industry)))

        fundamentals['mc_r'] = fundamentals['market_cap'].rank(ascending = True, method = 'max', pct=True)
        fundamentals = fundamentals[fundamentals['mc_r'] <= mc]
        fundamentals = fundamentals.set_index(['code'])

        df_industry = fundamentals.join(df_industry.set_index(['code']), how='left')
        df_group = df_industry.groupby(['industry'])['pb_ratio']
        df_stat = df_group.agg({'count':'count', 'min':'min','max':'max', 'std':'std', 'mean':'mean', 'median':'median', 'low': lambda x: np.percentile(x, q = pb)})
        df_stat = df_stat[df_stat['count'] >= 10]['low']

        df_stat = pd.DataFrame(df_stat)
        df_stat.index.name = None
        df_stat.columns = ['pb']

        df_industry = df_industry.join(df_stat, on='industry')
        df_industry = df_industry[df_industry['pb_ratio'] < df_industry['pb']]

        self.stocks = list(df_industry.index)

class StockFactor():
    def __init__(self, stocks):
        self.stocks = stocks

class PriceStockFactor(StockFactor):
    def __init__(self, stocks, prices):
        StockFactor.__init__(self, stocks)
        self.prices = prices

class VarStockFactor(PriceStockFactor):
    def generate(self, days, asc):
        df_var = self.prices[-(days+1):].pct_change()

        # 进行转置
        df_var = df_var.T
        # 生成方差
        df_var['VAR'] = df_var.var(axis = 1, skipna = True)
        # 生成新的DataFrame
        df_var = pd.DataFrame(df_var['VAR'])
        # 删除nan
        df_var = df_var.dropna()
        # 排序给出排序打分
        df_var['VAR_sorted_rank'] = df_var['VAR'].rank(ascending = asc, method = 'dense')

        return df_var

class IndexVarStockFactor(PriceStockFactor):
    def generate(self, days, asc, date, reference_index):
        df_var = self.prices[-(days+1):].pct_change()
        index_prices = get_price(reference_index,
            count = days+1,
            end_date=date,
            frequency='daily',
            fields='close')['close']

        df_index_var = index_prices.pct_change()
        df_var = df_var - df_index_var

        # 进行转置
        df_var = df_var.T
        # 生成方差
        df_var['IndexVar'] = df_var.var(axis = 1, skipna = True)
        # 生成新的DataFrame
        df_var = pd.DataFrame(df_var['IndexVar'])
        # 删除nan
        df_var = df_var.dropna()
        # 排序给出排序打分
        df_var['IndexVar_sorted_rank'] = df_var['IndexVar'].rank(ascending = asc, method = 'dense')

        return df_var

class VarChangeStockFactor(PriceStockFactor):
    def generate(self, days, asc):
        this_period_var_factor = VarStockFactor(self.stocks, self.prices)
        df_var_this_period = this_period_var_factor.generate(days, asc)
        del df_var_this_period['VAR_sorted_rank']
        df_var_this_period.columns = ["VAR_This"]

        last_period_var_factor = VarStockFactor(self.stocks, self.prices[-2 * days:-days])
        df_var_last_period = last_period_var_factor.generate(days, asc)
        del df_var_last_period['VAR_sorted_rank']
        df_var_last_period.columns = ["VAR_Last"]

        df = pd.concat([df_var_this_period, df_var_last_period], axis = 1)
        df['VARC'] = df['VAR_Last'] - df['VAR_This']
        df = df.dropna()
        df['VARC_sorted_rank'] = df['VARC'].rank(ascending = asc, method = 'dense')
        del df['VAR_This']
        del df['VAR_Last']

        return df

class MtmStockFactor(PriceStockFactor):
    def generate(self, days, asc):
        last_price = self.prices.iloc[-1]
        prev_price = self.prices.iloc[-days]

        price_pct_change = (last_price - prev_price) / prev_price
        mtm_name = 'MTM' + str(days)
        df = pd.DataFrame({mtm_name: price_pct_change})
        df = df.dropna()
        df[mtm_name + '_sorted_rank'] = df[mtm_name].rank(ascending = asc, method = 'dense')

        return df

class FlucStockFactor(PriceStockFactor):
    def generate(self, days, asc):
        max_price = self.prices.max(skipna = True)
        min_price = self.prices.min(skipna = True)
        start_price = self.prices.iloc[0]
        end_price = self.prices.iloc[-1]

        df = pd.DataFrame({'FLUC': (max_price - min_price) / (start_price + end_price)})
        df = df.dropna()

        df['FLUC_sorted_rank'] = df['FLUC'].rank(ascending = asc, method = 'dense')

        return df

class FundamentalStockFactor(StockFactor):
    def __init__(self, stocks):
        StockFactor.__init__(self, stocks)

    def generate(self, fundamentals, asc):
        factor_name = self.factor_name
        factor_sorted_rank_name = factor_name + '_sorted_rank'

        df = self.fundamentals_get_func(fundamentals)
        if hasattr(self, 'filter_func'):
            df = df[self.filter_func(df)]

        # 删除nan
        df = df.dropna()
        df[factor_name] = self.factor_get_value_func(df)
        # 生成排名序数
        df[factor_sorted_rank_name] = df[factor_name].rank(ascending = asc, method = 'dense')
        # 使用股票代码作为index
        df.index = df.code
        # 删除无用数据
        for column_name in df.columns.values:
            if column_name != factor_name and column_name != factor_sorted_rank_name:
                del df[column_name]

        # 改个名字
        df.columns = [self.factor_name, factor_sorted_rank_name]

        return df

class VolumeStockFactor(StockFactor):
    def __init__(self, stocks, volumes):
        StockFactor.__init__(self, stocks)
        self.volumes = volumes

class VVarStockFactor(VolumeStockFactor):
    def generate(self, days, asc):
        df_var = self.volumes[-(days+1):].pct_change()

        # 进行转置
        df_var = df_var.T
        # 生成方差
        df_var['VVAR'] = df_var.var(axis = 1, skipna = True)
        # 生成新的DataFrame
        df_var = pd.DataFrame(df_var['VVAR'])
        # 删除nan
        df_var = df_var.dropna()
        # 排序给出排序打分
        df_var['VVAR_sorted_rank'] = df_var['VVAR'].rank(ascending = asc, method = 'dense')

        return df_var

class TrStockFactor(VolumeStockFactor):
    def __init__(self, stocks, volumes):
        VolumeStockFactor.__init__(self, stocks, volumes)
        self.fundamentals = [valuation.code, valuation.circulating_cap]

    def generate(self, fundamentals, asc):
        total_volumes = self.volumes.sum(skipna = True).T

        df = fundamentals[['code', 'circulating_cap']]
        df.index = df.code
        df['TR'] = total_volumes / df['circulating_cap'] * 10000
        df.dropna()
        df['TR_sorted_rank'] = df['TR'].rank(ascending = asc, method = 'dense')
        del df['code']
        del df['circulating_cap']

        return df

class TrChangeStockFactor(TrStockFactor):
    def generate(self, fundamentals, days, end_date, asc):
        this_period_tr_factor = TrStockFactor(self.stocks, self.volumes)
        df_tr_this_period = this_period_tr_factor.generate(fundamentals, asc)
        del df_tr_this_period['TR_sorted_rank']

        df_tr_this_period.columns = ["TR_This"]

        last_period_end_date = shift_trading_day(end_date, -days)

        volumes = get_price(self.stocks,
           count = days,
           end_date = last_period_end_date,
           frequency = 'daily',
           fields = 'volume')['volume']

        last_period_tr_factor = TrStockFactor(self.stocks, volumes)

        df_fundamentals = get_fundamentals(query(*last_period_tr_factor.fundamentals
                              ).filter(indicator.code.in_(self.stocks)), last_period_end_date)

        df_tr_last_period = last_period_tr_factor.generate(df_fundamentals, asc)
        del df_tr_last_period['TR_sorted_rank']
        df_tr_last_period.columns = ["TR_Last"]

        df = pd.concat([df_tr_this_period, df_tr_last_period], axis = 1)
        df['TRC'] = df['TR_Last'] - df['TR_This']
        df = df.dropna()
        df['TRC_sorted_rank'] = df['TRC'].rank(ascending = asc, method = 'dense')
        del df['TR_This']
        del df['TR_Last']

        return df

class FundamentalChangeStockFactor(StockFactor):
    def generate(self, fundamentals, days, end_date, asc):
        factor_name = self.factor_name
        factor = self.fundamental_stock_factor(self.stocks)
        df_this_period = factor.generate(fundamentals, asc)
        del df_this_period[factor_name + '_sorted_rank']
        df_this_period.columns = ['This']

        last_period_end_date = shift_trading_day(end_date, -days)

        last_fundamentals = get_fundamentals(query(*factor.fundamentals).filter(indicator.code.in_(self.stocks)), last_period_end_date)

        df_last_period = factor.generate(last_fundamentals, asc)
        del df_last_period[factor_name + '_sorted_rank']
        df_last_period.columns = ['Last']

        df = pd.concat([df_this_period, df_last_period], axis = 1)
        df[factor_name + 'C'] = df['Last'] - df['This']
        df = df.dropna()
        df[factor_name + 'C_sorted_rank'] = df[ factor_name + 'C'].rank(ascending = asc, method = 'dense')
        del df['This']
        del df['Last']

        return df

class FundamentalPercentageChangeStockFactor(StockFactor):
    def generate(self, fundamentals, days, end_date, asc):
        factor_name = self.factor_name
        factor = self.fundamental_stock_factor(self.stocks)
        df_this_period = factor.generate(fundamentals, asc)
        del df_this_period[factor_name + '_sorted_rank']
        df_this_period.columns = ['This']

        last_period_end_date = shift_trading_day(end_date, -days)

        last_fundamentals = get_fundamentals(query(*factor.fundamentals).filter(indicator.code.in_(self.stocks)), last_period_end_date)

        df_last_period = factor.generate(last_fundamentals, asc)
        del df_last_period[factor_name + '_sorted_rank']
        df_last_period.columns = ['Last']

        df = pd.concat([df_this_period, df_last_period], axis = 1)
        df[factor_name + 'C'] = (df['Last'] - df['This']) / df['Last']
        df = df.dropna()
        df[factor_name + 'C_sorted_rank'] = df[ factor_name + 'C'].rank(ascending = asc, method = 'dense')
        del df['This']
        del df['Last']

        return df

class RoeStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, indicator.roe]
        self.factor_name = "ROE"
        self.fundamentals_get_func = lambda f: f[['code', 'roe']]
        self.factor_get_value_func = lambda f: f['roe']

class RoeChangeStockFactor(FundamentalChangeStockFactor, RoeStockFactor):
    def __init__(self, stocks):
        RoeStockFactor.__init__(self, stocks)
        self.fundamental_stock_factor = RoeStockFactor

class RoaStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code,
                                    # 负债和股东权益合计
                                    balance.total_sheet_owner_equities,
                                    # 净利润(元)
                                    income.net_profit,
                                    # 所得税费用(元)
                                    income.income_tax_expense,
                                    # 应付利息(元)
                                    balance.interest_payable]
        self.factor_name = "ROA"
        self.fundamentals_get_func = lambda f: f[['code',
                                                  'total_sheet_owner_equities',
                                                  'net_profit',
                                                  'income_tax_expense',
                                                  'interest_payable']]
        self.factor_get_value_func = lambda f: (f['net_profit']
                                               + f['income_tax_expense']
                                               + f['interest_payable']
                                               )/f['total_sheet_owner_equities']

class RoaChangeStockFactor(FundamentalChangeStockFactor, RoaStockFactor):
    def __init__(self, stocks):
        RoaStockFactor.__init__(self, stocks)
        self.fundamental_stock_factor = RoaStockFactor


class OptpStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, income.operating_profit, income.total_profit]
        self.factor_name = "OPTP"
        self.fundamentals_get_func = lambda f: f[['code', 'operating_profit', 'total_profit']]
        self.factor_get_value_func = lambda f: f['operating_profit'] / f['total_profit']

class NporStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, income.net_profit, income.operating_revenue]
        self.factor_name = "NPOR"
        self.fundamentals_get_func = lambda f: f[['code', 'net_profit', 'operating_revenue']]
        self.factor_get_value_func = lambda f: f['net_profit'] / f['operating_revenue']

class NporChangeStockFactor(FundamentalChangeStockFactor, NporStockFactor):
    def __init__(self, stocks):
        NporStockFactor.__init__(self, stocks)
        self.fundamental_stock_factor = NporStockFactor

class BpStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, valuation.pb_ratio]
        self.factor_name = "BP"
        self.fundamentals_get_func = lambda f: f[['code', 'pb_ratio']]
        self.factor_get_value_func = lambda f: f['pb_ratio'].apply(lambda x: 1/x)

class BpChangeStockFactor(FundamentalPercentageChangeStockFactor, BpStockFactor):
    def __init__(self, stocks):
        BpStockFactor.__init__(self, stocks)
        self.fundamental_stock_factor = BpStockFactor

class EpStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, valuation.pe_ratio]
        self.factor_name = "EP"
        self.fundamentals_get_func = lambda f: f[['code', 'pe_ratio']]
        self.filter_func = lambda f: (f.pe_ratio >0)
        self.factor_get_value_func = lambda f: f['pe_ratio'].apply(lambda x: 1/x)

class EpChangeStockFactor(FundamentalPercentageChangeStockFactor, EpStockFactor):
    def __init__(self, stocks):
        EpStockFactor.__init__(self, stocks)
        self.fundamental_stock_factor = EpStockFactor

class PegStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, valuation.pe_ratio, indicator.inc_net_profit_year_on_year]
        self.factor_name = "PEG"
        self.fundamentals_get_func = lambda f: f[['code', 'pe_ratio', 'inc_net_profit_year_on_year']]
        self.filter_func = lambda f: (f.pe_ratio >0) & (f.inc_net_profit_year_on_year >0)
        self.factor_get_value_func = lambda f: f['pe_ratio'] / f['inc_net_profit_year_on_year']

class DpStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, balance.dividend_payable, valuation.market_cap]
        self.factor_name = "DP"
        self.fundamentals_get_func = lambda f: f[['code', 'dividend_payable', 'market_cap']]
        self.factor_get_value_func = lambda f: f['dividend_payable'] / (f['market_cap']*100000000)

class CfpStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, valuation.pcf_ratio]
        self.factor_name = "CFP"
        self.fundamentals_get_func = lambda f: f[['code', 'pcf_ratio']]
        self.factor_get_value_func = lambda f: f['pcf_ratio'].apply(lambda x: 1/x)

class PsStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, valuation.ps_ratio]
        self.factor_name = "PS"
        self.fundamentals_get_func = lambda f: f[['code', 'ps_ratio']]
        self.factor_get_value_func = lambda f: f['ps_ratio']

class AlrStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, balance.total_liability, balance.total_assets]
        self.factor_name = "ALR"
        self.fundamentals_get_func = lambda f: f[['code', 'total_liability', 'total_assets']]
        self.factor_get_value_func = lambda f: f['total_liability'] / f['total_assets']

class CmcStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, valuation.circulating_market_cap]
        self.factor_name = "CMC"
        self.fundamentals_get_func = lambda f: f[['code', 'circulating_market_cap']]
        self.factor_get_value_func = lambda f: f['circulating_market_cap']

class FacrStockFactor(FundamentalStockFactor):
    def __init__(self, stocks):
        FundamentalStockFactor.__init__(self, stocks)
        self.fundamentals = [valuation.code, balance.fixed_assets, balance.total_assets]
        self.factor_name = "FACR"
        self.fundamentals_get_func = lambda f: f[['code', 'fixed_assets', 'total_assets']]
        self.factor_get_value_func = lambda f: f['fixed_assets'] / f['total_assets']

def get_turning_point(prices, window = 0):
    if window <= 0:
            raise ValueError("window should be greater than 0")

    if len(prices) <= window * 3:
            raise ValueError("prices len should be greater than window * 3")

    prices = prices.reset_index()
    double_window = window * 2

    df = pd.concat([prices,
                pd.rolling_apply(prices.ix[:,-1:], double_window, lambda x: pd.Series(x).min()),
                pd.rolling_apply(prices.ix[:,-1:], double_window, lambda x: pd.Series(x).argmin()),
                pd.rolling_apply(prices.ix[:,-1:], double_window, lambda x: pd.Series(x).max()),
                pd.rolling_apply(prices.ix[:,-1:], double_window, lambda x: pd.Series(x).argmax())
              ], axis=1)


    df.columns = ['date', 'close', 'rolling_min_close', 'rolling_min_index', 'rolling_max_close', 'rolling_max_index']
    df['rolling_min_date'] = df.ix[df.index - (window - 1 - df['rolling_min_index'])]['date'].values
    df['rolling_max_date'] = df.ix[df.index - (window - 1 - df['rolling_max_index'])]['date'].values

    df['rolling_date'] = df['date'].shift(window)
    df.index = df['date']
    df = df[df.rolling_date.notnull()]

    df_min = df[df['date'] == df['rolling_min_date']][['rolling_date']]
    df_max = df[df['date'] == df['rolling_max_date']][['rolling_date']]

    df_min = df[df['date'].isin(df_min['rolling_date'])][['close']]
    df_max = df[df['date'].isin(df_max['rolling_date'])][['close']]


    return df_min['close'], df_max['close']


# 设置可行股票池
# 过滤掉当日停牌的股票,且筛选出前days天未停牌股票
# 输入：stock_list为list类型,样本天数days为int类型，context（见API）
# 输出：list=g.feasible_stocks
def set_feasible_stocks(stock_list,days,end_date):
    # 得到是否停牌信息的dataframe，停牌的1，未停牌得0
    suspened_info_df = get_price(list(stock_list),
                       count = days + 1,
                       end_date= end_date,
                       frequency='daily',
                       fields='paused')['paused']

    suspend_days = suspened_info_df.sum()

    unsuspened_index = suspend_days[suspend_days == 0]

    return list(unsuspened_index.index)

def get_trading_day_num_from(start_date, end_date):
    tradingdays = get_trade_days(start_date, end_date)

    return len(tradingdays)

def get_trading_week_no_in_month(date):
    first_trading_day = get_first_trading_day_of_month(date)

    return (date - first_trading_day).days // 7 + 1

def get_first_trading_day_of_month(date):
    tradingday = get_all_trade_days()

    first_day_of_month = date.replace(day=1)

    for day in range(1, 20):
         shift_day = (first_day_of_month + relativedelta(days=day))
         if shift_day in tradingday:
            return shift_day
    return None


def shift_trading_day(date, shift):
    # 获取所有的交易日，返回一个包含所有交易日的 list,元素值为 datetime.date 类型.
    tradingday = get_all_trade_days()
    # 得到date之后shift天那一天在列表中的行标号 返回一个数
    shiftday_index = list(tradingday).index(date)+shift
    # 根据行号返回该日日期 为datetime.date类型
    return tradingday[shiftday_index]

def get_linear(prices):
    prices_mean = prices.mean()
    factor = 10000 / prices_mean
    prices = prices * factor

    days = np.arange(1, len(prices) + 1)

    linear = stats.linregress(days, prices)

    return linear

def set_backtest(g):
    set_benchmark(g.indices[0])       # 设置为基准
    set_option('use_real_price', True) # 用真实价格交易
    log.set_level('order', 'error')    # 设置报错等级

def set_slip_fee(date):
    # 根据不同的时间段设置手续费
    if date > dt.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003,
                                sell_cost=0.0013,
                                min_cost=5))
    elif date > dt.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001,
                                sell_cost=0.002,
                                min_cost=5))
    elif date > dt.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002,
                                sell_cost=0.003,
                                min_cost=5))
    else:
        set_commission(PerTrade(buy_cost=0.003,
                                sell_cost=0.004,
                                min_cost=5))

def get_indexes_display_name(indexes):
    global all_indexes

    if all_indexes is None:
        all_indexes = get_all_securities(['index'])

    return all_indexes.loc[indexes]['display_name']

def get_new_stocks_pct(date, shift):
    all_securities = get_all_securities(date=date)
    new_securities = all_securities[(all_securities['start_date'] > shift_trading_day(date, -shift))]

    return len(new_securities) / (len(all_securities) + 0.1)

def count_positive(values):
    return sum(x>0 for x in values)

def send_163_email(subject,message):
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header

    '''
    记得请先开启邮箱的SMTP服务
    '''
    ## 发送邮件
    sender = 'luke19807346@163.com' #发送的邮箱
    receiver = 'luke19807346@163.com' #要接受的邮箱（注:测试中发送其他邮箱会提示错误）
    smtpserver = 'smtp.163.com'
    username = 'luke19807346@163.com' #你的邮箱账号
    password = 'Ekx5oE8yKo' #你的邮箱密码
