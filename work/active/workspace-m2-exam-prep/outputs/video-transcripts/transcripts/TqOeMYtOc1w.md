---
video_id: TqOeMYtOc1w
url: https://www.youtube.com/watch?v=TqOeMYtOc1w
title: Confidence Intervals, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 6:41
language: en
unit: L09
status: OK
---

[00:00] stat Quest stat
[00:05] Quest stat Quest stat Quest hello and welcome to
[00:10] Quest stat Quest hello and welcome to stat Quest stat Quest is brought to you
[00:12] stat Quest stat Quest is brought to you by the friendly folks in the genetics
[00:14] by the friendly folks in the genetics department at the University of North
[00:16] department at the University of North Carolina at Chapel
[00:18] Carolina at Chapel Hill today's stat Quest is all about
[00:21] Hill today's stat Quest is all about confidence
[00:24] confidence intervals you may have seen or heard of
[00:27] intervals you may have seen or heard of confidence intervals before however if
[00:29] confidence intervals before however if you're not not very confident about them
[00:31] you're not not very confident about them then you're not alone many people
[00:34] then you're not alone many people misunderstand confidence intervals but
[00:36] misunderstand confidence intervals but that's only because they didn't learn
[00:38] that's only because they didn't learn about bootstrapping first now just to
[00:41] about bootstrapping first now just to clarify there are lots of ways to
[00:43] clarify there are lots of ways to calculate confidence intervals and
[00:45] calculate confidence intervals and bootstrapping is just one of them but
[00:47] bootstrapping is just one of them but for me it makes it easiest to understand
[00:50] for me it makes it easiest to understand but when you see confidence intervals
[00:52] but when you see confidence intervals out there in the wild you're likely to
[00:54] out there in the wild you're likely to see a different way to calculate
[00:56] see a different way to calculate them now even though we just did
[00:59] them now even though we just did bootstrapping your brain might be a
[01:00] bootstrapping your brain might be a little cloudy and you may have forgotten
[01:02] little cloudy and you may have forgotten what it was all about my brain's like
[01:04] what it was all about my brain's like that so I totally understand that's why
[01:06] that so I totally understand that's why we're going to do a little bootstrap
[01:09] we're going to do a little bootstrap refresher imagine we weighed a bunch of
[01:12] refresher imagine we weighed a bunch of female mice in this case we weighed 12
[01:15] female mice in this case we weighed 12 of them we didn't weigh every single
[01:18] of them we didn't weigh every single female Mouse on the planet just
[01:21] female Mouse on the planet just 12 now we can take these 12 measurements
[01:25] 12 now we can take these 12 measurements and we can use them to calculate the
[01:26] and we can use them to calculate the sample mean now the sample mean is not
[01:29] sample mean now the sample mean is not the mean for all mice in the entire
[01:32] the mean for all mice in the entire planet it's just the mean of the mice
[01:34] planet it's just the mean of the mice that we sampled however we can use
[01:37] that we sampled however we can use bootstrapping and the data that we have
[01:39] bootstrapping and the data that we have here to determine what values would be
[01:42] here to determine what values would be reasonable for the global worldwide mean
[01:46] reasonable for the global worldwide mean of all female mice on the
[01:49] of all female mice on the planet now that we've calculated the
[01:51] planet now that we've calculated the sample mean we can bootstrap the
[01:54] sample mean we can bootstrap the sample to bootstrap the sample we
[01:57] sample to bootstrap the sample we randomly select 12 weights from the
[01:59] randomly select 12 weights from the original sample and duplicates are
[02:03] original sample and duplicates are okay here's an example of a bootstrapped
[02:07] okay here's an example of a bootstrapped sample we can see that this measurement
[02:10] sample we can see that this measurement on the far left was sampled twice in our
[02:13] on the far left was sampled twice in our bootstrap
[02:15] bootstrap sample and the measurement to its right
[02:18] sample and the measurement to its right wasn't included in our bootstrap sample
[02:20] wasn't included in our bootstrap sample this is called sampling with
[02:23] this is called sampling with replacement now we calculate the mean of
[02:26] replacement now we calculate the mean of the random
[02:28] the random sample after we've calculated the mean
[02:30] sample after we've calculated the mean of our first random sample all we have
[02:33] of our first random sample all we have to do is repeat steps one and two until
[02:36] to do is repeat steps one and two until we've calculated a lot of means
[02:38] we've calculated a lot of means sometimes more than
[02:40] sometimes more than 10,000 and here's what it looks like
[02:42] 10,000 and here's what it looks like when we've calculated a lot of means
[02:45] when we've calculated a lot of means it's maybe a little fewer than 10,000
[02:47] it's maybe a little fewer than 10,000 but you get the
[02:49] but you get the idea anyway that's all there is to
[02:51] idea anyway that's all there is to bootstrapping now let's talk about
[02:53] bootstrapping now let's talk about confidence
[02:55] confidence intervals usually when you see a
[02:57] intervals usually when you see a confidence interval out in the wild it's
[02:59] confidence interval out in the wild it's called a 95% confidence
[03:02] called a 95% confidence interval a 95% confidence interval is
[03:05] interval a 95% confidence interval is just an interval that covers 95% of the
[03:08] just an interval that covers 95% of the means so here we have a black bar that
[03:11] means so here we have a black bar that spans 95% of the bootstrapped means that
[03:14] spans 95% of the bootstrapped means that we just
[03:16] we just calculated that's it that's all a
[03:18] calculated that's it that's all a confidence interval is nothing more
[03:21] confidence interval is nothing more nothing
[03:22] nothing less can you guess what a 99% confidence
[03:25] less can you guess what a 99% confidence interval
[03:27] interval is here's a hint it's wider than a 95%
[03:31] is here's a hint it's wider than a 95% confidence interval all right I'll tell
[03:34] confidence interval all right I'll tell you it's just an interval that covers
[03:36] you it's just an interval that covers 99% of the means that you calculated
[03:39] 99% of the means that you calculated when you bootstrapped the
[03:41] when you bootstrapped the sample now that we know what confidence
[03:43] sample now that we know what confidence intervals are we might ask why are they
[03:47] intervals are we might ask why are they useful well I think confidence intervals
[03:49] useful well I think confidence intervals are useful because they are statistical
[03:51] are useful because they are statistical tests performed
[03:53] tests performed visually because the interval covers 95%
[03:57] visually because the interval covers 95% of the means we know that anything
[03:59] of the means we know that anything outside of occurs less than 5% of the
[04:01] outside of occurs less than 5% of the time that is to say the P value of
[04:04] time that is to say the P value of anything outside of the confidence
[04:06] anything outside of the confidence interval is less than 05 and thus
[04:09] interval is less than 05 and thus significantly
[04:11] significantly different here's an example of a visual
[04:14] different here's an example of a visual statistical test you'll remember we
[04:17] statistical test you'll remember we originally calculated the sample mean
[04:20] originally calculated the sample mean the sample mean is an estimate of the
[04:21] the sample mean is an estimate of the true mean for all female
[04:24] true mean for all female mice well with our confidence interval
[04:28] mice well with our confidence interval we can figure out what the the P value
[04:30] we can figure out what the the P value is that the true mean of all female mice
[04:33] is that the true mean of all female mice not just of our sample is less than
[04:36] not just of our sample is less than 20 to perform that test we draw our
[04:39] 20 to perform that test we draw our confidence interval which we know
[04:41] confidence interval which we know because of bootstrapping or some formula
[04:44] because of bootstrapping or some formula that we
[04:45] that we use we can see that the area left of 20
[04:49] use we can see that the area left of 20 so values less than 20 are outside of
[04:52] so values less than 20 are outside of our 95% confidence
[04:54] our 95% confidence interval because the highlighted region
[04:56] interval because the highlighted region is outside of the 95% confidence
[04:59] is outside of the 95% confidence interval which contains 95% of the means
[05:02] interval which contains 95% of the means we know that the probability that the
[05:04] we know that the probability that the true mean is in this area has to be less
[05:07] true mean is in this area has to be less than
[05:08] than 05 thus the P value is less than
[05:12] 05 thus the P value is less than 0.05 this is unlikely and because of
[05:15] 0.05 this is unlikely and because of this we can say there's a statistically
[05:18] this we can say there's a statistically significant difference between the true
[05:20] significant difference between the true mean and any value less than
[05:24] mean and any value less than 20 here's another example of a visual
[05:28] 20 here's another example of a visual statistical test in this case we're
[05:30] statistical test in this case we're going to compare two
[05:32] going to compare two samples here we've weighed female
[05:35] samples here we've weighed female mice and now we have a sample of male
[05:38] mice and now we have a sample of male mice we've already done the
[05:40] mice we've already done the bootstrapping on that sample and here in
[05:42] bootstrapping on that sample and here in the figure we just show the means from
[05:44] the figure we just show the means from that
[05:45] that bootstrapping because the 95% confidence
[05:48] bootstrapping because the 95% confidence intervals do not overlap we know that
[05:51] intervals do not overlap we know that there is a statistically significant
[05:53] there is a statistically significant difference in the weights of female and
[05:55] difference in the weights of female and male mice that is to say we know that
[05:58] male mice that is to say we know that the P value is less than 005 just by
[06:01] the P value is less than 005 just by looking at the
[06:03] looking at the picture there is one caveat to that and
[06:06] picture there is one caveat to that and to illustrate that caveat I've shifted
[06:09] to illustrate that caveat I've shifted the means a little bit over to the left
[06:11] the means a little bit over to the left so that now the confidence intervals
[06:14] so that now the confidence intervals overlap if the confidence intervals
[06:16] overlap if the confidence intervals overlap there's still a chance that the
[06:18] overlap there's still a chance that the means are significantly different from
[06:20] means are significantly different from each other so in this case you still
[06:23] each other so in this case you still have to do the T Test but when the
[06:26] have to do the T Test but when the confidence intervals do not overlap then
[06:29] confidence intervals do not overlap then you can rest assured that there's a
[06:31] you can rest assured that there's a statistically significant difference
[06:33] statistically significant difference between those two
[06:35] between those two means that's all there is to it tune in
[06:37] means that's all there is to it tune in next time for another stack Quest
