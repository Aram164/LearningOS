---
video_id: UsU-O2Z1rAs
url: https://www.youtube.com/watch?v=UsU-O2Z1rAs
title: What is a p-value?  (Updated and extended version)
channel: jbstatistics
duration: 10:50
language: en
unit: L10
status: OK
---

[00:02] In this video I'm going to look at the question: what is a p-value?
[00:05] I'm going to do one simple example of finding the p-value,
[00:08] but this video is mainly about the concept of the p-value.
[00:14] The p-value is a measure of the strength of the evidence against the null hypothesis
[00:19] that is provided by our sample data.
[00:24] The p-value is the probability of getting the observed value of the test statistic,
[00:29] or a value with even greater evidence against the null hypothesis,
[00:34] if the null hypothesis is in fact true.
[00:37] So first of all the p-value is a probability
[00:40] and it is a probability calculated conditional on the null hypothesis being true.
[00:49] The definition is a bit of a mouthful, so let's look at an example.
[00:55] Suppose we wish to carry out a test of the null hypothesis
[00:58] that mu, the population mean, is equal to some hypothesized value.
[01:02] And suppose that we are sampling from a normally distributed population,
[01:06] where sigma is known.
[01:08] If that's the case, the appropriate test statistic is this Z test statistic.
[01:14] If this null hypothesis is in fact true,
[01:17] then mu is equal to mu_0,
[01:20] and this statistic will have the standard normal distribution.
[01:24] And so over here I have the distribution of that Z test statistic, if the null hypothesis is true,
[01:32] and that is the standard normal distribution.
[01:36] Suppose for the sake of illustration
[01:39] that we get a sample and we find that the value of the test statistic is 2.05.
[01:46] 2.05 is right about here on the curve.
[01:51] In this case our alternative hypothesis
[01:53] is that the population mean is greater than the hypothesized value,
[01:58] and so large values of this test statistic
[02:01] are going to give us evidence against the null hypothesis.
[02:05] The farther out in the right tail that this test statistic is,
[02:09] the greater the evidence against the null hypothesis.
[02:16] And recall that the p-value
[02:18] is the probability of getting the observed value of the test statistic,
[02:21] or something with even greater evidence against the null hypothesis,
[02:25] if the null hypothesis is true.
[02:29] So in this case, that's going to be the probability, under the null hypothesis,
[02:33] of getting the observed value of the test statistic
[02:37] or something even farther out in the right tail.
[02:41] Or in other words, the area to the right of the observed test statistic.
[02:47] That is going to be be the p-value here.
[02:52] And if we went to software or a standard normal table here
[02:55] we'd see that this is approximately 0.020.
[03:03] In this particular setting, the farther out in the right tail
[03:06] the observed value of the test statistic is,
[03:09] the smaller the p-value, and the greater the evidence against the null hypothesis.
[03:18] And this is true in the more general setting.
[03:22] The smaller the p-value, the greater the evidence against the null hypothesis.
[03:30] If we have a given significance level alpha,
[03:33] then we reject the null hypothesis
[03:36] if the p-value is less than or equal to the significance level alpha.
[03:42] Or we could say that the evidence against the null hypothesis is significant
[03:48] at the alpha level of significance.
[03:51] And so we could consider alpha to be a cut-off level for significance.
[04:00] In the real world, we're not always going to have an alpha level given to us,
[04:03] and then the situation is not quite so simple.
[04:08] If we do have a given significance level, then situation is not as cut and dried.
[04:15] But it might help us come up with a reasonable conclusion
[04:18] if we understand the distribution of the p-value.
[04:24] For continuous test statistics, under the assumptions of the model,
[04:28] if the null hypothesis is true the p-value
[04:32] will have a uniform distribution between 0 and 1.
[04:38] And a little loosely speaking, any value
[04:40] between 0 and 1 is equally likely to occur,
[04:45] if the null hypothesis is true.
[04:47] And so if the null hypothesis is true,
[04:50] on average we're going to get a p-value of 0.5.
[04:56] But it also might help with our interpretation if we know something
[05:00] about the distribution of the p-value when the null hypothesis is false.
[05:06] So let's simulate a million samples
[05:09] to investigate the distribution of the p-value in different scenarios.
[05:15] Here I've decided to test the null hypothesis that mu=0,
[05:20] against a two-sided alternative.
[05:22] The samples have 20 observations in them, and sigma is equal to 5.
[05:28] And we are sampling from a normally distributed population,
[05:31] so we'll be using as Z test.
[05:33] And on this slide, there's three scenarios illustrated.
[05:37] In this first one, mu=0,
[05:40] so the true value of the population mean is equal to the hypothesized mean,
[05:45] or in other words, the null hypothesis is true.
[05:50] Here's a histogram of the million p-values,
[05:53] corresponding to those million different samples that I've simulated.
[05:56] And as we can see, that p-value seems to have that uniform distribution.
[06:02] The theoretical average value for our p-value when the null hypothesis is true
[06:06] is 0.5, and here in the simulation, we also get a value of 0.50 to 2 decimal places.
[06:17] Down here I'm going to look at two situations where the null hypothesis is false.
[06:22] In this first one, the true value of mu is 1,
[06:26] and we're still hypothesizing that it's zero,
[06:28] so the null hypothesis is false.
[06:31] I've simulated a million samples where mu is actually 1,
[06:35] and find out what the p-value is, and plot it in this histogram.
[06:42] And here the distribution is not uniform anymore,
[06:45] the distribution is moved towards 0.
[06:49] And in this situation, for those million p-values,
[06:52] we find an average p-value of 0.39.
[06:59] In this other situation, the null hypothesis is still false,
[07:04] but mu is even farther from the hypothesized value.
[07:09] And this histogram of p-values is shifted even farther over toward 0,
[07:15] and the average p-value we got here is 0.18.
[07:22] And so we can see here that when the null hypothesis is true,
[07:26] the p-value has a uniform distribution between 0 and 1,
[07:30] and when the null hypothesis is false, the distribution of the p-value moves more toward zero.
[07:35] So we're going to be more likely to get p-values near 0
[07:40] when the null hypothesis is false
[07:43] than when the null hypothesis is true.
[07:50] We saw here that the distribution of the p-value
[07:53] depends on what the true value of the population mean is.
[07:57] It's also going to depend on the sample size, and the standard deviation in this case.
[08:06] To illustrate that,
[08:07] let's see what happens when we increase the sample size to 50.
[08:12] The only thing that's been changed in this simulation
[08:16] is that the sample size has been increased to 50.
[08:19] We can see here when the null hypothesis is true
[08:22] that that distribution of the p-value is still uniform between 0 and 1,
[08:29] and when the null hypothesis is false,
[08:32] the distribution of the p-value still, again, moves toward zero.
[08:38] But because of the increased sample size,
[08:41] down here when the null hypothesis is false,
[08:44] the p-value distribution has shifted even farther towards 0.
[08:49] Over here the average p-value is now 0.27,
[08:54] and over here the average p-value is now 0.04.
[08:58] When we have a greater sample size,
[09:00] our tests are going to have greater power,
[09:03] and the distribution of the p-value is going to be shifted more toward 0.
[09:10] The overall lesson I'm trying to get at here
[09:12] is that we're more likely to get p-values close to 0
[09:15] when the null hypothesis is wrong than when the null hypothesis is right.
[09:20] And so the smaller the p-value, the greater the evidence against the null hypothesis.
[09:31] I'm going to give a very rough guideline here.
[09:34] It has to be a very rough guideline
[09:36] because what we feel is strong evidence against the null hypothesis
[09:40] depends on the situation at hand as well as the p-value.
[09:45] But as a very rough guideline, if the p-value is less than 0.01
[09:50] we can say there is very strong evidence against the null hypothesis.
[09:54] If the p-value lies between point 0.01 and 0.05,
[09:58] well, there's starting to be strong evidence against the null hypothesis.
[10:04] If the p-value is between 0.05 and 0.10,
[10:07] there's some weak evidence against the null hypothesis.
[10:11] And if the p-value is greater than 0.10 we say there's
[10:14] little or no evidence against the null hypothesis.
[10:18] This does depend on the setting. If the p-value is close to 0.10,
[10:22] some situations we may feel that that has a hint of evidence against the null hypothesis.
[10:26] For example, if our p-value is 0.11 or 0.13 or something like that,
[10:31] in some situations we might view that as a hint of evidence against the null hypothesis.
[10:36] But for most practical cases once the p-value starts getting up into the 0.2
[10:39] and 0.3 range and greater,
[10:41] we say that there is no evidence against the null hypothesis.
