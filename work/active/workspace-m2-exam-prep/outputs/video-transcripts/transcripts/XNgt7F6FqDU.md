---
video_id: XNgt7F6FqDU
url: https://www.youtube.com/watch?v=XNgt7F6FqDU
title: The standard error, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 11:43
language: en
unit: L09
status: OK
---

[00:00] Stat Quest Stat Quest
[00:05] Stat Quest Stat Quest
[00:07] Stat Quest Hello and welcome to Stat Quest. This
[00:10] Hello and welcome to Stat Quest. This time, we're going to talk about standard
[00:12] time, we're going to talk about standard errors and we're also going to have a
[00:14] errors and we're also going to have a bootstrapping bonus.
[00:16] bootstrapping bonus. We'll start by talking about error bars,
[00:18] We'll start by talking about error bars, which are very closely related to
[00:20] which are very closely related to standard errors.
[00:22] standard errors. For example, you might collect
[00:24] For example, you might collect measurements from three samples labeled
[00:27] measurements from three samples labeled A, B, and C and plot them on a scatter
[00:30] A, B, and C and plot them on a scatter plot just like we see here.
[00:34] You could then calculate the means for the three data sets and we've
[00:37] the three data sets and we've illustrated those here with three green
[00:40] illustrated those here with three green horizontal bars approximately halfway up
[00:43] horizontal bars approximately halfway up the clusters of data points.
[00:47] the clusters of data points. After that, we could calculate the
[00:49] After that, we could calculate the standard deviations and add those to the
[00:51] standard deviations and add those to the graph and we've shown those here with
[00:53] graph and we've shown those here with red error bars.
[00:56] red error bars. In manuscripts and presentations, people
[00:58] In manuscripts and presentations, people often don't display the original data,
[01:00] often don't display the original data, but instead just show the mean and the
[01:02] but instead just show the mean and the standard deviation in what's called a
[01:04] standard deviation in what's called a dynamite plot because each column in the
[01:07] dynamite plot because each column in the plot looks like it's the igniter for a
[01:09] plot looks like it's the igniter for a stick of dynamite.
[01:13] There are three common types of error bars.
[01:16] bars. The first type are standard deviations,
[01:18] The first type are standard deviations, which we just saw and I'm sure you're
[01:20] which we just saw and I'm sure you're all familiar with.
[01:22] all familiar with. These tell you how the data are
[01:23] These tell you how the data are distributed around the mean.
[01:25] distributed around the mean. Big standard deviations tell you that
[01:27] Big standard deviations tell you that some of the data points were pretty far
[01:29] some of the data points were pretty far from the mean.
[01:30] from the mean. In most cases, you want to use standard
[01:32] In most cases, you want to use standard deviations in your graphs since it tells
[01:34] deviations in your graphs since it tells us about your data, the data points that
[01:37] us about your data, the data points that you collected yourself.
[01:40] you collected yourself. The second type of error bar comes from
[01:42] The second type of error bar comes from standard errors.
[01:43] standard errors. These tell you how the mean is
[01:45] These tell you how the mean is distributed, not just the data, but the
[01:48] distributed, not just the data, but the means, which sounds crazy, but it'll
[01:50] means, which sounds crazy, but it'll become clear once I draw some pictures.
[01:54] become clear once I draw some pictures. The third common type of error bar are
[01:57] The third common type of error bar are confidence intervals, and these are
[01:58] confidence intervals, and these are related to standard errors. Confidence
[02:01] related to standard errors. Confidence intervals will be explained more in a
[02:03] intervals will be explained more in a future StatQuest.
[02:05] future StatQuest. Since this StatQuest is all about
[02:07] Since this StatQuest is all about standard errors, that's what we're going
[02:09] standard errors, that's what we're going to talk about.
[02:12] to talk about. Let's start by considering a normal
[02:14] Let's start by considering a normal distribution.
[02:15] distribution. In this case, we can imagine that we
[02:17] In this case, we can imagine that we weighed a lot of mice and plotted the
[02:19] weighed a lot of mice and plotted the distribution of differences from the
[02:21] distribution of differences from the mean.
[02:23] mean. The Y axis is the proportion of the mice
[02:26] The Y axis is the proportion of the mice that we weighed, and the X axis is the
[02:29] that we weighed, and the X axis is the difference from the mean.
[02:31] difference from the mean. Most of the mice had weights close to
[02:33] Most of the mice had weights close to the average.
[02:35] the average. A few of the mice weighed much less than
[02:37] A few of the mice weighed much less than the average mouse.
[02:39] the average mouse. And a few other mice weighed much more
[02:41] And a few other mice weighed much more than the average mouse.
[02:44] than the average mouse. Usually, you can't afford to measure the
[02:46] Usually, you can't afford to measure the weight of all the mice, so you just take
[02:48] weight of all the mice, so you just take a sample.
[02:50] a sample. In this example, we'll just assume we
[02:52] In this example, we'll just assume we took five measurements from the
[02:53] took five measurements from the population rather than measuring all the
[02:56] population rather than measuring all the mice.
[02:57] mice. Since most of the mice have weights
[03:00] Since most of the mice have weights close to the average,
[03:01] close to the average, most of our samples are going to be
[03:03] most of our samples are going to be close to zero.
[03:06] close to zero. Now, just like we always do, we can
[03:08] Now, just like we always do, we can calculate the mean and standard
[03:09] calculate the mean and standard deviation from our sample.
[03:12] deviation from our sample. In this case,
[03:13] In this case, the mean of our sample is minus point
[03:16] the mean of our sample is minus point two, and the standard deviation is
[03:18] two, and the standard deviation is 1.923.
[03:20] 1.923. And we can plot the mean and standard
[03:22] And we can plot the mean and standard deviation on our graph as the mean plus
[03:26] deviation on our graph as the mean plus or minus the standard deviation around
[03:28] or minus the standard deviation around the mean.
[03:29] the mean. And for all you StatQuesters out there,
[03:32] And for all you StatQuesters out there, here's a rule of thumb. Remember that
[03:34] here's a rule of thumb. Remember that one standard deviation on each side of
[03:36] one standard deviation on each side of the mean is supposed to cover about 68%
[03:39] the mean is supposed to cover about 68% of the data.
[03:40] of the data. Two standard deviations on each side of
[03:42] Two standard deviations on each side of the mean is supposed to cover about 95%
[03:44] the mean is supposed to cover about 95% of the data.
[03:46] of the data. This will come in handy later.
[03:49] The mean is now a lighter color because we're going to take additional samples
[03:53] we're going to take additional samples and overlay additional means and
[03:55] and overlay additional means and standard deviations on this same graph.
[03:58] standard deviations on this same graph. Here, we've taken another five
[04:00] Here, we've taken another five measurements.
[04:01] measurements. And from those five measurements, we've
[04:03] And from those five measurements, we've calculated the mean and the standard
[04:05] calculated the mean and the standard deviation.
[04:07] deviation. And here we've plotted that mean plus or
[04:09] And here we've plotted that mean plus or minus one standard deviation on each
[04:11] minus one standard deviation on each side.
[04:12] side. And now we take another five
[04:14] And now we take another five measurements.
[04:15] measurements. This is the first sample where one of
[04:17] This is the first sample where one of the measurements is relatively extreme.
[04:19] the measurements is relatively extreme. However, that one measurement doesn't
[04:22] However, that one measurement doesn't sway the mean that far from zero.
[04:27] That is to say, the means are relatively close to each other compared to the raw
[04:31] close to each other compared to the raw data.
[04:32] data. This is because for a mean to be far
[04:35] This is because for a mean to be far from the middle, most, if not all of the
[04:37] from the middle, most, if not all of the raw data points, would have to be in a
[04:39] raw data points, would have to be in a single cluster that is far away from the
[04:42] single cluster that is far away from the middle.
[04:43] middle. For example, the sample of purple points
[04:46] For example, the sample of purple points all form a cluster that are far from the
[04:47] all form a cluster that are far from the middle.
[04:48] middle. This could happen, but very rarely.
[04:53] This could happen, but very rarely. What's much more likely is to have a
[04:55] What's much more likely is to have a sample where most of the points are
[04:57] sample where most of the points are close to zero and only one or two are
[05:00] close to zero and only one or two are far away.
[05:02] far away. So far, we've shown that you can
[05:04] So far, we've shown that you can calculate the standard deviations for
[05:06] calculate the standard deviations for each sample.
[05:08] each sample. But now that we have three means, we can
[05:11] But now that we have three means, we can also calculate the standard deviation of
[05:13] also calculate the standard deviation of those means.
[05:15] those means. Because one standard deviation will
[05:17] Because one standard deviation will cover 68% of the values, and two will
[05:19] cover 68% of the values, and two will cover 95% of the values, the standard
[05:22] cover 95% of the values, the standard deviation of the means won't be as wide
[05:25] deviation of the means won't be as wide as the standard deviations of the data.
[05:28] as the standard deviations of the data. Here, we've plotted the mean of the
[05:30] Here, we've plotted the mean of the means plus or minus one standard
[05:32] means plus or minus one standard deviation of the means.
[05:34] deviation of the means. Notice that this standard deviation is
[05:37] Notice that this standard deviation is much smaller than the standard
[05:38] much smaller than the standard deviations we got from the individual
[05:40] deviations we got from the individual samples.
[05:43] samples. The standard deviation of the mean is
[05:45] The standard deviation of the mean is called the standard error of the mean,
[05:47] called the standard error of the mean, or more simply the standard error.
[05:50] or more simply the standard error. The standard error gives us a sense of
[05:52] The standard error gives us a sense of how much variation we can expect in our
[05:55] how much variation we can expect in our means if we took a bunch of independent
[05:57] means if we took a bunch of independent five measurement samples.
[05:59] five measurement samples. So, to review, this is how we calculate
[06:02] So, to review, this is how we calculate the standard error of the mean.
[06:05] the standard error of the mean. First, you take a bunch of samples, each
[06:08] First, you take a bunch of samples, each with the same number of measurements, or
[06:10] with the same number of measurements, or n.
[06:11] n. In this case, n = 5.
[06:15] In this case, n = 5. The second step is to calculate the mean
[06:17] The second step is to calculate the mean for each sample.
[06:18] for each sample. Here, we've calculated the mean and
[06:20] Here, we've calculated the mean and standard deviation for each sample,
[06:22] standard deviation for each sample, but for the standard error, all we need
[06:24] but for the standard error, all we need to do is calculate the mean.
[06:28] Once we've calculated the means for each sample, we can calculate the standard
[06:32] sample, we can calculate the standard deviation of the means. In this case,
[06:35] deviation of the means. In this case, the standard error = 0.86.
[06:40] Here, we notice that the standard error is much less than the standard
[06:44] is much less than the standard deviations because the means aren't as
[06:46] deviations because the means aren't as widely dispersed as the raw data.
[06:50] widely dispersed as the raw data. We've shown how to calculate the
[06:51] We've shown how to calculate the standard error of the mean, but there
[06:53] standard error of the mean, but there are other standard errors.
[06:56] are other standard errors. For example, we can also take the
[06:58] For example, we can also take the standard deviation of the standard
[07:00] standard deviation of the standard deviations.
[07:01] deviations. This is called the standard error of the
[07:03] This is called the standard error of the standard deviations, which I guess is to
[07:05] standard deviations, which I guess is to avoid a tongue twister.
[07:07] avoid a tongue twister. It tells us how the standard deviations
[07:09] It tells us how the standard deviations of multiple samples are dispersed.
[07:12] of multiple samples are dispersed. You can calculate the standard deviation
[07:13] You can calculate the standard deviation of any statistic, for example, the
[07:16] of any statistic, for example, the median, the mode, percentiles, or
[07:18] median, the mode, percentiles, or anything. Anything that you can
[07:20] anything. Anything that you can calculate for multiple samples.
[07:22] calculate for multiple samples. You just calculate the standard
[07:23] You just calculate the standard deviation, and then you have the
[07:25] deviation, and then you have the standard error of that. So, if we
[07:27] standard error of that. So, if we calculated many medians,
[07:30] calculated many medians, we could calculate the standard
[07:31] we could calculate the standard deviation of those medians, and we'd
[07:33] deviation of those medians, and we'd have the standard error of those
[07:35] have the standard error of those medians.
[07:37] medians. To summarize everything we've talked
[07:38] To summarize everything we've talked about so far,
[07:40] about so far, know that the standard error is just the
[07:42] know that the standard error is just the standard deviation of multiple means
[07:46] standard deviation of multiple means taken from the same population. So, if
[07:48] taken from the same population. So, if there's a population and we can take a
[07:50] there's a population and we can take a bunch of different samples from it, all
[07:53] bunch of different samples from it, all we have to do to get the standard error
[07:55] we have to do to get the standard error is to calculate the standard deviation
[07:57] is to calculate the standard deviation of the means of each sample.
[08:00] of the means of each sample. Well, at this point, you might be
[08:02] Well, at this point, you might be wondering if we can calculate standard
[08:03] wondering if we can calculate standard errors without spending a lot of time
[08:05] errors without spending a lot of time and money on doing the same experiment a
[08:08] and money on doing the same experiment a bunch of times.
[08:10] bunch of times. The good news is the answer is yes.
[08:13] The good news is the answer is yes. In rare cases, there's a formula you can
[08:15] In rare cases, there's a formula you can use to estimate it. The standard error
[08:17] use to estimate it. The standard error of the mean is one. The formula for that
[08:19] of the mean is one. The formula for that is very simple. It's just the standard
[08:21] is very simple. It's just the standard deviation divided by the square root of
[08:24] deviation divided by the square root of the sample size.
[08:25] the sample size. However, there aren't many other cases.
[08:28] However, there aren't many other cases. The good news, again,
[08:31] The good news, again, is that we can use something called
[08:32] is that we can use something called bootstrapping for everything else. Every
[08:34] bootstrapping for everything else. Every time we don't have a simple formula, we
[08:37] time we don't have a simple formula, we can bootstrap it. The nice thing about
[08:39] can bootstrap it. The nice thing about bootstrapping is it's very simple
[08:41] bootstrapping is it's very simple conceptually, and it's easy to make a
[08:43] conceptually, and it's easy to make a computer do this work.
[08:46] computer do this work. Here's a bootstrapping example. Just
[08:48] Here's a bootstrapping example. Just like before, we have an experiment where
[08:50] like before, we have an experiment where we took five measurements.
[08:53] we took five measurements. As an aside, usually for bootstrapping,
[08:55] As an aside, usually for bootstrapping, it's good to have 10 or more
[08:57] it's good to have 10 or more measurements in a single experiment.
[09:00] measurements in a single experiment. Now, we bootstrap our data with the
[09:03] Now, we bootstrap our data with the following steps.
[09:06] following steps. First, we pick a random measurement from
[09:08] First, we pick a random measurement from the sample that we just took.
[09:10] the sample that we just took. This random measurement isn't a new
[09:12] This random measurement isn't a new measurement that we haven't taken
[09:14] measurement that we haven't taken before. It's not a new number that we
[09:16] before. It's not a new number that we haven't seen. It's part of the sample
[09:17] haven't seen. It's part of the sample that we already have.
[09:20] that we already have. Now, we just write that value down.
[09:23] Now, we just write that value down. In this case, it's 1.43.
[09:27] In this case, it's 1.43. In step three, we just go back to step
[09:29] In step three, we just go back to step one and pick a new random measurement
[09:32] one and pick a new random measurement and write that value down, and we do
[09:34] and write that value down, and we do that five times.
[09:37] that five times. Our second measurement is minus 1.38.
[09:41] Our second measurement is minus 1.38. The third measurement is minus 3.11.
[09:46] The third measurement is minus 3.11. Our fourth measurement is 1.43.
[09:51] Our fourth measurement is 1.43. We've already picked that measurement
[09:52] We've already picked that measurement before, but that's okay.
[09:55] before, but that's okay. When you're bootstrapping, you just pick
[09:57] When you're bootstrapping, you just pick five measurements from your sample, and
[10:00] five measurements from your sample, and it doesn't matter if you've picked the
[10:01] it doesn't matter if you've picked the same one before.
[10:04] same one before. Our last measurement is minus 0.10.
[10:10] Step four in bootstrapping is to calculate the mean, median, mode, or
[10:15] calculate the mean, median, mode, or whatever the statistic it is we're
[10:16] whatever the statistic it is we're interested in understanding the standard
[10:18] interested in understanding the standard error of, and we calculate that with our
[10:21] error of, and we calculate that with our sample.
[10:22] sample. In this case, we're interested in the
[10:24] In this case, we're interested in the standard error of the mean.
[10:26] standard error of the mean. So, all we do is calculate the mean from
[10:28] So, all we do is calculate the mean from our new bootstrap sample.
[10:30] our new bootstrap sample. The fifth step is to go all the way back
[10:33] The fifth step is to go all the way back to the beginning, step one, and repeat
[10:35] to the beginning, step one, and repeat that until you have a lot of means or
[10:38] that until you have a lot of means or medians or whatever you're interested in
[10:40] medians or whatever you're interested in calculating the standard error of.
[10:43] calculating the standard error of. The sixth and final step in the
[10:45] The sixth and final step in the bootstrapping procedure is to simply
[10:47] bootstrapping procedure is to simply calculate the standard deviation of all
[10:50] calculate the standard deviation of all the means that we generated in steps one
[10:52] the means that we generated in steps one through five.
[10:54] through five. That's all there is to it. In this case,
[10:56] That's all there is to it. In this case, we calculated the standard error of the
[10:58] we calculated the standard error of the mean, and we've plotted it as a black
[11:00] mean, and we've plotted it as a black line in the graph.
[11:02] line in the graph. So, if there's no fancy formula to help
[11:05] So, if there's no fancy formula to help us calculate the standard error, we can
[11:07] us calculate the standard error, we can do it ourselves from scratch. We can
[11:09] do it ourselves from scratch. We can just use bootstrapping and get the job
[11:11] just use bootstrapping and get the job done.
[11:13] done. And that's it. In this Stat Quest, we
[11:15] And that's it. In this Stat Quest, we learned that the standard error is a
[11:17] learned that the standard error is a measure of how we might expect the means
[11:21] measure of how we might expect the means from many different samples to vary from
[11:23] from many different samples to vary from one sample to another.
[11:26] one sample to another. We also learned that if we don't have a
[11:27] We also learned that if we don't have a fancy formula for calculating the
[11:29] fancy formula for calculating the standard error, we can do it ourselves
[11:31] standard error, we can do it ourselves using bootstrapping.
[11:33] using bootstrapping. Okay, so tune in next time and we'll
[11:36] Okay, so tune in next time and we'll talk about how to use bootstrapping to
[11:38] talk about how to use bootstrapping to calculate confidence intervals, and
[11:40] calculate confidence intervals, and that's when things get really cool.
