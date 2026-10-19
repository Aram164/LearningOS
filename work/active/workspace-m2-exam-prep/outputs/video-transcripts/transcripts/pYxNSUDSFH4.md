---
video_id: pYxNSUDSFH4
url: https://www.youtube.com/watch?v=pYxNSUDSFH4
title: In Statistics, Probability is not Likelihood.
channel: StatQuest with Josh Starmer
duration: 5:01
language: en
unit: L08
status: OK
---

[00:00] StatQuest makes me feel so happy,
[00:05] StatQuest makes me feel so happy, so very, very, very, very, very, very,
[00:08] so very, very, very, very, very, very, very happy.
[00:11] very happy. StatQuest.
[00:12] StatQuest. Hello, I'm Josh Starmer and welcome to
[00:15] Hello, I'm Josh Starmer and welcome to StatQuest. Today we're going to be
[00:17] StatQuest. Today we're going to be talking about the difference between
[00:18] talking about the difference between probability and likelihood. These are
[00:21] probability and likelihood. These are two closely related concepts that are
[00:22] two closely related concepts that are very easy to get confused. Even I mix
[00:25] very easy to get confused. Even I mix them up from time to time. So enough of
[00:27] them up from time to time. So enough of this gibber jabber, let's get down to
[00:29] this gibber jabber, let's get down to it.
[00:30] it. For me, the easiest way to understand
[00:33] For me, the easiest way to understand the difference between probability and
[00:34] the difference between probability and likelihood is to just see it in
[00:36] likelihood is to just see it in pictures.
[00:38] pictures. So let's start by looking at probability
[00:40] So let's start by looking at probability with respect to a normal distribution,
[00:42] with respect to a normal distribution, keeping in mind that this concept
[00:44] keeping in mind that this concept applies to all continuous distributions.
[00:47] applies to all continuous distributions. In this case, let's imagine that this is
[00:50] In this case, let's imagine that this is a distribution of mouse weights.
[00:53] a distribution of mouse weights. It has a mean of 32 g
[00:56] It has a mean of 32 g and a standard deviation of 2.5.
[01:00] and a standard deviation of 2.5. On the low end, we have 24 g.
[01:04] On the low end, we have 24 g. And on the high end, we have 40 g.
[01:08] And on the high end, we have 40 g. The probability that we will weigh a
[01:10] The probability that we will weigh a randomly selected mouse between 32 and
[01:13] randomly selected mouse between 32 and 34 g
[01:15] 34 g is the area under the curve between 32
[01:18] is the area under the curve between 32 and 34 g.
[01:21] and 34 g. In this case, the area under the curve
[01:23] In this case, the area under the curve equals 0.29,
[01:25] equals 0.29, meaning there's a 29% chance a randomly
[01:28] meaning there's a 29% chance a randomly selected mouse will weigh between 32 and
[01:31] selected mouse will weigh between 32 and 34 g.
[01:33] 34 g. Mathematically, we say this with the
[01:35] Mathematically, we say this with the following notation.
[01:38] following notation. The probability of weighing a mouse
[01:40] The probability of weighing a mouse between 32 and 34 g
[01:43] between 32 and 34 g given
[01:45] given the mean of the distribution is 32 and
[01:48] the mean of the distribution is 32 and the standard deviation is 2.5.
[01:52] the standard deviation is 2.5. And all this equals 0.29.
[01:56] And all this equals 0.29. This is the part of the equation we
[01:57] This is the part of the equation we change if we are interested in different
[01:59] change if we are interested in different mouse weights.
[02:02] mouse weights. For example, if we wanted to know the
[02:04] For example, if we wanted to know the probability of a mouse weighing more
[02:06] probability of a mouse weighing more than 34 g,
[02:09] than 34 g, we would change the bit on the left side
[02:11] we would change the bit on the left side to reflect this.
[02:14] to reflect this. The right side, which defines the shape
[02:16] The right side, which defines the shape and location of the distribution, stays
[02:19] and location of the distribution, stays the same.
[02:21] the same. So, when we talk about probabilities, we
[02:23] So, when we talk about probabilities, we are talking about
[02:25] are talking about a distribution that's described by the
[02:27] a distribution that's described by the right side of this equation,
[02:30] right side of this equation, and the area under the curve that is
[02:32] and the area under the curve that is described on the left side.
[02:36] described on the left side. Using the same distribution,
[02:38] Using the same distribution, we can change the left side to get a new
[02:41] we can change the left side to get a new probability.
[02:43] probability. Bam!
[02:46] Bam! Now that we have probability worked out,
[02:48] Now that we have probability worked out, let's talk about likelihood.
[02:51] let's talk about likelihood. To talk about likelihood, you assume
[02:54] To talk about likelihood, you assume that you have already weighed your
[02:55] that you have already weighed your mouse, or mice, if you've weighed more
[02:57] mouse, or mice, if you've weighed more than one.
[03:00] than one. So, here's our mouse. It weighs 34 g.
[03:04] So, here's our mouse. It weighs 34 g. The likelihood of weighing a 34 g mouse
[03:07] The likelihood of weighing a 34 g mouse is
[03:09] is this point on the curve,
[03:11] this point on the curve, and that value is 0.12.
[03:15] Mathematically, we say this with the following notation.
[03:20] following notation. The likelihood of a distribution with
[03:22] The likelihood of a distribution with mean equals 32 and the standard
[03:24] mean equals 32 and the standard deviation equals 2.5,
[03:27] deviation equals 2.5, given
[03:29] given we weighed a 34 g mouse,
[03:32] we weighed a 34 g mouse, and all that equals 0.12.
[03:36] If we shifted the distribution over so
[03:39] If we shifted the distribution over so that the mean was 34 g,
[03:42] that the mean was 34 g, the new likelihood would be 0.21.
[03:47] So, with likelihoods, the measurements
[03:50] So, with likelihoods, the measurements on the right side are fixed,
[03:53] on the right side are fixed, And we modify the shape and location of
[03:55] And we modify the shape and location of the distribution with the left side.
[03:59] the distribution with the left side. Double bam.
[04:01] Double bam. In summary,
[04:03] In summary, probabilities are the areas under a
[04:05] probabilities are the areas under a fixed distribution.
[04:08] fixed distribution. And mathematically, we have the
[04:10] And mathematically, we have the probability of data given a
[04:12] probability of data given a distribution.
[04:15] distribution. Likelihoods are the Y axis values for
[04:18] Likelihoods are the Y axis values for fixed data points with distributions
[04:20] fixed data points with distributions that can be moved.
[04:23] that can be moved. Mathematically, this is written as the
[04:25] Mathematically, this is written as the likelihood of a distribution given data.
[04:30] likelihood of a distribution given data. If you want to see the actual equations,
[04:32] If you want to see the actual equations, check out the stat quest that derives
[04:34] check out the stat quest that derives the maximum likelihood estimator for the
[04:36] the maximum likelihood estimator for the exponential distribution.
[04:39] exponential distribution. Hooray! We've made it to the end of
[04:41] Hooray! We've made it to the end of another exciting stat quest.
[04:44] another exciting stat quest. If you like this stat quest and want to
[04:45] If you like this stat quest and want to see more of them, please subscribe. And
[04:48] see more of them, please subscribe. And if you want to support stat quest, well,
[04:51] if you want to support stat quest, well, consider buying one or two of my
[04:52] consider buying one or two of my original songs. The link to my bandcamp
[04:55] original songs. The link to my bandcamp page is down below in the comments. All
[04:57] page is down below in the comments. All right, until next time, quest on.
