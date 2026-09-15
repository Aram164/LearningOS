---
video_id: Uv6nGIgZMVw
url: https://www.youtube.com/watch?v=Uv6nGIgZMVw
title: Introduction to the t Distribution (non-technical)
channel: jbstatistics
duration: 8:54
language: en
unit: L09
status: OK
---

[00:01] Let's look at an introduction to the Student t distribution,
[00:04] often shortened to simply the t distribution.
[00:07] This video is a little light on mathematical details,
[00:10] so if you're looking for how the t distribution arises mathematically,
[00:13] or its pdf, I go through that in another video.
[00:18] Suppose we are about to draw a random sample of n observations
[00:22] from a normally distributed population.
[00:24] We've previously learned that the quantity X bar minus mu
[00:27] over sigma over the square root of n has the standard normal distribution.
[00:31] And we typically label that with the letter Z.
[00:35] Previously, we've used this notion to construct a confidence interval
[00:38] for the population mean mu.
[00:40] But in practice we encounter a problem, and that problem is
[00:45] that we don't know the value of the population standard deviation sigma.
[00:48] Sigma is a parameter, the standard deviation for the entire population,
[00:54] and we don't typically know its value, so we can't use that value in a formula.
[00:59] So we do the next best thing, and instead of using the population standard deviation,
[01:04] we're going to use our sample standard deviation to estimate it
[01:08] and then we're going to have a statistic X bar minus mu
[01:11] over s over the square root of n, where s is our sample standard deviation.
[01:19] But something very fundamental has changed here.
[01:23] Sigma is a constant but we don't know its value
[01:26] so we use s, which is a statistic, and this statistic s has a sampling distribution,
[01:32] and it would vary from sample to sample.
[01:35] And so this quantity down here
[01:37] would no longer have the standard normal distribution.
[01:41] And we call this quantity or we label it as t
[01:44] because it has a t distribution.
[01:51] When we are sampling from a normally distributed population,
[01:55] the quantity X bar minus mu over s over the square root of n
[01:58] has the t distribution with n-1 degrees of freedom.
[02:02] The concept of degrees of freedom can be a bit of a tricky one,
[02:06] so I'm not going to get into the details here.
[02:09] But the degrees of freedom for the t
[02:15] and if you recall when we had our sample variance s squared, we divided by n-1.
[02:21] those two notions are very much tied together.
[02:26] What does the t distribution look like?
[02:28] We'll look at that in a moment, but if we look at this statistic,
[02:33] it looks very much like our Z statistic, which has the standard normal distribution,
[02:38] Except we've replaced the population standard deviation
[02:41] with the sample standard deviation.
[02:44] We are estimating a parameter with a statistic
[02:47] so there is greater variability. So our t distribution is going
[02:52] to look a lot like the standard normal distribution, except with greater variance.
[02:59] Here's a plot of the standard normal distribution in white
[03:02] and a t distribution with one degree of freedom in red.
[03:05] We can see that both distributions are symmetric about zero and bell-shaped,
[03:10] but the t distribution has heavier tails and a lower peak.
[03:15] The exact shape of the t distribution depends on the degrees of freedom.
[03:20] A very fundamental point here is that as the degrees of freedom increase,
[03:25] the t distribution tends toward the standard normal distribution.
[03:30] So I'm going to let the degrees of freedom increase and let's see what happens.
[03:36] as the degrees of freedom increase here
[03:40] we see the red curve getting closer and closer and closer to the white curve.
[03:45] or in other words, as the degrees of freedom increase
[03:47] the t distribution is tending towards the standard normal distribution.
[03:53] I've stopped it here at 20 degrees of freedom,
[03:56] and the curves might look close, but if we look very closely we would see that
[04:00] the t distribution still has slightly heavier tails and a slightly lower peak.
[04:06] But if I let those degrees of freedom continue to increase,
[04:09] the t distribution is going to get closer and closer and closer to the standard normal distribution.
[04:18] This has some implications for us in statistical inference.
[04:21] Here I'm going to look at constructing a 95% confidence interval,
[04:26] but the same notion would hold in many other situations as well.
[04:30] If we are sampling from a normally distributed population,
[04:33] and we happen to know the value of the population standard deviation sigma,
[04:37] then we've discussed previously that this is the appropriate formula for our confidence interval.
[04:43] This 1.96 comes from the standard normal distribution.
[04:46] And I've drawn in the standard normal distribution down here.
[04:50] If we want a 95% confidence interval
[04:53] then we put an area of 0.95 in the middle,
[04:57] and we divide up the remaining area of 0.05
[05:01] evenly into the two tails,
[05:03] putting 0.025 in the right tail and 0.025 in the left tail.
[05:08] We call the value here with an area to the right of 0.025
[05:14] z_.025,
[05:19] and that value is 1.96,
[05:23] which we've encountered previously,
[05:25] and we can find from the standard normal table or software.
[05:31] But if sigma is not known,
[05:33] then we can't use it in our confidence interval formula,
[05:36] and we would have to replace it with the sample standard deviation.
[05:39] But then we should no longer use 1.96,
[05:43] we shouldn't use a value based on the standard normal distribution,
[05:47] we need to use a value based on the t distribution.
[05:50] So down here I've drawn in a t distribution,
[05:53] and we use the same logic in that we want to put 95%
[05:57] of the area in the middle and split up the remaining area evenly into the two tails.
[06:04] And so what we want to find
[06:06] is from this t distribution the t value
[06:10] that gives an area to the right of 0.025.
[06:14] Because the t distribution has greater area in the tails
[06:18] and greater variability than the standard normal distribution,
[06:29] How much greater?
[06:31] Well that depends on the degrees of freedom,
[06:33] because the shape of the t distribution depends on the degrees of freedom.
[06:36] But let's look at a few values.
[06:41] Here I have a table with the appropriate t value for various degrees of freedom.
[06:44] This first column has the sample size n.
[06:48] The second column has the degrees of freedom,
[06:51] which are n-1 for the case we're discussing today.
[06:54] And then the appropriate t value for a 95% confidence interval.
[07:00] This can be found from a t table or software.
[07:03] Take note that at infinite degrees of freedom we get our z value of 1.96,
[07:09] that is our z_.025 value,
[07:12] and that's because a t distribution with infinite degrees of freedom
[07:16] is the same as the standard normal distribution.
[07:20] But if we look up here with five degrees of freedom,
[07:23] we see that the t value is 2.571,
[07:26] which is quite a bit bigger than the 1.96 value from the standard normal distribution.
[07:31] As the degrees of freedom increase,
[07:34] the t distribution is getting closer and closer and closer to the standard normal distribution,
[07:41] so these t values are getting closer and closer and closer and closer
[07:46] to 1.96, the value from the standard normal distribution.
[07:51] Some sources go so far as to say that if the sample size is greater than 30
[07:55] just forget all about the t distribution and use the standard normal distribution.
[08:00] But if you take statistics from me, forget you ever heard such a notion.
[08:05] If we look here at 30 degrees of freedom
[08:07] we see that the t value is 2.042,
[08:11] which to me at least is quite a bit bigger than the z value of 1.96.
[08:16] Even at 100 degrees of freedom the t value
[08:21] still is a little bit different than the 1.96.
[08:24] And so if we use this z value when we should be using the t value
[08:28] our calculated margin of error will be smaller than it should be.
[08:34] If we are sampling from a normally distributed population
[08:38] and we are using a standard deviation that is based on our sample's data,
[08:42] then we should be using values from the t distribution
[08:46] and not the standard normal distribution,
[08:48] regardless of the sample size.
