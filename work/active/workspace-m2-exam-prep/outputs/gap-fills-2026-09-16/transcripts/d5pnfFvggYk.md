---
video_id: d5pnfFvggYk
url: https://www.youtube.com/watch?v=d5pnfFvggYk
title: L18.3 The Chebyshev Inequality
channel: MIT OpenCourseWare
duration: 5:56
language: en
unit: L06
status: OK
---

[00:00] Mathematically speaking, the Chebyshev inequality is just a
[00:03] simple application of the Markov inequality.
[00:06] However, it contains a somewhat different message.
[00:09] Consider a random variable that has a
[00:11] certain mean and variance.
[00:13] What the Chebyshev inequality says is that if the variance
[00:16] is small, then the random variable is unlikely to fall
[00:21] too far off from the mean.
[00:23] If the variance is small, we have little randomness.
[00:27] And so X cannot be too far from the mean.
[00:31] In more precise terms, we have the following inequality.
[00:35] The probability that the distance from the mean is
[00:37] larger than or equal to a certain number is, at most,
[00:42] the variance divided by the square of that number.
[00:46] So if the variance is small, the probability of falling far
[00:50] from the mean is also going to be small.
[00:53] And if the number c is large, so that we're talking about a
[00:57] large distance from the mean, then the probability of this
[01:01] event happening falls off at a rate at
[01:04] least 1 over c squared.
[01:08] By the way, I should add here that c is assumed to be a
[01:13] positive number.
[01:14] If c was negative, then the probability that we're looking
[01:18] at would be equal to 1 anyway.
[01:20] And there isn't any point in trying obtain a bound for it.
[01:24] To prove the Chebyshev inequality, we will apply the
[01:27] Markov equality as follows.
[01:30] The probability of interest is the same as the probability
[01:39] that the square of this quantity is larger than or
[01:46] equal to the square of c.
[01:49] But now, here we have a non-negative random variable.
[01:53] And we can apply the Markov inequality with X replaced by
[01:57] this random variable and with a replaced by c squared.
[02:01] So this gives us the expected value of the random variable
[02:05] of interest divided by c squared.
[02:10] But we recognize that the
[02:12] numerator is just the variance.
[02:16] And this is the Chebyshev inequality that we claimed.
[02:22] As an application of the Chebyshev inequality, let us
[02:25] look at the probability of this event that the distance
[02:28] from the mean is at least k standard deviations, where k
[02:34] is some positive number.
[02:37] Using the Chebyshev inequality with c replaced by k times
[02:41] sigma, we obtain sigma squared over c squared, which in our
[02:47] case is k squared times sigma squared,
[02:50] which is 1 over k squared.
[02:53] So what this is saying is that if you take, for example, k
[02:57] equal to 3, the probability that you fall three standard
[03:02] deviations away from the mean or more, that probability is
[03:07] going to be less than or equal to 1 over 9.
[03:10] And this is true no matter what kind of
[03:12] distribution you have.
[03:15] Let us now revisit our earlier example, where X is an
[03:19] exponential random variable.
[03:20] And we're interested in the probability that the random
[03:23] variable takes a value larger than or equal to a.
[03:26] The Markov inequality gave us a bound of 1 over a.
[03:32] And as we recall, the exact answer to this probability was
[03:38] e to the minus a.
[03:40] Let us see what we can get using the Chebyshev
[03:43] inequality.
[03:44] Now, our random variable has a mean of 1.
[03:50] Let us assume that a is bigger than 1, so that we're
[03:55] considering an event that we fall far away from the mean by
[04:01] a distance of at least a minus 1.
[04:05] That is we write the probability that X is larger
[04:08] than or equal to a as the probability that the distance
[04:12] of X from the mean is larger than or equal to a minus 1.
[04:18] And now, this event is smaller than the event that the
[04:26] absolute value of X minus 1 is larger than a minus 1.
[04:33] This is because if this event is true, then that event will
[04:38] also be true.
[04:39] And now, we can apply the Chebyshev inequality.
[04:42] Here we have the distance of X from the mean.
[04:45] So the Chebyshev inequality applied to the random variable
[04:50] X will have up here the variance of X,
[04:53] which is equal to 1.
[04:55] And in the denominator, we will have a minus 1 squared.
[05:03] Notice that if a is a large number, this quantity here
[05:08] behaves like 1 over a squared, which falls off much faster
[05:14] than 1 over a.
[05:15] So at least for large a's, the Chebyshev bound is going to
[05:20] give us a smaller bound and, therefore, more informative
[05:26] than what we obtained from the Markov inequality.
[05:30] In most cases, the Chebyshev inequality is, indeed,
[05:34] stronger and more informative than the Markov inequality.
[05:38] And one of the reasons is that it exploits more information
[05:43] about the distribution of the random variable X. That is it
[05:46] uses knowledge, not just about the mean
[05:49] of the random variable.
[05:50] But it also uses some information about the variance
[05:54] of the random variable.
