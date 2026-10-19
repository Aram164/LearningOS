---
video_id: EJe3jiZNwUU
url: https://www.youtube.com/watch?v=EJe3jiZNwUU
title: What are confidence intervals? Actually.
channel: zedstatistics
duration: 24:03
language: en
unit: L09
status: OK
---

[00:00] Confidence intervals are one of the foundational concepts of statistics. You
[00:04] foundational concepts of statistics. You might see them in academic journals, in
[00:07] might see them in academic journals, in forest plots, funnel plots, bar charts.
[00:11] forest plots, funnel plots, bar charts. They're everywhere, but how are they
[00:13] They're everywhere, but how are they actually constructed? And why do we need
[00:15] actually constructed? And why do we need them?
[00:16] them? Well, in this video, we're going to be
[00:18] Well, in this video, we're going to be exploring all those concepts and more.
[00:20] exploring all those concepts and more. My name is Justin Zeltzer and this is
[00:22] My name is Justin Zeltzer and this is zstatistics.com.
[00:30] Now, this video forms part of a series on the foundational concepts of health
[00:34] on the foundational concepts of health statistics. And if you want to see any
[00:37] statistics. And if you want to see any of the other videos, you can check out
[00:38] of the other videos, you can check out the link in the description below. I'll
[00:41] the link in the description below. I'll put a link to the playlist. Uh, but you
[00:43] put a link to the playlist. Uh, but you can see all my videos up on
[00:44] can see all my videos up on zstatistics.com.
[00:47] zstatistics.com. And as always, if you like the video,
[00:49] And as always, if you like the video, give us a thumbs up, subscribe, and do
[00:51] give us a thumbs up, subscribe, and do all that stuff. That'll help me out a
[00:52] all that stuff. That'll help me out a ton. Uh, otherwise, let's jump straight
[00:55] ton. Uh, otherwise, let's jump straight into confidence intervals, shall we?
[01:01] All right. So, the first thing I'm going to do is work on your intuition around
[01:06] to do is work on your intuition around confidence intervals. Trying to do it
[01:08] confidence intervals. Trying to do it without any mathematical formula.
[01:11] without any mathematical formula. We're going to move on then to an actual
[01:13] We're going to move on then to an actual calculation of confidence intervals. And
[01:16] calculation of confidence intervals. And we're going to be looking at two
[01:17] we're going to be looking at two particular intervals that are commonly
[01:20] particular intervals that are commonly created. One which is created for a
[01:22] created. One which is created for a population mean and the other which is
[01:25] population mean and the other which is created for a population proportion.
[01:28] created for a population proportion. From there, we'll have a look at some
[01:30] From there, we'll have a look at some other examples of confidence intervals
[01:32] other examples of confidence intervals you might see in the wild.
[01:35] you might see in the wild. And finally, I've got this sealed
[01:36] And finally, I've got this sealed section just for the stats nerds out
[01:39] section just for the stats nerds out there. Or even if you're not a stats
[01:41] there. Or even if you're not a stats nerd, you can come along.
[01:43] nerd, you can come along. We're going to have a quick look at the
[01:44] We're going to have a quick look at the difference between frequentist and
[01:46] difference between frequentist and Bayesian intervals. But let's jump
[01:49] Bayesian intervals. But let's jump straight into the intuition now. So, the
[01:51] straight into the intuition now. So, the first thing we need to understand is
[01:53] first thing we need to understand is that statistics is about estimation.
[01:57] that statistics is about estimation. That's a crucial point to get your head
[01:59] That's a crucial point to get your head around confidence intervals.
[02:01] around confidence intervals. So, here's the example I'm going to be
[02:02] So, here's the example I'm going to be using.
[02:03] using. We want to know what the average resting
[02:05] We want to know what the average resting heart rate is for women.
[02:08] heart rate is for women. So, if I was to ask you how you'd find
[02:11] So, if I was to ask you how you'd find the average resting heart rate for
[02:13] the average resting heart rate for women,
[02:14] women, you might say, "Well, look, Justin, I
[02:15] you might say, "Well, look, Justin, I need to take a sample."
[02:18] need to take a sample." So, here we have a sample of five women,
[02:20] So, here we have a sample of five women, that's n equals five.
[02:22] that's n equals five. And these are the heart rates for each
[02:24] And these are the heart rates for each of the five women.
[02:25] of the five women. And we can find what's called a sample
[02:27] And we can find what's called a sample mean, which is, in this case, 79.
[02:31] mean, which is, in this case, 79. Now, the symbol x bar is often used for
[02:34] Now, the symbol x bar is often used for the sample mean.
[02:36] the sample mean. But appreciate that if we took another
[02:38] But appreciate that if we took another sample, we might get five completely
[02:41] sample, we might get five completely different values. Now, these would be
[02:42] different values. Now, these would be beats per minute, just by the way. And
[02:44] beats per minute, just by the way. And of course, then we'd get a different
[02:46] of course, then we'd get a different sample mean.
[02:48] sample mean. So, it's not as if this sample mean is
[02:50] So, it's not as if this sample mean is the end of the story, right? And
[02:52] the end of the story, right? And realistically, what this is is an
[02:54] realistically, what this is is an estimate for the true average heart rate
[02:58] estimate for the true average heart rate for women. And when I say true, I'm
[03:00] for women. And when I say true, I'm talking about what we might call the
[03:02] talking about what we might call the population
[03:03] population mean, or the population average.
[03:06] mean, or the population average. So, we could use this 79 we got from our
[03:08] So, we could use this 79 we got from our sample mean, and hopefully construct a
[03:11] sample mean, and hopefully construct a kind of interval where we go, "All
[03:13] kind of interval where we go, "All right, we've got 79, but we know that
[03:16] right, we've got 79, but we know that it's just a random sample. Maybe the
[03:17] it's just a random sample. Maybe the next sample might be 77. Maybe the next
[03:20] next sample might be 77. Maybe the next sample might be 85. Who knows?
[03:24] sample might be 85. Who knows? But this does tell us something about
[03:26] But this does tell us something about the population mean, doesn't it? In that
[03:29] the population mean, doesn't it? In that we know the population mean's not going
[03:30] we know the population mean's not going to be something like 40, right? And we
[03:33] to be something like 40, right? And we also know it's not going to be something
[03:34] also know it's not going to be something like 120. Well, it's very unlikely to be
[03:37] like 120. Well, it's very unlikely to be those two numbers looking
[03:39] those two numbers looking at the sample we've been given. So,
[03:41] at the sample we've been given. So, we've got some kind of information about
[03:43] we've got some kind of information about the population mean.
[03:44] the population mean. But what we want to try to do is give us
[03:46] But what we want to try to do is give us what's called a confidence interval. So,
[03:48] what's called a confidence interval. So, we might be able to say something like
[03:50] we might be able to say something like this.
[03:51] this. We are 95% confident
[03:53] We are 95% confident that the population mean mu
[03:56] that the population mean mu lies between let's just say 67 and 91.
[04:00] lies between let's just say 67 and 91. Now, you'll notice that the sample mean
[04:02] Now, you'll notice that the sample mean lies right in the middle of this
[04:04] lies right in the middle of this interval.
[04:06] interval. And that actually tends to be the case
[04:08] And that actually tends to be the case for most confidence intervals we'll be
[04:10] for most confidence intervals we'll be creating.
[04:11] creating. Because realistically, there's no reason
[04:13] Because realistically, there's no reason to think that the population mean should
[04:15] to think that the population mean should be specifically higher or lower than
[04:18] be specifically higher or lower than this sample mean we've got.
[04:20] this sample mean we've got. So, it should be nice and balanced this
[04:22] So, it should be nice and balanced this confidence interval around the center of
[04:25] confidence interval around the center of the sample mean being 79.
[04:28] the sample mean being 79. So, you may well be asking now, why is
[04:31] So, you may well be asking now, why is this 67 and 91 specifically? How did we
[04:34] this 67 and 91 specifically? How did we calculate those two numbers? I get that
[04:36] calculate those two numbers? I get that 79 should be in the middle, but how wide
[04:39] 79 should be in the middle, but how wide should this confidence interval be? And
[04:41] should this confidence interval be? And why did we choose 95%
[04:44] why did we choose 95% confidence?
[04:46] confidence? Well, let's go and have a look at how
[04:48] Well, let's go and have a look at how confidence intervals are calculated.
[04:52] So, as I said before, we were looking at two different confidence intervals. One
[04:55] two different confidence intervals. One where we're doing a confidence interval
[04:57] where we're doing a confidence interval for the population mean,
[05:00] for the population mean, and another where we're doing it for a
[05:01] and another where we're doing it for a population proportion. Now, they're just
[05:03] population proportion. Now, they're just different types of data that's going to
[05:05] different types of data that's going to give us either a mean or a proportion.
[05:09] give us either a mean or a proportion. And for example, we saw before a
[05:12] And for example, we saw before a potential population mean when we were
[05:14] potential population mean when we were estimating the average resting heart
[05:17] estimating the average resting heart rate for women because that will be in
[05:18] rate for women because that will be in beats per minute. And a population
[05:21] beats per minute. And a population proportion might be something like this.
[05:24] proportion might be something like this. What proportion of women have high heart
[05:26] What proportion of women have high heart rates? And let's just say a high heart
[05:28] rates? And let's just say a high heart rate is at least 100 bpm.
[05:33] rate is at least 100 bpm. But you can see we actually have what's
[05:34] But you can see we actually have what's called binary data on this side. We've
[05:37] called binary data on this side. We've got just a collection of yeses and no's,
[05:40] got just a collection of yeses and no's, right? Either you do have a high heart
[05:42] right? Either you do have a high heart rate or you don't.
[05:43] rate or you don't. And on this side, on the mean side, we
[05:45] And on this side, on the mean side, we actually have numerical values for the
[05:47] actually have numerical values for the heart rates.
[05:49] heart rates. So, on the population mean side, we're
[05:50] So, on the population mean side, we're trying to estimate mu, which is the
[05:53] trying to estimate mu, which is the population mean, using x-bar, which is
[05:55] population mean, using x-bar, which is our sample mean.
[05:58] our sample mean. And on the proportion side, we want to
[05:59] And on the proportion side, we want to estimate pi. Now, that is the Greek
[06:01] estimate pi. Now, that is the Greek symbol we tend to use
[06:04] symbol we tend to use for population proportions.
[06:07] for population proportions. And p is going to be our sample
[06:09] And p is going to be our sample proportion.
[06:11] proportion. Be aware that you might also see the
[06:13] Be aware that you might also see the Greek letter theta used in either of
[06:15] Greek letter theta used in either of these two scenarios for a general
[06:18] these two scenarios for a general population parameter.
[06:21] population parameter. Okay, so what we're trying to aim to do
[06:22] Okay, so what we're trying to aim to do is use our sample mean, wherever that
[06:25] is use our sample mean, wherever that happens to be, and then construct for
[06:27] happens to be, and then construct for ourselves this interval for the
[06:29] ourselves this interval for the population mean. Similarly, we can use
[06:32] population mean. Similarly, we can use the sample proportion and construct this
[06:35] the sample proportion and construct this population proportion interval.
[06:38] population proportion interval. So, that's I've actually created some
[06:39] So, that's I've actually created some data for this, which you can, if you go
[06:41] data for this, which you can, if you go to zstatistics.com, you can download
[06:44] to zstatistics.com, you can download this, if you want to have a play around
[06:46] this, if you want to have a play around yourself, that is, but it's basically 50
[06:47] yourself, that is, but it's basically 50 women and their particular heart rate.
[06:49] women and their particular heart rate. So, instead of having five women this
[06:51] So, instead of having five women this time, I've gone with 50.
[06:56] So, what I'm going to do now is actually introduce the formula on each side here.
[07:00] introduce the formula on each side here. And it's something I tend not to do so
[07:02] And it's something I tend not to do so much on this channel, cuz I don't like
[07:04] much on this channel, cuz I don't like formulas for the sake of them, but here
[07:07] formulas for the sake of them, but here they're actually quite instructive as to
[07:08] they're actually quite instructive as to what's going on. So,
[07:11] what's going on. So, so let's first focus on the mean side of
[07:13] so let's first focus on the mean side of things. You can see we have x-bar plus
[07:17] things. You can see we have x-bar plus or minus something, right? And so,
[07:19] or minus something, right? And so, clearly we're going to construct this
[07:20] clearly we're going to construct this confidence interval such that it goes
[07:22] confidence interval such that it goes plus a little bit and minus a little bit
[07:24] plus a little bit and minus a little bit from the actual sample mean, whatever
[07:26] from the actual sample mean, whatever that happens to be.
[07:29] that happens to be. And in this case, we actually find the
[07:31] And in this case, we actually find the sample mean to be 75.9. That's the
[07:34] sample mean to be 75.9. That's the average of the 50 women in the sample.
[07:38] average of the 50 women in the sample. So, what's this t s and root n stuff?
[07:43] So, what's this t s and root n stuff? Well, I might start with the s.
[07:45] Well, I might start with the s. S is actually the sample standard
[07:48] S is actually the sample standard deviation. So, that is some indication
[07:50] deviation. So, that is some indication of the spread of the underlying data.
[07:54] of the spread of the underlying data. So, the greater the variation in the
[07:56] So, the greater the variation in the samples heart rates here, the greater
[07:59] samples heart rates here, the greater this number will be in the numerator.
[08:02] this number will be in the numerator. So, in other words, the greater the
[08:04] So, in other words, the greater the interval we will create will be.
[08:07] interval we will create will be. And that kind of makes sense. The more
[08:08] And that kind of makes sense. The more uncertainty we have in our sample, the
[08:11] uncertainty we have in our sample, the more uncertainty we will have in the
[08:14] more uncertainty we will have in the construction of our confidence interval
[08:16] construction of our confidence interval for the population mean, right?
[08:19] for the population mean, right? Now, the second thing we can see here is
[08:20] Now, the second thing we can see here is this divided by root n.
[08:24] this divided by root n. And so, quite simply, this tells us that
[08:26] And so, quite simply, this tells us that more observations we have in our sample,
[08:29] more observations we have in our sample, the smaller this interval is going to
[08:31] the smaller this interval is going to be, right? Cuz as the denominator
[08:33] be, right? Cuz as the denominator increases, this interval is going to
[08:35] increases, this interval is going to decrease. Now, you should find that
[08:37] decrease. Now, you should find that somewhat understandable because the more
[08:39] somewhat understandable because the more people we have in our sample, the more
[08:41] people we have in our sample, the more likely the sample mean will be close to
[08:45] likely the sample mean will be close to the true population mean,
[08:47] the true population mean, right?
[08:50] So, that's going to reduce our uncertainty.
[08:54] uncertainty. And that all kind of makes sense, but
[08:55] And that all kind of makes sense, but what is this t doing? Why do we have
[08:58] what is this t doing? Why do we have this t figure here?
[09:00] this t figure here? So, that's why we might want to consider
[09:02] So, that's why we might want to consider the actual shape of this distribution.
[09:05] the actual shape of this distribution. Think of it this way. We have a sample
[09:06] Think of it this way. We have a sample mean of 75.9. That's what we got from
[09:08] mean of 75.9. That's what we got from this sample. If you averaged out this
[09:10] this sample. If you averaged out this final column. And because there's 50
[09:12] final column. And because there's 50 observations here, we'd be likely to get
[09:15] observations here, we'd be likely to get a population mean, the true value of the
[09:18] a population mean, the true value of the population mean should be somewhere near
[09:20] population mean should be somewhere near 75.9.
[09:21] 75.9. The further we get away from 75, the
[09:23] The further we get away from 75, the less likely we're probably going to find
[09:26] less likely we're probably going to find our population mean. So, we might say
[09:28] our population mean. So, we might say this has a normal distribution.
[09:32] this has a normal distribution. Now, the unfortunate thing is that it's
[09:33] Now, the unfortunate thing is that it's not quite normal. It's actually what's
[09:34] not quite normal. It's actually what's called a t distribution. And I'm not
[09:37] called a t distribution. And I'm not going to get into the t-distribution
[09:38] going to get into the t-distribution here. You can check out my video on the
[09:41] here. You can check out my video on the t-distribution if you like.
[09:43] t-distribution if you like. But for the sake of this video, we'll
[09:44] But for the sake of this video, we'll just say that the t-distribution
[09:46] just say that the t-distribution describes this bell curve shape for our
[09:50] describes this bell curve shape for our possible values of mu.
[09:53] possible values of mu. So, what we need to do now is find this
[09:55] So, what we need to do now is find this particular point on the t-distribution
[09:58] particular point on the t-distribution that encloses this 95% region. Now,
[10:01] that encloses this 95% region. Now, we're going to use 95% just as a rule of
[10:03] we're going to use 95% just as a rule of thumb. It's a nice round number and it
[10:05] thumb. It's a nice round number and it gives us a good coverage for the
[10:07] gives us a good coverage for the potential values of mu. But don't be
[10:10] potential values of mu. But don't be confused. This is just a arbitrary
[10:13] confused. This is just a arbitrary value. You can find a 96% confidence
[10:15] value. You can find a 96% confidence interval if you like, a 98.3%
[10:18] interval if you like, a 98.3% confidence interval.
[10:19] confidence interval. But we use 95 often because it's just
[10:22] But we use 95 often because it's just nice and round. So, to find this value,
[10:24] nice and round. So, to find this value, we're going to need to use this
[10:26] we're going to need to use this t-distribution.
[10:27] t-distribution. And the correct Excel formula to use to
[10:30] And the correct Excel formula to use to find it would be this here. You can go
[10:33] find it would be this here. You can go equals t.inv.
[10:36] equals t.inv. This gives us the value on the x-axis
[10:38] This gives us the value on the x-axis here for a given probability.
[10:42] here for a given probability. And when I say probability, I mean the
[10:44] And when I say probability, I mean the amount of the distribution to the left
[10:47] amount of the distribution to the left of a given point.
[10:49] of a given point. So, it is a little bit confusing. But
[10:50] So, it is a little bit confusing. But for this point up here, just think about
[10:52] for this point up here, just think about it. If there's a 95%
[10:54] it. If there's a 95% region between these two points, there's
[10:56] region between these two points, there's 2.5% in each tail such that there's
[11:00] 2.5% in each tail such that there's 97.5%
[11:02] 97.5% below this value.
[11:04] below this value. So, yeah, a little bit tricky. But 0.975
[11:07] So, yeah, a little bit tricky. But 0.975 will get us this point.
[11:09] will get us this point. And then 49 is the number of degrees of
[11:12] And then 49 is the number of degrees of freedom, which is always n minus 1.
[11:15] freedom, which is always n minus 1. Again, I'll go into more details in the
[11:17] Again, I'll go into more details in the t-distribution video, which I'll link to
[11:20] t-distribution video, which I'll link to in the description of this video.
[11:23] in the description of this video. And that will provide for you the t
[11:25] And that will provide for you the t value, and you can multiply them by s on
[11:27] value, and you can multiply them by s on root n. And finally, we can get our two
[11:31] root n. And finally, we can get our two confidence limits. 72.1 is the lower
[11:34] confidence limits. 72.1 is the lower confidence limit. 79.7 is the upper
[11:37] confidence limit. 79.7 is the upper confidence limit.
[11:40] confidence limit. So, if we zoom over now to the
[11:42] So, if we zoom over now to the proportion side of things, it's actually
[11:45] proportion side of things, it's actually very much the same.
[11:47] very much the same. In this case, the proportion of women
[11:49] In this case, the proportion of women that have a high heart rate was 0.12
[11:53] that have a high heart rate was 0.12 because there was six out of the 50
[11:56] because there was six out of the 50 people in our sample that had a high
[11:58] people in our sample that had a high heart rate. Now, have a look at this.
[11:59] heart rate. Now, have a look at this. This is the sample proportion, 0.12,
[12:03] This is the sample proportion, 0.12, plus or minus something, just like the
[12:05] plus or minus something, just like the previous example.
[12:06] previous example. It's just slightly different. It's
[12:08] It's just slightly different. It's clearly going to have something to do
[12:09] clearly going to have something to do with P because it's now categorical
[12:12] with P because it's now categorical data, so P is our proportion.
[12:15] data, so P is our proportion. And you can see that again n is on the
[12:17] And you can see that again n is on the denominator. So, this actually forms
[12:19] denominator. So, this actually forms what's called the standard error when
[12:21] what's called the standard error when you have a binomial distribution. Again,
[12:25] you have a binomial distribution. Again, I've got a video on that, but for the
[12:27] I've got a video on that, but for the purpose of this video, we might just
[12:28] purpose of this video, we might just keep it simple and say this describes
[12:31] keep it simple and say this describes the uncertainty around our estimate.
[12:34] the uncertainty around our estimate. Now, here we have a nice little Z which
[12:36] Now, here we have a nice little Z which tells us it's going to be a normal
[12:38] tells us it's going to be a normal distribution,
[12:39] distribution, not a T distribution in this case, but a
[12:41] not a T distribution in this case, but a normal distribution.
[12:43] normal distribution. But, it's the same idea. We've got this
[12:44] But, it's the same idea. We've got this kind of bell-shaped curve to our
[12:47] kind of bell-shaped curve to our possible values for pi, for our
[12:50] possible values for pi, for our population proportion.
[12:53] population proportion. In other words, it's more likely for the
[12:54] In other words, it's more likely for the population proportion to be something
[12:57] population proportion to be something close to 0.12
[12:59] close to 0.12 than it is to be further away from 0.12.
[13:04] And no surprise, you can actually use Excel again to find this value of Z.
[13:09] Excel again to find this value of Z. You can write equals norm.s.inv,
[13:13] You can write equals norm.s.inv, and in the brackets, you're going to be
[13:15] and in the brackets, you're going to be putting 0.975.
[13:18] putting 0.975. Why 0.975? Well, for the same reason we
[13:22] Why 0.975? Well, for the same reason we did on the T distribution,
[13:24] did on the T distribution, we're after the point above which lies
[13:27] we're after the point above which lies 2.5% so below which lies 97.5%.
[13:32] 2.5% so below which lies 97.5%. So, it is a little bit confusing, but
[13:34] So, it is a little bit confusing, but using this in Excel, that's the way we
[13:36] using this in Excel, that's the way we can find this particular value, and that
[13:38] can find this particular value, and that happens to be 1.96.
[13:41] happens to be 1.96. So, then we can sub in all the values
[13:43] So, then we can sub in all the values that we have, 0.12 being P, N is 50, and
[13:47] that we have, 0.12 being P, N is 50, and when you sub all those into the formula,
[13:49] when you sub all those into the formula, you get 0.074
[13:51] you get 0.074 and 0.166.
[13:53] and 0.166. Feel free to confirm that for me.
[13:56] Feel free to confirm that for me. But, we now have a nice 95% confidence
[13:59] But, we now have a nice 95% confidence interval for P.
[14:02] interval for P. So, how do we interpret both of these?
[14:04] So, how do we interpret both of these? Well, on the left side here, we can say
[14:06] Well, on the left side here, we can say we are 95% confident that the average
[14:09] we are 95% confident that the average resting heart rate for women is between
[14:11] resting heart rate for women is between 72.1 and 79.7 bpm.
[14:15] 72.1 and 79.7 bpm. And on this side, we can say we're 95%
[14:17] And on this side, we can say we're 95% confident that the proportion of women
[14:19] confident that the proportion of women with high heart rates
[14:21] with high heart rates is between 0.074
[14:24] is between 0.074 and 0.166.
[14:28] So, let's have a look and see some examples of confidence intervals you
[14:32] examples of confidence intervals you might find in academic papers and the
[14:34] might find in academic papers and the like. This one is coronavirus-related,
[14:37] like. This one is coronavirus-related, and in fact, this paper came out just
[14:39] and in fact, this paper came out just last week. Disparities in coronavirus
[14:42] last week. Disparities in coronavirus reported incidents, knowledge, and
[14:44] reported incidents, knowledge, and behavior among US adults by Olson et al.
[14:48] behavior among US adults by Olson et al. And you might find
[14:50] And you might find in the results things that look a bit
[14:53] in the results things that look a bit like this. African-American respondents
[14:56] like this. African-American respondents were 3.5 percentage points
[14:59] were 3.5 percentage points more likely than white respondents to
[15:00] more likely than white respondents to report being infected with COVID. Now,
[15:03] report being infected with COVID. Now, after 3.5 percentage points, you can see
[15:05] after 3.5 percentage points, you can see we have a 95%
[15:07] we have a 95% confidence interval, 1.5 to 5.5
[15:10] confidence interval, 1.5 to 5.5 percentage points. So, that's often a
[15:12] percentage points. So, that's often a way that they will show
[15:14] way that they will show confidence intervals in text. And you
[15:16] confidence intervals in text. And you can see there's quite a few more of them
[15:18] can see there's quite a few more of them as you go down here.
[15:20] as you go down here. This is the same paper, and this is a
[15:22] This is the same paper, and this is a way that they've actually shown it using
[15:24] way that they've actually shown it using what's called a forest plot. So, you can
[15:26] what's called a forest plot. So, you can see that for example, this is the
[15:27] see that for example, this is the probability of having COVID-19.
[15:30] probability of having COVID-19. We've got white people being the
[15:32] We've got white people being the reference. This is from the USA. Now,
[15:35] reference. This is from the USA. Now, black people have a higher probability
[15:38] black people have a higher probability of having COVID-19. And you can see that
[15:41] of having COVID-19. And you can see that the estimate is this little
[15:43] the estimate is this little dot here, and this line, the whiskers on
[15:46] dot here, and this line, the whiskers on each side, provide the 95% confidence
[15:49] each side, provide the 95% confidence interval. And that tells you down the
[15:50] interval. And that tells you down the bottom that it in in that it is in fact
[15:53] bottom that it in in that it is in fact a 95%
[15:55] a 95% confidence interval. So, it's quite
[15:56] confidence interval. So, it's quite crucial here to look down and see which
[15:59] crucial here to look down and see which of these confidence intervals cross this
[16:01] of these confidence intervals cross this dotted line, and which of them are
[16:03] dotted line, and which of them are wholly on one side
[16:06] wholly on one side of the dotted line. So, here this tells
[16:07] of the dotted line. So, here this tells us there's a significant difference
[16:09] us there's a significant difference between black and white people in terms
[16:12] between black and white people in terms of their probability of having COVID-19.
[16:15] of their probability of having COVID-19. There's not a significant difference
[16:17] There's not a significant difference between white and Hispanic because you
[16:19] between white and Hispanic because you can see that confidence interval crosses
[16:21] can see that confidence interval crosses this line where the white people were
[16:23] this line where the white people were at. So, there's also a big difference
[16:25] at. So, there's also a big difference between females and males, and and
[16:27] between females and males, and and that's a statistically significant
[16:29] that's a statistically significant difference as well.
[16:30] difference as well. So, that's quite neat. Other examples
[16:32] So, that's quite neat. Other examples might be in graphical form, and for this
[16:34] might be in graphical form, and for this I'm actually giving you some statistical
[16:36] I'm actually giving you some statistical stuff that I've been involved in myself
[16:39] stuff that I've been involved in myself as a biostatistician here in New South
[16:41] as a biostatistician here in New South Wales.
[16:43] Wales. So, this first one comes care of
[16:45] So, this first one comes care of HealthStats New South Wales.
[16:47] HealthStats New South Wales. And you can see here we have the
[16:48] And you can see here we have the proportion of Aboriginal people and
[16:50] proportion of Aboriginal people and non-Aboriginal people that are
[16:52] non-Aboriginal people that are overweight, obese, or overweight or
[16:55] overweight, obese, or overweight or obese. So, we get a nice comparison
[16:57] obese. So, we get a nice comparison between Aboriginal and non-Aboriginal.
[17:00] between Aboriginal and non-Aboriginal. But, we also get these nice little
[17:02] But, we also get these nice little confidence interval bars here, or
[17:04] confidence interval bars here, or they're also sometimes called error
[17:06] they're also sometimes called error bars.
[17:07] bars. And they'll be 95% confidence intervals
[17:09] And they'll be 95% confidence intervals for each of them.
[17:11] for each of them. And quite telling, you can see that the
[17:13] And quite telling, you can see that the confidence intervals for Aboriginal
[17:14] confidence intervals for Aboriginal people are larger than the confidence
[17:17] people are larger than the confidence intervals for non-Aboriginal. But,
[17:19] intervals for non-Aboriginal. But, that's only because we have a smaller
[17:21] that's only because we have a smaller number of Aboriginal people in our
[17:23] number of Aboriginal people in our sample. So, remember how the number of
[17:25] sample. So, remember how the number of observations affects the confidence
[17:28] observations affects the confidence interval width? Well, in Australia,
[17:30] interval width? Well, in Australia, there's a lot more non-Aboriginal people
[17:32] there's a lot more non-Aboriginal people than there are Aboriginal.
[17:34] than there are Aboriginal. So, that's why these confidence
[17:35] So, that's why these confidence intervals are a lot smaller.
[17:39] And finally, here's another way of showing confidence intervals in a paper
[17:44] showing confidence intervals in a paper that I've put together some years ago
[17:46] that I've put together some years ago now. It's a bit old, but the funnel plot
[17:48] now. It's a bit old, but the funnel plot is a classic way of showing confidence
[17:50] is a classic way of showing confidence intervals. Here, here we have the number
[17:52] intervals. Here, here we have the number of hip fracture procedures done per
[17:54] of hip fracture procedures done per year. So, each of these dots are
[17:56] year. So, each of these dots are hospitals in New South Wales.
[17:58] hospitals in New South Wales. And on the Y axis here, we have the
[18:01] And on the Y axis here, we have the percentage of the procedures resulting
[18:03] percentage of the procedures resulting in death within 30 days. So, we've got
[18:06] in death within 30 days. So, we've got the average for New South Wales, 7.35%.
[18:09] the average for New South Wales, 7.35%. That's our mortality rate. And so, as
[18:11] That's our mortality rate. And so, as the number of hip fractures increases,
[18:14] the number of hip fractures increases, you can see that the confidence interval
[18:16] you can see that the confidence interval is actually going to decrease again
[18:18] is actually going to decrease again because of the increasing value of n.
[18:21] because of the increasing value of n. So, it's a nice way of of seeing which
[18:23] So, it's a nice way of of seeing which particular hospitals are outside the
[18:25] particular hospitals are outside the bounds of these confidence intervals.
[18:28] bounds of these confidence intervals. So, this hospital here is doing much
[18:29] So, this hospital here is doing much better for its number of hip fractures
[18:32] better for its number of hip fractures done per year
[18:34] done per year than we might expect.
[18:35] than we might expect. Anyway, there are some examples of
[18:37] Anyway, there are some examples of confidence intervals you might see
[18:40] confidence intervals you might see as I said, in the wild.
[18:43] as I said, in the wild. All right. So, let's move on now and
[18:44] All right. So, let's move on now and have a look at the sealed section for
[18:47] have a look at the sealed section for math nerds.
[18:49] math nerds. Yes, here we're going to have a a just a
[18:50] Yes, here we're going to have a a just a brief look at the difference between
[18:52] brief look at the difference between frequentist intervals and Bayesian
[18:54] frequentist intervals and Bayesian intervals.
[18:56] intervals. Now, if you want to go deep into the
[18:57] Now, if you want to go deep into the difference between frequentist and
[18:59] difference between frequentist and Bayesian statistics,
[19:01] Bayesian statistics, uh I've got a video that deals with this
[19:03] uh I've got a video that deals with this in depth.
[19:05] in depth. But, I didn't want to make this video
[19:06] But, I didn't want to make this video too long, so I'm just having a cursory
[19:09] too long, so I'm just having a cursory overview of the differences here.
[19:11] overview of the differences here. But, nonetheless, they are different.
[19:13] But, nonetheless, they are different. For frequentists,
[19:14] For frequentists, they will call these intervals
[19:16] they will call these intervals confidence intervals, and for Bayesians,
[19:18] confidence intervals, and for Bayesians, they're called credible intervals. But,
[19:20] they're called credible intervals. But, let's have a look and see how they
[19:21] let's have a look and see how they differ.
[19:22] differ. So, from a frequentist perspective,
[19:24] So, from a frequentist perspective, theta, which is our parameter that we're
[19:26] theta, which is our parameter that we're trying to estimate, we consider that to
[19:28] trying to estimate, we consider that to be fixed, whereas the sample is
[19:31] be fixed, whereas the sample is something which might be considered
[19:32] something which might be considered random. This is the way that people tend
[19:34] random. This is the way that people tend to talk about frequentist intervals, and
[19:37] to talk about frequentist intervals, and Bayesian intervals are kind of the
[19:38] Bayesian intervals are kind of the reverse, where they say that theta is
[19:40] reverse, where they say that theta is random. This is our parameter is
[19:42] random. This is our parameter is considered random, and the sample is
[19:43] considered random, and the sample is considered a fixed singular item.
[19:47] considered a fixed singular item. Now, that's just a simplification, and
[19:48] Now, that's just a simplification, and while I'm not going to get into really
[19:50] while I'm not going to get into really the weeds here, it's probably a good way
[19:52] the weeds here, it's probably a good way of looking at it for the purpose of this
[19:54] of looking at it for the purpose of this video. So,
[19:56] video. So, for example, when I say on the
[19:57] for example, when I say on the frequentist side that theta is fixed,
[20:00] frequentist side that theta is fixed, what I mean by that is that there's one
[20:02] what I mean by that is that there's one kind of godly value of theta,
[20:05] kind of godly value of theta, and you can see that this first red bar
[20:07] and you can see that this first red bar might be a 95% confidence interval we've
[20:09] might be a 95% confidence interval we've generated from a sample, and it crosses
[20:12] generated from a sample, and it crosses the true value
[20:14] the true value theta. Now, what frequentists would say
[20:16] theta. Now, what frequentists would say was would be that this sample is just a
[20:18] was would be that this sample is just a a random outcome that could have been
[20:21] a random outcome that could have been anywhere else. It could have been this
[20:22] anywhere else. It could have been this sample we took here, or maybe it's this
[20:24] sample we took here, or maybe it's this one, or maybe we could have taken this
[20:26] one, or maybe we could have taken this sample over here, and this one's
[20:28] sample over here, and this one's actually not including theta in its
[20:31] actually not including theta in its range. But, the idea here is that 95% of
[20:35] range. But, the idea here is that 95% of these intervals we'd create, if they're,
[20:37] these intervals we'd create, if they're, of course, 95% confidence intervals. 95
[20:41] of course, 95% confidence intervals. 95 out of 100 of these would contain theta,
[20:44] out of 100 of these would contain theta, and five out of 100 of those would not
[20:47] and five out of 100 of those would not contain theta, like this one here.
[20:49] contain theta, like this one here. So, this is the way we'd interpret a
[20:51] So, this is the way we'd interpret a confidence interval. You'd say 95% of
[20:54] confidence interval. You'd say 95% of similarly constructed intervals would
[20:57] similarly constructed intervals would contain theta.
[20:59] contain theta. Now, again, the key point was that theta
[21:01] Now, again, the key point was that theta is fixed and kind of godly. I like I
[21:03] is fixed and kind of godly. I like I like that term godly, cuz it means like
[21:06] like that term godly, cuz it means like it just is one particular value.
[21:08] it just is one particular value. Bayesians are a bit more flexible. They
[21:11] Bayesians are a bit more flexible. They will attribute to theta a probability
[21:14] will attribute to theta a probability distribution.
[21:16] distribution. And in fact, they do this before they
[21:17] And in fact, they do this before they even see the sample.
[21:20] even see the sample. It's something called a prior
[21:21] It's something called a prior distribution.
[21:23] distribution. So in this case, this is just a uniform
[21:25] So in this case, this is just a uniform prior in that they're saying that theta
[21:27] prior in that they're saying that theta could be any number along this
[21:29] could be any number along this particular number line of equal
[21:31] particular number line of equal probability between these two values.
[21:34] probability between these two values. Then what happens is you get an actual
[21:36] Then what happens is you get an actual sample mean, which might be somewhere
[21:38] sample mean, which might be somewhere here, and all of a sudden we can can
[21:40] here, and all of a sudden we can can construct what's called a posterior. So
[21:42] construct what's called a posterior. So this incorporates now information from
[21:44] this incorporates now information from our sample,
[21:46] our sample, and we construct again a probability
[21:49] and we construct again a probability distribution for theta. This time it's
[21:51] distribution for theta. This time it's called the posterior. So you can see
[21:53] called the posterior. So you can see here that theta is considered like a
[21:55] here that theta is considered like a random variable. It's given a
[21:57] random variable. It's given a probability distribution within itself.
[22:00] probability distribution within itself. Whereas the sample is only considered by
[22:02] Whereas the sample is only considered by itself. We don't have numerous
[22:04] itself. We don't have numerous theoretical samples here. We only have
[22:06] theoretical samples here. We only have one sample, and from that distribution
[22:08] one sample, and from that distribution we create for theta, we can construct a
[22:11] we create for theta, we can construct a 95% interval. So between these two
[22:14] 95% interval. So between these two points, you would have 95% of the data.
[22:17] points, you would have 95% of the data. And there we might say that there's a
[22:19] And there we might say that there's a 95% chance that the interval contains
[22:22] 95% chance that the interval contains the true population mean theta.
[22:26] Now it's quite interesting because in the intervals we've created so far in
[22:31] the intervals we've created so far in this video, and indeed in most of your
[22:33] this video, and indeed in most of your textbooks, they'll be frequentist
[22:35] textbooks, they'll be frequentist intervals, but they'll tend to provide
[22:38] intervals, but they'll tend to provide you with a Bayesian interpretation of
[22:40] you with a Bayesian interpretation of those intervals. You'll say, "There's a
[22:42] those intervals. You'll say, "There's a 95% chance that the interval contains
[22:45] 95% chance that the interval contains the true population mean theta." But in
[22:47] the true population mean theta." But in reality, this is the technically true
[22:50] reality, this is the technically true conclusion you can draw.
[22:53] conclusion you can draw. So there's a a bit of poetic license
[22:54] So there's a a bit of poetic license here in that we allow ourselves just
[22:56] here in that we allow ourselves just this nice interpretation for using a
[22:59] this nice interpretation for using a frequentist interval. When in reality,
[23:01] frequentist interval. When in reality, hardcore statisticians will be wagging
[23:03] hardcore statisticians will be wagging their fingers at us because
[23:05] their fingers at us because frequentist and Bayesian intervals,
[23:08] frequentist and Bayesian intervals, while they're often the same, there are
[23:09] while they're often the same, there are situations where they are not the same.
[23:12] situations where they are not the same. And I'll investigate that more in the
[23:14] And I'll investigate that more in the frequentist versus Bayesian statistics
[23:16] frequentist versus Bayesian statistics video, which I'll put a link for in the
[23:19] video, which I'll put a link for in the description.
[23:21] description. But that, my friends, is the end of
[23:23] But that, my friends, is the end of confidence intervals. Thanks so much for
[23:25] confidence intervals. Thanks so much for watching. Uh and if you want to watch
[23:27] watching. Uh and if you want to watch any of the others, you can check out the
[23:29] any of the others, you can check out the links below.
[23:31] links below. My name is Justin Zeltzer. If you've got
[23:32] My name is Justin Zeltzer. If you've got any comments, feedback, questions, feel
[23:36] any comments, feedback, questions, feel free to shoot me an email. You can
[23:38] free to shoot me an email. You can navigate to my address on the website
[23:40] navigate to my address on the website zstatistics.com.
[23:44] And keep an eye out on the YouTube channel cuz I've got some interesting
[23:46] channel cuz I've got some interesting things coming up in the next few months.
[23:49] things coming up in the next few months. Keep subscribed and hit the notification
[23:52] Keep subscribed and hit the notification bell to keep updated on that. But I'll
[23:54] bell to keep updated on that. But I'll see you next time.
