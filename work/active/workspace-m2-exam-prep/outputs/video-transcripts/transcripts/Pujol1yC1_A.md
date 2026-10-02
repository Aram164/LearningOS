---
video_id: Pujol1yC1_A
url: https://www.youtube.com/watch?v=Pujol1yC1_A
title: Introduction to the Central Limit Theorem
channel: jbstatistics
duration: 13:13
language: en
unit: L08
status: OK
---

[00:02] Let's talk about the central limit theorem, an extremely important concept in statistics.
[00:08] The gist of the central limit theorem
[00:10] is that the sample mean will be approximately normally distributed for large sample sizes,
[00:14] regardless of the distribution from which we are sampling.
[00:19] And I'm going to illustrate this using simulation in a little bit.
[00:24] First let's recall a few characteristics of the sampling distribution of the sample mean.
[00:29] Suppose we are sampling from a population with mean mu and standard deviation sigma.
[00:35] Let X bar be a random variable representing the sample mean of n independently drawn observations from this distribution.
[00:44] We have previously learned
[00:46] that the mean of the sampling distribution of the sample mean is equal to the population mean,
[00:51] the mean of the sampling distribution of the sample mean is equal to the mean of
[00:55] the population from which we are sampling.
[00:59] We've also learned that the standard deviation of the sampling distribution of X bar
[01:04] is equal to sigma over the square root of n.
[01:09] As previously discussed,
[01:11] if the population is normally distributed,
[01:14] then the sample mean X bar is also normally distributed.
[01:18] But what if the population is not normal?
[01:21] The central limit theorem addresses this question.
[01:26] The distribution of the sample mean tends toward the normal distribution as the sample size increases,
[01:33] regardless of the distribution from which we are sampling.
[01:38] Let's illustrate this through simulation.
[01:42] Here's an exponential distribution which is most definitely not normal.
[01:47] And what I'm going to do is I'm going to draw a sample of 2 observations, so n is 2,
[01:52] I'm going to draw 2 independent values from this distribution and get the mean.
[01:57] And I'm going to do that again and again and again a million times,
[02:02] and so we're going to get a million sample means where n is equal to 2.
[02:09] One thing to note right off the bat
[02:11] is that I'm allowing the y axis scaling and the x axis scaling to change.
[02:16] What we're interested here is the shape of the distribution.
[02:22] The grey histogram here is a histogram of those of million sample means where n=2,
[02:29] and this is going to be approximately the sampling distribution of X bar in this scenario.
[02:36] In this particular spot we can mathematically work out the exact sampling distribution,
[02:41] but here i've done it through simulation.
[02:44] We can see that this distribution retains some of the original distribution here,
[02:49] we've got some right skewness. It's most definitely not normal.
[02:55] Here, this white line I've plotted in, superimposed,
[02:57] a normal curve with the appropriate mean and variance.
[03:01] And we can see here is that when n is 2
[03:03] the sampling distribution of the sample mean is not normal.
[03:09] Let's see what happens when I increase the sample size.
[03:14] Here again have drawn a million samples,
[03:16] this time the sample size in each one of those samples is 4,
[03:20] and I've plotted out those million sample means in a histogram,
[03:24] and that is approximately the sampling distribution of X bar when n is 4.
[03:29] Here again we still have some of that skewness
[03:34] and it's not quite normal, but it's getting there.
[03:37] Still quite a bit different from this superimposed normal curve though.
[03:42] When n is 10 we're getting a little bit closer
[03:45] but we can still see some of that skewness.
[03:49] When n is 20 we're getting closer still.
[03:54] and when n is 50
[03:56] this histogram of sample means, which is approximately the sampling distribution of X bar when n is 50 here,
[04:04] is pretty close to that superimposed normal curve.
[04:07] So for a sample size of 50
[04:10] the sampling distribution of X bar is pretty close to normal.
[04:14] And we'd see if I did this for larger and larger sample sizes
[04:18] it would be getting more and more normally distributed.
[04:21] It would look better and better and closer and closer to that superimposed normal curve.
[04:29] What I was illustrating there
[04:30] is that when we are sampling from non normal populations
[04:34] the distribution of the sample mean tends toward the normal distribution as the sample size increases.
[04:43] As a very rough guideline
[04:45] the sample mean can be considered to be approximately normally distributed if the sample size is at least 30.
[04:52] if our n is at least 30.
[04:55] Again this is a very rough guideline.
[04:59] We can easily construct scenarios in which a sample size of a hundred trillion
[05:04] is not nearly enough to give us approximate normality,
[05:08] but in most practical situations
[05:10] when our sample size starts getting up beyond 30
[05:13] the distribution of the sample mean will be approximately normal.
[05:18] Let's do another simulation for a different distribution.
[05:22] This one's a bit of a weird mixture type of distribution.
[05:27] So the same scenario as the last time,
[05:29] I'm going to randomly and independently draw 2 observations from this distribution,
[05:34] draw another 2 observations, calculate the sample mean,
[05:39] and do that a million times, and plot out a histogram.
[05:45] Here the grey histogram is approximately the sampling distribution of X bar when n=2,
[05:52] and I've superimposed the normal curve again
[05:55] and obviously this distribution is not quite normal.
[05:59] Let's increase the sample size and see what happens.
[06:04] Note that in this series of plots I'm keeping the scaling on the x-axis the same
[06:08] and letting the y axis scaling change from plot to plot.
[06:13] Here I've done this a million times, sampled from the original distribution a million times,
[06:18] for a sample size of 4,
[06:21] and plotted out the million resulting sample means in the histogram,
[06:25] so the grey histogram is approximately the sampling distribution of X bar when n is equal to 4.
[06:32] And I've superimposed the normal curve
[06:34] with the appropriate mean and variance.
[06:36] And we can see here that the sampling distribution of X bar is actually quite close to normal.
[06:43] And we'll see that when we let the sample size increase
[06:46] it's going to get closer and closer and closer to that superimposed normal curve.
[06:52] Here when n is 10 the sampling distribution of X bar looks quite normal.
[06:58] When n is 20 it's even closer to that normal curve.
[07:03] And when n is 50 it's looking very normal.
[07:06] And the sampling distribution of X bar would get closer and closer and closer
[07:11] to a normal distribution as the sample size increases.
[07:18] Why is this important?
[07:21] The central limit theorem tells us that many statistics have distributions
[07:25] that are approximately normal for large sample sizes,
[07:28] even when we are sampling from a distribution that is not normal.
[07:35] And this means that we can often use well-developed statistical inference procedures and probability calculations
[07:41] that are based on a normal distribution,
[07:44] even if we are sampling from a population that is not normal,
[07:48] provided we have a large sample size.
[07:54] A little more formally,
[07:55] the central limit theorem tells us that our usual z score value here involving the sample mean,
[08:03] that tends in distribution to the standard normal distribution as the sample size tends to infinity.
[08:12] We do have a couple of technical restrictions
[08:15] in that we need the mean and variance to be finite,
[08:19] but that's usually going to be the case for the things we're dealing with.
[08:25] Let's see how the central limit theorem might help us carry out a probability calculation.
[08:29] Suppose salaries at a very large corporation have a mean of $62,000
[08:34] and a standard deviation of $32,000.
[08:37] Our population mean mu is 62,000
[08:41] and our population standard deviation sigma is 32,000.
[08:48] If a single employee is a randomly selected,
[08:51] what is the probability their salary exceeds $66,000?
[08:57] Let's let the random variable X
[08:59] represent the salary of a randomly selected employee.
[09:02] What we want to find is the probability that X is greater than $66,000.
[09:10] We've previously done some probability calculations
[09:13] and said that Z is equal to X minus mu over sigma.
[09:20] So it might be tempting here to say that this is equal to the probability
[09:24] that Z is greater than 66,000 minus 62,000 over 32,000
[09:35] and this would be equal to the probability that Z is greater than 0.125.
[09:44] We haven't done anything wrong to this point,
[09:46] but if we were to find this probability
[09:48] by looking it up for the standard normal distribution, that would be an error.
[09:55] Nowhere in this question does it say that salaries are normally distributed,
[10:01] and we've learned previously that salaries are simply not normally distributed typically.
[10:05] Salaries have some right skewness to them.
[10:09] So salaries are not normally distributed,
[10:11] nowhere in this question does it say anything about normal
[10:14] and so this random variable X is not going to have a normal distribution,
[10:20] which means that this random variables Z is going to not have a standard normal distribution,
[10:26] and so this question cannot be answered without further information about the distribution of X.
[10:37] But suppose we changed the question a little bit.
[10:40] We still have the same premise in that we're sampling from a population with
[10:44] a mean of 62,000 and a standard deviation of 32,000.
[10:51] And here it changes to if 100 employees are randomly selected,
[10:56] what is the probability their average salary exceed $66,000?
[11:02] And we're going to let X bar represent the average salary of those 100 employees.
[11:08] And we want to know the probability that X bar takes on a value greater than $66,000.
[11:16] Well we previously had this notion that we can standardize that
[11:21] and call it a Z if we go X bar minus mu over sigma over the square root of n.
[11:28] And here the fundamental difference in this question as opposed to the previous question
[11:34] is that X bar is going to be approximately normally distributed, by the central limit theorem.
[11:40] The central limit theorem tells us that the sample mean will be approximately normally distributed in this spot,
[11:46] so we can come up with an approximate probability
[11:49] even though we don't know the real distribution of the salaries.
[11:54] And so this is going to be the probability that Z is greater than 66,000 minus 62,000
[12:04] over sigma which is 32,000, over the square root of the sample size.
[12:11] And this is the probability that Z is greater than 1.25.
[12:18] The central limit theorem tells me that X bar is approximately normal
[12:21] which tells me that Z has approximately the standard normal distribution,
[12:28] And so this probability, for that we're going to go to our normal curve.
[12:33] Here's zero, 1.25 is over here somewhere
[12:37] and if we looked that up using software or a table we'd see that that is 0.106.
[12:44] So the central limit theorem has allowed me to say
[12:47] that this probability here is approximately 0.106,
[12:53] even though we didn't know that distribution from which we were sampling.
[13:00] This is going to be an extremely helpful notion in a lot of spots.
[13:04] The world of statistics would be very very different
[13:07] if there was no such thing as the central limit theorem.
