---
video_id: qcTcsEdMgBo
url: https://www.youtube.com/watch?v=qcTcsEdMgBo
title: Range | Interquartile Range (IQR) | Box and whisker plot
channel: zedstatistics
duration: 9:07
language: en
unit: L02
status: OK
---

[00:03] [Music] hi guys today is going to be all about
[00:08] hi guys today is going to be all about Rangers on our descriptive statistics
[00:12] Rangers on our descriptive statistics series here that is rangers and IQR
[00:16] series here that is rangers and IQR interquartile ranges now if you want to
[00:20] interquartile ranges now if you want to see the rest of the videos in the series
[00:21] see the rest of the videos in the series head over to Z statistics comm that's my
[00:25] head over to Z statistics comm that's my website where I've got a whole bunch of
[00:27] website where I've got a whole bunch of statistical resources for you including
[00:29] statistical resources for you including the rest of the elements of this series
[00:31] the rest of the elements of this series and some stuff on regression hypothesis
[00:35] and some stuff on regression hypothesis testing you names it let's get stuck
[00:39] testing you names it let's get stuck straight into probably one of the most
[00:41] straight into probably one of the most simple statistical measures today and
[00:43] simple statistical measures today and it's the first one where we're going to
[00:44] it's the first one where we're going to start to deal with this concept of
[00:47] start to deal with this concept of dispersion or spread so there shouldn't
[00:51] dispersion or spread so there shouldn't take us too long we're just going to
[00:52] take us too long we're just going to look at the definition of these two
[00:54] look at the definition of these two different quantities and then we'll have
[00:56] different quantities and then we'll have a look at how they both apply in a
[00:58] a look at how they both apply in a box-and-whisker plot where we'll be able
[01:01] box-and-whisker plot where we'll be able to visually inspect our range and
[01:04] to visually inspect our range and interquartile range so let's consider
[01:06] interquartile range so let's consider this ordered dataset which has seven
[01:09] this ordered dataset which has seven elements now as I said the range is a
[01:12] elements now as I said the range is a measure of the spread of the data set
[01:14] measure of the spread of the data set and it's simply the maximum value minus
[01:17] and it's simply the maximum value minus the minimum value so 13 minus 2 is going
[01:20] the minimum value so 13 minus 2 is going to give us a range of 11 pretty
[01:24] to give us a range of 11 pretty straightforward right so what then is
[01:28] straightforward right so what then is the interquartile range and importantly
[01:31] the interquartile range and importantly why do we need it let's have a look at
[01:33] why do we need it let's have a look at the definition first the interquartile
[01:36] the definition first the interquartile range is going to be the third quartile
[01:38] range is going to be the third quartile minus the first quartile so if you
[01:42] minus the first quartile so if you recall from the previous video on
[01:45] recall from the previous video on quantiles where we looked at quartiles
[01:48] quantiles where we looked at quartiles the first quartile is that number in the
[01:51] the first quartile is that number in the series which is a which is about a
[01:53] series which is a which is about a quarter of the way into the data set the
[01:56] quarter of the way into the data set the second quartile is two quarters of the
[01:59] second quartile is two quarters of the way into the data set in other words
[02:01] way into the data set in other words that's the median and the third quartile
[02:03] that's the median and the third quartile is three quarters into the data set so
[02:09] is three quarters into the data set so instead of being the maximum minus the
[02:10] instead of being the maximum minus the minimum this is going to be quartile 3
[02:13] minimum this is going to be quartile 3 which is 10
[02:14] which is 10 - quartile 1 which is - which gives us
[02:18] - quartile 1 which is - which gives us an inter quartile range of 8 now if
[02:23] an inter quartile range of 8 now if you're worried as to why these two are
[02:25] you're worried as to why these two are exactly quartile 1 and quartile 3 then
[02:29] exactly quartile 1 and quartile 3 then you best head back and have a look at
[02:31] you best head back and have a look at how we calculate quartiles but for the
[02:34] how we calculate quartiles but for the sake of this video we're just interested
[02:36] sake of this video we're just interested in why we bother dealing with inter
[02:39] in why we bother dealing with inter quartile ranges when we've already got
[02:41] quartile ranges when we've already got something to measure the spread which
[02:43] something to measure the spread which was the range in itself so what possible
[02:47] was the range in itself so what possible benefit do we have from using this
[02:48] benefit do we have from using this interquartile range
[02:54] well let's think of it this way imagine instead if the maximum value was not 13
[02:59] instead if the maximum value was not 13 let's just say the maximum value
[03:01] let's just say the maximum value happened to be 58 so everything else was
[03:05] happened to be 58 so everything else was the same except we had this huge outlier
[03:07] the same except we had this huge outlier as one of the values now the range for
[03:11] as one of the values now the range for this data set becomes 56 it's the
[03:13] this data set becomes 56 it's the maximum minus the minimum and it seems
[03:16] maximum minus the minimum and it seems to suggest that this data set has a very
[03:19] to suggest that this data set has a very large spread but in reality most of the
[03:23] large spread but in reality most of the data points are very close to the first
[03:25] data points are very close to the first data point which is 2 it's only this
[03:29] data point which is 2 it's only this last one which is very extreme it seems
[03:32] last one which is very extreme it seems so you can see here that range is
[03:35] so you can see here that range is susceptible to outliers and that often
[03:37] susceptible to outliers and that often gives us a an incorrect impression of
[03:40] gives us a an incorrect impression of how spread the data is but you'll notice
[03:43] how spread the data is but you'll notice that the interquartile range here hasn't
[03:45] that the interquartile range here hasn't changed it's still 10 minus 2 giving us
[03:49] changed it's still 10 minus 2 giving us 8 so the presence of one outlier here
[03:52] 8 so the presence of one outlier here doesn't affect our interquartile range
[03:54] doesn't affect our interquartile range but it does affect our range now there
[03:59] but it does affect our range now there are different applications for each of
[04:01] are different applications for each of these sometimes you just want the range
[04:03] these sometimes you just want the range you want the maximum minus the minimum
[04:05] you want the maximum minus the minimum but other times you want to try to avoid
[04:08] but other times you want to try to avoid this outlier problem here so let's look
[04:13] this outlier problem here so let's look at the box and whisker plot now
[04:16] at the box and whisker plot now so the inspiration for this example here
[04:19] so the inspiration for this example here is my increasing addiction to Messina
[04:23] is my increasing addiction to Messina ice cream which is just up the road from
[04:25] ice cream which is just up the road from my place
[04:25] my place dangerously I should say so here are all
[04:28] dangerously I should say so here are all of the flavors from the Cena
[04:31] of the flavors from the Cena don't ask me what Nikki glasses is but
[04:34] don't ask me what Nikki glasses is but if you're telling me that there's a
[04:36] if you're telling me that there's a better flavor than pistachio praline you
[04:38] better flavor than pistachio praline you are out of luck my friend it is the
[04:41] are out of luck my friend it is the clear winner for mine nonetheless we're
[04:44] clear winner for mine nonetheless we're actually assessing the grams of sugar in
[04:46] actually assessing the grams of sugar in each scoop of these ice creams so pandan
[04:50] each scoop of these ice creams so pandan and coconut has the most sugar and
[04:53] and coconut has the most sugar and yogurt and caramel has the least down
[04:55] yogurt and caramel has the least down the bottom here now of course there's
[04:57] the bottom here now of course there's many flavors in between but I'm just
[04:59] many flavors in between but I'm just showing you the top ones and the bottom
[05:01] showing you the top ones and the bottom ones here completely fictionalized by
[05:04] ones here completely fictionalized by the way I don't actually want to know
[05:06] the way I don't actually want to know how many grams of sugar there are in
[05:07] how many grams of sugar there are in each of those scoops
[05:10] each of those scoops so if pan down and coconuts the maximum
[05:13] so if pan down and coconuts the maximum and yogurt and caramel is the minimum we
[05:17] and yogurt and caramel is the minimum we can kind of draw this is called a
[05:19] can kind of draw this is called a box-and-whisker plot these whiskers
[05:21] box-and-whisker plot these whiskers which is the black bits go from the
[05:24] which is the black bits go from the minimum to the maximum and then we have
[05:27] minimum to the maximum and then we have this box in the middle with three
[05:29] this box in the middle with three horizontal lines now you can probably
[05:31] horizontal lines now you can probably guess that these lines are going to be
[05:33] guess that these lines are going to be the first quartile the median and the
[05:38] the first quartile the median and the third quartile now in this configuration
[05:41] third quartile now in this configuration this is a vertical configuration of a
[05:43] this is a vertical configuration of a box and whisker plot sometimes you'll
[05:45] box and whisker plot sometimes you'll see it horizontal so obviously it would
[05:47] see it horizontal so obviously it would go from left to right going from
[05:49] go from left to right going from quartile one to quartile two to quartile
[05:52] quartile one to quartile two to quartile 3 etc but here quartile one is on the
[05:55] 3 etc but here quartile one is on the bottom of the box the medians the middle
[05:58] bottom of the box the medians the middle strip and the quartile 3 is the top part
[06:01] strip and the quartile 3 is the top part of the box and then you've got the
[06:03] of the box and then you've got the maximum and minimum being the whiskers
[06:05] maximum and minimum being the whiskers now I might just make a note here to say
[06:08] now I might just make a note here to say that some statistical packages when they
[06:11] that some statistical packages when they draw up this box and whisker plot will
[06:14] draw up this box and whisker plot will exclude outliers from the maximum and
[06:17] exclude outliers from the maximum and minimum value so the ends of the
[06:19] minimum value so the ends of the whiskers would represent those values
[06:22] whiskers would represent those values the maximum and minimum not including
[06:25] the maximum and minimum not including those values considered to be too
[06:27] those values considered to be too extreme or outliers and it'll depend on
[06:30] extreme or outliers and it'll depend on the statistical software what their
[06:32] the statistical software what their criteria is for declaring observations
[06:35] criteria is for declaring observations and outlier anyway you get the sense
[06:39] and outlier anyway you get the sense here that you can see this interquartile
[06:41] here that you can see this interquartile range which is the difference between
[06:43] range which is the difference between the bottom and top of the box versus the
[06:47] the bottom and top of the box versus the range itself which is the difference
[06:49] range itself which is the difference between the whiskers so we can calculate
[06:52] between the whiskers so we can calculate those pretty simply maximum minus
[06:54] those pretty simply maximum minus minimum which is 26 point one minus
[06:57] minimum which is 26 point one minus twelve point two and that gives us
[06:59] twelve point two and that gives us thirteen point nine is our range and the
[07:03] thirteen point nine is our range and the interquartile range is it's going to be
[07:04] interquartile range is it's going to be the twenty three point five minus
[07:06] the twenty three point five minus nineteen point one now I just pulled
[07:09] nineteen point one now I just pulled these out of thin air but let's just
[07:11] these out of thin air but let's just presume that they are indeed quartile 3
[07:13] presume that they are indeed quartile 3 and quartile one for this data set and
[07:17] and quartile one for this data set and hopefully you get a sense of how box and
[07:20] hopefully you get a sense of how box and whisker plots are quite useful as well
[07:22] whisker plots are quite useful as well each section has 25% of the data so
[07:27] each section has 25% of the data so we've got 25% of the ice cream scoops up
[07:31] we've got 25% of the ice cream scoops up here in the top whisker we got another
[07:34] here in the top whisker we got another 25% between the median and the third
[07:36] 25% between the median and the third quartile another 25% between the first
[07:39] quartile another 25% between the first quartile and the median and we have 25%
[07:43] quartile and the median and we have 25% of the data down here as well so this is
[07:46] of the data down here as well so this is more sort of spread out so this gives us
[07:50] more sort of spread out so this gives us the impression that there's only maybe a
[07:51] the impression that there's only maybe a couple of low sugar ice creams down here
[07:55] couple of low sugar ice creams down here and they kind of spread out over this
[07:58] and they kind of spread out over this range from nineteen point one to twelve
[08:00] range from nineteen point one to twelve point two whereas most of the ice creams
[08:03] point two whereas most of the ice creams actually exist above nineteen point one
[08:06] actually exist above nineteen point one so there you have it a simple little
[08:10] so there you have it a simple little video for range and interquartile range
[08:13] video for range and interquartile range the rest of these videos on this bottom
[08:16] the rest of these videos on this bottom line here are going to be alternate
[08:19] line here are going to be alternate classifications of spread and they're
[08:22] classifications of spread and they're gonna get a little bit more
[08:23] gonna get a little bit more statistically robust as well so stick
[08:26] statistically robust as well so stick around for those go to Z statistics com
[08:29] around for those go to Z statistics com if you want to skip through to any of
[08:30] if you want to skip through to any of these videos or indeed any video I've
[08:33] these videos or indeed any video I've created over the last 10 years or so
[08:35] created over the last 10 years or so thanks for watching my name is justin's
[08:37] thanks for watching my name is justin's Elsa and if you dig this feel free to
[08:39] Elsa and if you dig this feel free to like the video subscribe and do all that
[08:41] like the video subscribe and do all that kind of stuff and I also have a podcast
[08:43] kind of stuff and I also have a podcast which is called Jeremy's iron you can
[08:46] which is called Jeremy's iron you can find that on the website too
[08:55] [Music] you
[08:58] you [Music]
