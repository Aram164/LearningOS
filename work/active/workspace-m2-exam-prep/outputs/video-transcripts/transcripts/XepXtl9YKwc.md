---
video_id: XepXtl9YKwc
url: https://www.youtube.com/watch?v=XepXtl9YKwc
title: Maximum Likelihood, clearly explained!!!
channel: StatQuest with Josh Starmer
duration: 6:12
language: en
unit: L08
status: OK
---

[00:01] StatQuest,
[00:05] it's bad to the bone.
[00:09] it's bad to the bone. StatQuest, check it out.
[00:14] StatQuest, check it out. It's bad to the bone.
[00:20] Hello, and welcome to StatQuest.
[00:23] Hello, and welcome to StatQuest. StatQuest is brought to you by the
[00:24] StatQuest is brought to you by the friendly folks in the genetics
[00:26] friendly folks in the genetics department at the University of North
[00:28] department at the University of North Carolina at Chapel Hill.
[00:30] Carolina at Chapel Hill. Today, we're going to be talking about
[00:32] Today, we're going to be talking about maximum likelihood.
[00:34] maximum likelihood. Let's say we weighed a bunch of mice.
[00:38] Let's say we weighed a bunch of mice. The goal of maximum likelihood is to
[00:40] The goal of maximum likelihood is to find the optimal way to fit a
[00:42] find the optimal way to fit a distribution to the data.
[00:45] distribution to the data. There are lots of different types of
[00:47] There are lots of different types of distributions for different types of
[00:49] distributions for different types of data.
[00:50] data. Here's a normal distribution.
[00:53] Here's a normal distribution. Here's what an exponential distribution
[00:55] Here's what an exponential distribution looks like.
[00:56] looks like. And here's what a gamma distribution
[00:58] And here's what a gamma distribution looks like.
[01:00] looks like. And there are many more.
[01:02] And there are many more. The reason you want to fit a
[01:03] The reason you want to fit a distribution to your data is it can be
[01:05] distribution to your data is it can be easier to work with, and it is also more
[01:08] easier to work with, and it is also more general. It applies to every experiment
[01:11] general. It applies to every experiment of the same type.
[01:13] of the same type. In this case, we think the weights might
[01:15] In this case, we think the weights might be normally distributed.
[01:18] be normally distributed. That means we think it came from this
[01:20] That means we think it came from this type of distribution.
[01:22] type of distribution. Normally distributed means a number of
[01:24] Normally distributed means a number of things.
[01:26] things. First, we expect most of the
[01:28] First, we expect most of the measurements, for example, mouse
[01:30] measurements, for example, mouse weights, to be close to the mean or
[01:33] weights, to be close to the mean or average.
[01:35] average. And we see, lo and behold, in our data
[01:37] And we see, lo and behold, in our data set, most of the mice weigh close to the
[01:40] set, most of the mice weigh close to the average.
[01:42] average. We also expect the measurements to be
[01:44] We also expect the measurements to be relatively symmetrical around the mean.
[01:47] relatively symmetrical around the mean. Although the measurements are not
[01:49] Although the measurements are not perfectly symmetrical around the mean,
[01:51] perfectly symmetrical around the mean, they are not crazy skewed to one side,
[01:53] they are not crazy skewed to one side, either. This is pretty good.
[01:56] either. This is pretty good. Normal distributions come in all kinds
[01:58] Normal distributions come in all kinds of shapes and sizes.
[02:01] of shapes and sizes. They can be skinny,
[02:02] They can be skinny, medium, or large-boned.
[02:06] medium, or large-boned. Once we settle on the shape, we have to
[02:08] Once we settle on the shape, we have to figure out where to center the thing.
[02:11] figure out where to center the thing. Is one location better than another?
[02:15] Is one location better than another? Before we get too technical, let's just
[02:17] Before we get too technical, let's just pick any old normal distribution and see
[02:20] pick any old normal distribution and see how well it fits the data.
[02:22] how well it fits the data. This distribution says, "Most of the
[02:25] This distribution says, "Most of the values you measure should be near my
[02:27] values you measure should be near my average."
[02:29] average." The distribution's average is the black
[02:31] The distribution's average is the black dotted line. In this case, that's
[02:34] dotted line. In this case, that's different from the average of the actual
[02:36] different from the average of the actual measurements.
[02:38] measurements. Unfortunately,
[02:39] Unfortunately, most of the values we measured are far
[02:41] most of the values we measured are far from the distribution's average.
[02:44] from the distribution's average. According to a normal distribution with
[02:47] According to a normal distribution with a mean value over here,
[02:50] a mean value over here, the probability or likelihood of
[02:52] the probability or likelihood of observing all these weights is low.
[02:56] observing all these weights is low. What if we shifted the normal
[02:57] What if we shifted the normal distribution over so that its mean was
[03:00] distribution over so that its mean was the same as the average weight?
[03:03] the same as the average weight? According to a normal distribution with
[03:05] According to a normal distribution with a mean value here,
[03:08] a mean value here, the probability or likelihood of
[03:10] the probability or likelihood of observing these weights is relatively
[03:13] observing these weights is relatively high.
[03:15] high. If we kept shifting the normal
[03:16] If we kept shifting the normal distribution over,
[03:19] distribution over, then the probability or likelihood of
[03:22] then the probability or likelihood of observing these measurements would go
[03:24] observing these measurements would go down again.
[03:25] down again. We can plot the likelihood of observing
[03:28] We can plot the likelihood of observing the data over the location of the center
[03:31] the data over the location of the center of the distribution.
[03:34] of the distribution. We start on the left side and we
[03:35] We start on the left side and we calculate the likelihood of observing
[03:37] calculate the likelihood of observing the data, and then we shift the
[03:39] the data, and then we shift the distribution to the right and
[03:41] distribution to the right and recalculate. We just do this all the way
[03:44] recalculate. We just do this all the way down the data.
[03:45] down the data. Once we've tried all the possible
[03:47] Once we've tried all the possible locations we could center the normal
[03:49] locations we could center the normal distribution on, we want the location
[03:52] distribution on, we want the location that maximizes the likelihood of
[03:54] that maximizes the likelihood of observing the weights we measured.
[03:57] observing the weights we measured. This location for the mean maximizes the
[04:01] This location for the mean maximizes the likelihood of observing the weights we
[04:03] likelihood of observing the weights we measured.
[04:05] measured. Thus, it is the maximum likelihood
[04:07] Thus, it is the maximum likelihood estimate for the mean.
[04:10] estimate for the mean. In this case, we're specifically talking
[04:12] In this case, we're specifically talking about the mean of the distribution, not
[04:15] about the mean of the distribution, not the mean of the data. However, with a
[04:18] the mean of the data. However, with a normal distribution, those two things
[04:20] normal distribution, those two things are the same.
[04:22] are the same. Great. Now we have figured out the
[04:24] Great. Now we have figured out the maximum likelihood estimate for the
[04:26] maximum likelihood estimate for the mean.
[04:28] mean. Now we have to figure out the maximum
[04:29] Now we have to figure out the maximum likelihood estimate for the standard
[04:31] likelihood estimate for the standard deviation.
[04:33] deviation. Again, we can plot the likelihood of
[04:35] Again, we can plot the likelihood of observing the data over different values
[04:38] observing the data over different values for the standard deviation.
[04:40] for the standard deviation. Now we found the standard deviation that
[04:42] Now we found the standard deviation that maximizes the likelihood of observing
[04:45] maximizes the likelihood of observing the weights we measured.
[04:48] the weights we measured. This is the normal distribution that has
[04:50] This is the normal distribution that has been fit to the data by using the
[04:53] been fit to the data by using the maximum likelihood estimations for the
[04:55] maximum likelihood estimations for the mean and the standard deviation.
[04:58] mean and the standard deviation. Now, when someone says that they have
[05:01] Now, when someone says that they have the maximum likelihood estimates for the
[05:03] the maximum likelihood estimates for the mean or the standard deviation or for
[05:05] mean or the standard deviation or for something else,
[05:08] something else, you know that they found the value for
[05:10] you know that they found the value for the mean or the standard deviation or
[05:12] the mean or the standard deviation or for whatever that maximizes the
[05:15] for whatever that maximizes the likelihood that you observed the things
[05:17] likelihood that you observed the things that you observed.
[05:20] that you observed. Terminology alert.
[05:22] Terminology alert. In everyday conversation, probability
[05:25] In everyday conversation, probability and likelihood mean the same thing.
[05:28] and likelihood mean the same thing. However, in stats land, likelihood
[05:31] However, in stats land, likelihood specifically refers to this situation
[05:34] specifically refers to this situation we've covered here,
[05:36] we've covered here, where you are trying to find the optimal
[05:38] where you are trying to find the optimal value for the mean or standard deviation
[05:41] value for the mean or standard deviation for a distribution given a bunch of
[05:43] for a distribution given a bunch of observed measurements.
[05:45] observed measurements. This is how we fit a distribution to
[05:48] This is how we fit a distribution to data.
[05:49] data. Hooray! We've made it to the end of
[05:52] Hooray! We've made it to the end of another exciting StatQuest.
[05:54] another exciting StatQuest. If you like this StatQuest and want to
[05:56] If you like this StatQuest and want to see more like it, please subscribe. It's
[05:59] see more like it, please subscribe. It's super easy. Just click the little button
[06:01] super easy. Just click the little button below.
[06:02] below. And if you have any suggestions for
[06:04] And if you have any suggestions for other StatQuests that I could do, put
[06:07] other StatQuests that I could do, put them in the comments. All right, until
[06:09] them in the comments. All right, until next time, quest on.
