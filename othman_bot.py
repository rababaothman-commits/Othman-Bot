//@version=6
indicator("مستويات البيفوت + شهري - Pivot Levels", overlay=true, max_lines_count=500)

// ========== الإعدادات - جميعها في البداية ==========
showMonthly = input.bool(true, "إظهار الشهر", group="الإطارات الزمنية")
showWeekly = input.bool(true, "إظهار الأسبوع", group="الإطارات الزمنية")
showDaily = input.bool(true, "إظهار اليوم", group="الإطارات الزمنية")
showH4 = input.bool(true, "إظهار 4 ساعات", group="الإطارات الزمنية")
showMidpoints = input.bool(true, "إظهار المستويات الوسيطة", group="الإطارات الزمنية")
showLabels = input.bool(true, "إظهار التسميات", group="الإعدادات")

// الألوان
colorMonthlyPivot = input.color(color.new(color.purple, 0), "M Pivot", group="الشهر")
colorMonthlyR1 = input.color(color.new(color.red, 10), "M R1", group="الشهر")
colorMonthlyS1 = input.color(color.new(color.green, 10), "M S1", group="الشهر")
colorMonthlyR2 = input.color(color.new(color.red, 30), "M R2", group="الشهر")
colorMonthlyS2 = input.color(color.new(color.green, 30), "M S2", group="الشهر")

colorWeeklyPivot = input.color(color.new(color.yellow, 0), "W Pivot", group="الأسبوع")
colorWeeklyR1 = input.color(color.new(color.red, 20), "W R1", group="الأسبوع")
colorWeeklyS1 = input.color(color.new(color.green, 20), "W S1", group="الأسبوع")
colorWeeklyR2 = input.color(color.new(color.red, 40), "W R2", group="الأسبوع")
colorWeeklyS2 = input.color(color.new(color.green, 40), "W S2", group="الأسبوع")

colorDailyPivot = input.color(color.new(color.orange, 0), "D Pivot", group="اليوم")
colorDailyR1 = input.color(color.new(color.red, 30), "D R1", group="اليوم")
colorDailyS1 = input.color(color.new(color.green, 30), "D S1", group="اليوم")
colorDailyR2 = input.color(color.new(color.red, 50), "D R2", group="اليوم")
colorDailyS2 = input.color(color.new(color.green, 50), "D S2", group="اليوم")

colorH4Pivot = input.color(color.new(color.aqua, 0), "4H Pivot", group="4 ساعات")
colorH4R1 = input.color(color.new(color.red, 40), "4H R1", group="4 ساعات")
colorH4S1 = input.color(color.new(color.green, 40), "4H S1", group="4 ساعات")
colorH4R2 = input.color(color.new(color.red, 60), "4H R2", group="4 ساعات")
colorH4S2 = input.color(color.new(color.green, 60), "4H S2", group="4 ساعات")

colorMidSupport = input.color(color.new(color.green, 70), "MS", group="المستويات الوسيطة")
colorMidResistance = input.color(color.new(color.red, 70), "MR", group="المستويات الوسيطة")

lineWidthMonth = input.int(3, "سُمك الشهر", minval=1, maxval=5)
lineWidth = input.int(2, "سُمك الخط", minval=1, maxval=5)
lineWidthMid = input.int(1, "سُمك الوسيط", minval=1, maxval=3)

