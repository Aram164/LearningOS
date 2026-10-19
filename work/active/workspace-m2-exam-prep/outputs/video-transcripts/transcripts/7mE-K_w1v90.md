---
video_id: 7mE-K_w1v90
url: https://www.youtube.com/watch?v=7mE-K_w1v90
title: Type I Errors, Type II Errors, and the Power of the Test
channel: jbstatistics
duration: 8:10
language: en
unit: L10
status: OK
---

[00:01] Let's look at type I errors, type II errors, and the power of the test in hypothesis testing.
[00:08] A type I error is rejecting the null hypothesis when in reality it is true.
[00:15] A type II error is failing to reject the null hypothesis when in reality it is false.
[00:27] or if we made one of these two errors.
[00:32] Suppose we test the null hypothesis that mu is equal to 10,
[00:36] against the alternative that it's greater than 10.
[00:38] We carry out the test in the usual ways and we end up
[00:42] rejecting the null hypothesis at an alpha level of 0.05.
[00:47] One of two things occurred:
[00:49] the null hypothesis is false and we rejected it,
[00:52] so we made the correct decision, or
[00:56] the null hypothesis is true and we rejected it,
[00:59] so we made a type I error.
[01:04] In practice if we reject the null hypothesis
[01:08] we are simply not going to know which one of these two things occurred.
[01:14] But suppose instead that we carry out the same test
[01:18] and we do not reject the null hypothesis at an alpha level of 0.05.
[01:22] Well here again one of two things occurred:
[01:26] the null hypothesis is true and we did not reject it
[01:29] so we made the correct decision, or
[01:32] the null hypothesis is false and we did not reject it,
[01:36] so we made a type II error.
[01:43] Here in table form are the possible outcomes of a hypothesis test.
[01:47] In the columns is the underlying reality
[01:49] and that's going to be unknown to us.
[01:52] in the rows are the conclusion from the test,
[01:55] which is going to be known once we carry out our test.
[02:01] If we end up rejecting the null the null hypothesis
[02:04] and the null hypothesis is false, we made the correct decision.
[02:09] But if we rejected the null hypothesis and the null hypothesis is true
[02:13] we made a type I error.
[02:18] If we do not reject the null hypothesis
[02:21] and in reality the null hypothesis is false, we made a type II error.
[02:26] But if we don't reject the null hypothesis, and in reality it's true, we made the correct decision.
[02:38] Some people find it helps to compare the conclusions in a hypothesis test
[02:41] to the results of the criminal trial.
[02:44] In a criminal trial we test the null hypothesis
[02:48] that the defendant did not commit the crime
[02:49] against the alternative hypothesis that the defendant did commit the crime.
[02:56] In a criminal trial we give the defendant the benefit of the doubt
[02:59] and use terms like innocent until proven guilty.
[03:02] Well it's similar in a hypothesis test
[03:05] we will only reject the null hypothesis if we have very strong evidence against it.
[03:13] In a criminal trial setting, a type I error would be
[03:18] convicting a person who, in reality, did not commit the crime.
[03:21] In other words, rejecting the null hypothesis when it is in fact true.
[03:27] A type II error is acquitting a person who in reality committed the crime.
[03:32] In other words, not rejecting the null hypothesis when it is in fact false.
[03:40] Nobody likes the idea of spending the rest of their life in jail
[03:43] for a crime they did not commit,
[03:45] and so as a society
[03:47] we've decided to make the probability of a tight I error small,
[03:51] by using language like beyond a reasonable doubt.
[03:57] The probability of a type I error,
[03:59] given the null hypothesis is true,
[04:01] is called the significance level of the test,
[04:04] and it's typically represented by alpha.
[04:08] We get to pick the value of alpha that we feel is appropriate for any given problem.
[04:16] The probability of a type II error is represented by beta.
[04:21] The value of beta depends on a number of factors, including the choice of alpha,
[04:25] the sample size, and the true value of the parameter.
[04:28] It depends on other factors as well, such as the alternative hypothesis and the variance.
[04:36] The power of the test is the probability of rejecting the null hypothesis given it is false.
[04:42] Power is 1 minus the probability of a type II error, or 1-beta.
[04:47] And of course the power depends on the same factors as beta does.
[04:57] Alpha is the probability of a type I error, given the null hypothesis is true,
[05:02] and we choose the value of alpha,
[05:04] so why not choose alpha to be some tiny value
[05:07] so we're not making a lot of type I errors?
[05:10] It's because of the relationship between alpha and beta.
[05:14] If we decrease alpha, then beta will increase.
[05:20] If we choose a very small value of alpha
[05:23] we will be making it very difficult to reject the null hypothesis
[05:27] and so type II errors will be very common.
[05:32] If we choose a larger value of alpha,
[05:34] it will become easier to reject the null hypothesis
[05:38] and so type II errors will be less common.
[05:43] Let's take a look at the relationship between alpha and beta
[05:46] for a test of the null hypothesis that mu is equal to 0.
[05:51] to calculate beta, I had to make a decision on a few of these quantities down here,
[05:55] and I show how to actually calculate beta in another video.
[05:59] For now let's not worry too much about my choices there or how to calculate beta
[06:03] and let's focus on the relationship between alpha and beta.
[06:08] over here I put in the power which is simply one - beta.
[06:14] If we chose the common alpha value of 0.05,
[06:19] and we went up here, we'd see that the corresponding beta value is 0.77,
[06:23] that's the actual calculated value.
[06:28] So the probability of a type II error in this scenario is 0.77.
[06:33] And the corresponding power of the test is 1 minus that, 0.23.
[06:42] If we let alpha increase from 0.05 to 0.10,
[06:47] then we're going to be decreasing the probability of a type II error,
[06:52] and increasing the power of the test.
[06:56] If however we chose an alpha value that was very near zero,
[07:01] beta would creep up very close to one
[07:04] and our test would have almost no power.
[07:08] so there is a balancing act between alpha and beta.
[07:12] But in many practical situations people simply pick an alpha level they feel is appropriate
[07:17] and let beta fall where it may.
[07:21] Alpha is usually chosen to be a small value
[07:25] like 0.01 or 0.05,
[07:27] but for completeness let's look at the relationship between alpha, beta and power
[07:31] over all possible values of alpha.
[07:35] iI we choose a value of alpha very near zero,
[07:38] then depending on the other factors,
[07:40] beta will typically be very close to one,
[07:44] and the test will have very low power.
[07:47] But if we were to choose a value of alpha over here near one
[07:52] beta would be very close to 0 and the test would have very high power.
[07:56] But in statistics we do not like making a lot of type I errors,
[07:59] so alpha is typically chosen to be a small value like 0.01 or 0.05.