// ========== جلب البيانات ==========
[monthlyH, monthlyL, monthlyC] = request.security(syminfo.tickerid, "M", [high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)
[weeklyH, weeklyL, weeklyC] = request.security(syminfo.tickerid, "W", [high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)
[dailyH, dailyL, dailyC] = request.security(syminfo.tickerid, "D", [high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)
[h4H, h4L, h4C] = request.security(syminfo.tickerid, "240", [high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)

// ========== حساب المستويات - الشهر ==========
monthlyPP = (monthlyH + monthlyL + monthlyC) / 3
monthlyR1 = 2 * monthlyPP - monthlyL
monthlyS1 = 2 * monthlyPP - monthlyH
monthlyR2 = monthlyPP + (monthlyH - monthlyL)
monthlyS2 = monthlyPP - (monthlyH - monthlyL)
monthlyR3 = monthlyPP + 1.5 * (monthlyH - monthlyL)
monthlyS3 = monthlyPP - 1.5 * (monthlyH - monthlyL)
monthlyMR = (monthlyPP + monthlyR1) / 2
monthlyMS = (monthlyPP + monthlyS1) / 2

// ========== حساب المستويات - الأسبوع ==========
weeklyPP = (weeklyH + weeklyL + weeklyC) / 3
weeklyR1 = 2 * weeklyPP - weeklyL
weeklyS1 = 2 * weeklyPP - weeklyH
weeklyR2 = weeklyPP + (weeklyH - weeklyL)
weeklyS2 = weeklyPP - (weeklyH - weeklyL)
weeklyR3 = weeklyPP + 1.5 * (weeklyH - weeklyL)
weeklyS3 = weeklyPP - 1.5 * (weeklyH - weeklyL)
weeklyMR = (weeklyPP + weeklyR1) / 2
weeklyMS = (weeklyPP + weeklyS1) / 2

// ========== حساب المستويات - اليوم ==========
dailyPP = (dailyH + dailyL + dailyC) / 3
dailyR1 = 2 * dailyPP - dailyL
dailyS1 = 2 * dailyPP - dailyH
dailyR2 = dailyPP + (dailyH - dailyL)
dailyS2 = dailyPP - (dailyH - dailyL)
dailyR3 = dailyPP + 1.5 * (dailyH - dailyL)
dailyS3 = dailyPP - 1.5 * (dailyH - dailyL)
dailyMR = (dailyPP + dailyR1) / 2
dailyMS = (dailyPP + dailyS1) / 2

// ========== حساب المستويات - 4 ساعات ==========
h4PP = (h4H + h4L + h4C) / 3
h4R1 = 2 * h4PP - h4L
h4S1 = 2 * h4PP - h4H
h4R2 = h4PP + (h4H - h4L)
h4S2 = h4PP - (h4H - h4L)
h4R3 = h4PP + 1.5 * (h4H - h4L)
h4S3 = h4PP - 1.5 * (h4H - h4L)
h4MR = (h4PP + h4R1) / 2
h4MS = (h4PP + h4S1) / 2

// ========== الرسم - الشهر ==========
plot(showMonthly ? monthlyPP : na, "M-PP", colorMonthlyPivot, lineWidthMonth)
plot(showMonthly ? monthlyR1 : na, "M-R1", colorMonthlyR1, lineWidthMonth)
plot(showMonthly ? monthlyS1 : na, "M-S1", colorMonthlyS1, lineWidthMonth)
plot(showMonthly ? monthlyR2 : na, "M-R2", colorMonthlyR2, lineWidthMonth)
plot(showMonthly ? monthlyS2 : na, "M-S2", colorMonthlyS2, lineWidthMonth)
plot(showMonthly and showMidpoints ? monthlyR3 : na, "M-R3", color.new(color.red, 80), lineWidthMid)
plot(showMonthly and showMidpoints ? monthlyS3 : na, "M-S3", color.new(color.green, 80), lineWidthMid)
plot(showMonthly and showMidpoints ? monthlyMR : na, "M-MR", colorMidResistance, lineWidthMid)
plot(showMonthly and showMidpoints ? monthlyMS : na, "M-MS", colorMidSupport, lineWidthMid)

// ========== الرسم - الأسبوع ==========
plot(showWeekly ? weeklyPP : na, "W-PP", colorWeeklyPivot, lineWidth)
plot(showWeekly ? weeklyR1 : na, "W-R1", colorWeeklyR1, lineWidth)
plot(showWeekly ? weeklyS1 : na, "W-S1", colorWeeklyS1, lineWidth)
plot(showWeekly ? weeklyR2 : na, "W-R2", colorWeeklyR2, lineWidth)
plot(showWeekly ? weeklyS2 : na, "W-S2", colorWeeklyS2, lineWidth)
plot(showWeekly and showMidpoints ? weeklyR3 : na, "W-R3", color.new(color.red, 80), lineWidthMid)
plot(showWeekly and showMidpoints ? weeklyS3 : na, "W-S3", color.new(color.green, 80), lineWidthMid)
plot(showWeekly and showMidpoints ? weeklyMR : na, "W-MR", colorMidResistance, lineWidthMid)
plot(showWeekly and showMidpoints ? weeklyMS : na, "W-MS", colorMidSupport, lineWidthMid)

// ========== الرسم - اليوم ==========
plot(showDaily ? dailyPP : na, "D-PP", colorDailyPivot, lineWidth)
plot(showDaily ? dailyR1 : na, "D-R1", colorDailyR1, lineWidth)
plot(showDaily ? dailyS1 : na, "D-S1", colorDailyS1, lineWidth)
plot(showDaily ? dailyR2 : na, "D-R2", colorDailyR2, lineWidth)
plot(showDaily ? dailyS2 : na, "D-S2", colorDailyS2, lineWidth)
plot(showDaily and showMidpoints ? dailyR3 : na, "D-R3", color.new(color.red, 80), lineWidthMid)
plot(showDaily and showMidpoints ? dailyS3 : na, "D-S3", color.new(color.green, 80), lineWidthMid)
plot(showDaily and showMidpoints ? dailyMR : na, "D-MR", colorMidResistance, lineWidthMid)
plot(showDaily and showMidpoints ? dailyMS : na, "D-MS", colorMidSupport, lineWidthMid)

// ========== الرسم - 4 ساعات ==========
plot(showH4 ? h4PP : na, "4H-PP", colorH4Pivot, lineWidth)
plot(showH4 ? h4R1 : na, "4H-R1", colorH4R1, lineWidth)
plot(showH4 ? h4S1 : na, "4H-S1", colorH4S1, lineWidth)
plot(showH4 ? h4R2 : na, "4H-R2", colorH4R2, lineWidth)
plot(showH4 ? h4S2 : na, "4H-S2", colorH4S2, lineWidth)
plot(showH4 and showMidpoints ? h4R3 : na, "4H-R3", color.new(color.red, 80), lineWidthMid)
plot(showH4 and showMidpoints ? h4S3 : na, "4H-S3", color.new(color.green, 80), lineWidthMid)
plot(showH4 and showMidpoints ? h4MR : na, "4H-MR", colorMidResistance, lineWidthMid)
plot(showH4 and showMidpoints ? h4MS : na, "4H-MS", colorMidSupport, lineWidthMid)

// ========== التسميات - جميع المستويات ==========
if barstate.islast and showLabels
    // ===== MONTHLY =====
    if showMonthly
        label.new(bar_index, monthlyPP, "M-PP", style=label.style_label_left, color=colorMonthlyPivot, textcolor=color.white, size=size.small)
        label.new(bar_index, monthlyR1, "M-R1", style=label.style_label_left, color=colorMonthlyR1, textcolor=color.white, size=size.small)
        label.new(bar_index, monthlyS1, "M-S1", style=label.style_label_left, color=colorMonthlyS1, textcolor=color.white, size=size.small)
        label.new(bar_index, monthlyR2, "M-R2", style=label.style_label_left, color=colorMonthlyR2, textcolor=color.white, size=size.small)
        label.new(bar_index, monthlyS2, "M-S2", style=label.style_label_left, color=colorMonthlyS2, textcolor=color.white, size=size.small)
        if showMidpoints
            label.new(bar_index, monthlyR3, "M-R3", style=label.style_label_left, color=color.new(color.red, 80), textcolor=color.white, size=size.small)
            label.new(bar_index, monthlyS3, "M-S3", style=label.style_label_left, color=color.new(color.green, 80), textcolor=color.white, size=size.small)
            label.new(bar_index, monthlyMR, "M-MR⭐", style=label.style_label_left, color=colorMidResistance, textcolor=color.white, size=size.small)
            label.new(bar_index, monthlyMS, "M-MS⭐", style=label.style_label_left, color=colorMidSupport, textcolor=color.white, size=size.small)
   
    // ===== WEEKLY =====
    if showWeekly
        label.new(bar_index, weeklyPP, "W-PP", style=label.style_label_left, color=colorWeeklyPivot, textcolor=color.black, size=size.small)
        label.new(bar_index, weeklyR1, "W-R1", style=label.style_label_left, color=colorWeeklyR1, textcolor=color.white, size=size.small)
        label.new(bar_index, weeklyS1, "W-S1", style=label.style_label_left, color=colorWeeklyS1, textcolor=color.white, size=size.small)
        label.new(bar_index, weeklyR2, "W-R2", style=label.style_label_left, color=colorWeeklyR2, textcolor=color.white, size=size.small)
        label.new(bar_index, weeklyS2, "W-S2", style=label.style_label_left, color=colorWeeklyS2, textcolor=color.white, size=size.small)
        if showMidpoints
            