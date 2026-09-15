---
video_id: Xz0x-8-cgaQ
url: https://www.youtube.com/watch?v=Xz0x-8-cgaQ
title: Bootstrapping Main Ideas!!!
channel: StatQuest with Josh Starmer
duration: 9:27
language: en
unit: L09
status: OK
---

[00:00] [music] bootstrapping
[00:04] bootstrapping Stack Quest
[00:07] Stack Quest Hello, I'm Josh Starmer and welcome to
[00:10] Hello, I'm Josh Starmer and welcome to Stack Quest. Today, we're going to talk
[00:12] Stack Quest. Today, we're going to talk about bootstrapping part one, main
[00:15] about bootstrapping part one, main ideas.
[00:17] ideas. Now, imagine we had a new drug to treat
[00:20] Now, imagine we had a new drug to treat an illness.
[00:21] an illness. And we gave that drug to eight different
[00:23] And we gave that drug to eight different people that had the illness.
[00:26] people that had the illness. For five of these people, the drug
[00:28] For five of these people, the drug appeared to help them feel better.
[00:31] appeared to help them feel better. But for three people, the drug appeared
[00:33] But for three people, the drug appeared to make them feel worse.
[00:36] to make them feel worse. If we calculate the mean of the response
[00:38] If we calculate the mean of the response to the drug, we get 0.5.
[00:41] to the drug, we get 0.5. 0.5 is not a huge improvement, but since
[00:45] 0.5 is not a huge improvement, but since most of the people, five of eight,
[00:47] most of the people, five of eight, improved, maybe this drug is better than
[00:50] improved, maybe this drug is better than using no drug at all.
[00:52] using no drug at all. However, maybe these five people all
[00:54] However, maybe these five people all felt better because they were healthier
[00:56] felt better because they were healthier to begin with.
[00:58] to begin with. And maybe these three people all felt
[01:00] And maybe these three people all felt worse because they had unhealthy
[01:02] worse because they had unhealthy lifestyles.
[01:04] lifestyles. So, it is possible that the reason we
[01:06] So, it is possible that the reason we got a mean value equal to 0.5 instead of
[01:09] got a mean value equal to 0.5 instead of zero is because of random things that we
[01:12] zero is because of random things that we can't control.
[01:14] can't control. Is there anything we can do to decide if
[01:17] Is there anything we can do to decide if the drug works or not?
[01:19] the drug works or not? Yes.
[01:20] Yes. One expensive and time-consuming option
[01:23] One expensive and time-consuming option would be to replicate the experiment a
[01:25] would be to replicate the experiment a bunch of times.
[01:27] bunch of times. If we repeat the experiment a bunch of
[01:29] If we repeat the experiment a bunch of times, then we can keep track of each
[01:32] times, then we can keep track of each mean value.
[01:33] mean value. And we will end up with a histogram of
[01:36] And we will end up with a histogram of mean values.
[01:38] mean values. Just by looking at this distribution, we
[01:40] Just by looking at this distribution, we can see that mean values close to zero,
[01:43] can see that mean values close to zero, which suggests that the drug does not do
[01:45] which suggests that the drug does not do anything, are relatively likely to
[01:47] anything, are relatively likely to occur.
[01:49] occur. And mean values far from zero,
[01:51] And mean values far from zero, indicating that the drug does something,
[01:54] indicating that the drug does something, are relatively rare.
[01:56] are relatively rare. However, as I said earlier, repeating
[01:59] However, as I said earlier, repeating the experiment a bunch of times is both
[02:01] the experiment a bunch of times is both expensive and time-consuming.
[02:04] expensive and time-consuming. Is there something else we can do that
[02:06] Is there something else we can do that is less expensive and time-consuming?
[02:09] is less expensive and time-consuming? Yes. Instead of replicating the
[02:12] Yes. Instead of replicating the experiment a bunch of times, we can use
[02:15] experiment a bunch of times, we can use bootstrapping.
[02:16] bootstrapping. Bam!
[02:18] Bam! So, let's use bootstrapping to get a
[02:20] So, let's use bootstrapping to get a better sense of which results are likely
[02:22] better sense of which results are likely and which are rare.
[02:25] and which are rare. First, let's create a new number line.
[02:28] First, let's create a new number line. Now, from the eight original
[02:30] Now, from the eight original measurements,
[02:31] measurements, choose one at random
[02:34] choose one at random and add that value to the new number
[02:36] and add that value to the new number line.
[02:37] line. Now, go back to the original eight
[02:39] Now, go back to the original eight measurements and choose another value at
[02:41] measurements and choose another value at random
[02:43] random and add it to the new number line.
[02:45] and add it to the new number line. Then, we repeat that process, randomly
[02:48] Then, we repeat that process, randomly selecting one of the eight original
[02:50] selecting one of the eight original values for the new number line a total
[02:52] values for the new number line a total of eight times.
[02:54] of eight times. Note, we can randomly select the same
[02:57] Note, we can randomly select the same value more than once.
[02:59] value more than once. Oh, no! It's the dreaded terminology
[03:01] Oh, no! It's the dreaded terminology alert.
[03:03] alert. Randomly selecting data and allowing for
[03:05] Randomly selecting data and allowing for duplicates is called sampling with
[03:07] duplicates is called sampling with replacement.
[03:09] replacement. Anyway, so far we've only selected six
[03:12] Anyway, so far we've only selected six measurements, so we need two more.
[03:15] measurements, so we need two more. Bip boop. Note, the reason we selected
[03:18] Bip boop. Note, the reason we selected eight measurements for the new number
[03:20] eight measurements for the new number line
[03:21] line is because the original data set that we
[03:23] is because the original data set that we are sampling from contains eight
[03:25] are sampling from contains eight measurements.
[03:27] measurements. If we had started with 10 measurements,
[03:29] If we had started with 10 measurements, then we would need to add 10
[03:31] then we would need to add 10 measurements to the new number line.
[03:34] measurements to the new number line. Anyway, this new data set that was
[03:36] Anyway, this new data set that was created using sampling with replacement
[03:39] created using sampling with replacement so that it had the same number of values
[03:41] so that it had the same number of values as the original data set
[03:43] as the original data set is called a bootstrapped data set.
[03:46] is called a bootstrapped data set. Okay, now that we have a new
[03:48] Okay, now that we have a new bootstrapped data set,
[03:50] bootstrapped data set, we calculate the mean.
[03:52] we calculate the mean. Note, because the bootstrap data set is
[03:55] Note, because the bootstrap data set is different from the original data set,
[03:58] different from the original data set, we get a different mean.
[04:00] we get a different mean. Now, let's add the mean of the bootstrap
[04:02] Now, let's add the mean of the bootstrap data set to what will soon be a
[04:04] data set to what will soon be a histogram of means.
[04:06] histogram of means. Now, we start over with a fresh number
[04:08] Now, we start over with a fresh number line
[04:10] line and randomly select from the eight
[04:11] and randomly select from the eight original values for the new number line,
[04:14] original values for the new number line, repeating a total of eight times and
[04:16] repeating a total of eight times and allowing duplications.
[04:18] allowing duplications. Then, we calculate the mean
[04:21] Then, we calculate the mean and add that to our histogram.
[04:23] and add that to our histogram. Note, this process of creating a
[04:26] Note, this process of creating a bootstrap data set,
[04:28] bootstrap data set, then calculating something, in this
[04:30] then calculating something, in this case, we calculate the mean,
[04:32] case, we calculate the mean, then keeping track of those
[04:34] then keeping track of those calculations,
[04:35] calculations, is called bootstrapping.
[04:38] is called bootstrapping. In other words,
[04:39] In other words, bootstrapping consists of four steps.
[04:43] bootstrapping consists of four steps. First, make a bootstrapped data set.
[04:46] First, make a bootstrapped data set. Second, calculate something. In this
[04:49] Second, calculate something. In this case, we calculated the mean.
[04:52] case, we calculated the mean. Three, keep track of that calculation.
[04:55] Three, keep track of that calculation. And four, repeat steps one through three
[04:58] And four, repeat steps one through three a bunch of times.
[05:00] a bunch of times. Note, in step two, we calculated the
[05:03] Note, in step two, we calculated the mean, but we could have just as easily
[05:05] mean, but we could have just as easily calculated
[05:07] calculated the median
[05:08] the median or the standard deviation
[05:10] or the standard deviation or any other statistic.
[05:13] or any other statistic. Later on, I'll say more about why this
[05:15] Later on, I'll say more about why this flexibility is awesome.
[05:18] flexibility is awesome. For now, I'll just say, "Bam!"
[05:22] For now, I'll just say, "Bam!" Okay, now that we know what
[05:24] Okay, now that we know what bootstrapping is, we just do it a bunch
[05:26] bootstrapping is, we just do it a bunch of times.
[05:28] of times. Usually, we use a computer to bootstrap
[05:30] Usually, we use a computer to bootstrap thousands of times.
[05:32] thousands of times. And after creating thousands of
[05:34] And after creating thousands of bootstrap samples, calculating their
[05:37] bootstrap samples, calculating their means, and adding them to the histogram,
[05:39] means, and adding them to the histogram, we end up with this.
[05:41] we end up with this. Because we sampled with replacement, the
[05:44] Because we sampled with replacement, the histogram ended up with a wide variety
[05:46] histogram ended up with a wide variety of mean values.
[05:48] of mean values. Because there are so many combinations,
[05:51] Because there are so many combinations, bootstrapping usually only creates a
[05:52] bootstrapping usually only creates a subset, like 10,000, to estimate the
[05:55] subset, like 10,000, to estimate the full distribution.
[05:58] full distribution. In this case, the histogram tells us how
[06:00] In this case, the histogram tells us how the mean might change if we redid the
[06:03] the mean might change if we redid the experiment a bunch of times.
[06:06] experiment a bunch of times. Just by looking at the histogram, we can
[06:08] Just by looking at the histogram, we can get a sense of what might happen if we
[06:10] get a sense of what might happen if we redid the experiment.
[06:12] redid the experiment. If we redid the experiment, there's a
[06:14] If we redid the experiment, there's a high likelihood we will get something
[06:16] high likelihood we will get something close to the original mean.
[06:19] close to the original mean. And getting something really far from
[06:20] And getting something really far from the original mean should be relatively
[06:22] the original mean should be relatively rare.
[06:24] rare. Because the histogram tells us how the
[06:26] Because the histogram tells us how the mean might change if we redid the
[06:28] mean might change if we redid the experiment a bunch of times,
[06:30] experiment a bunch of times, if we want to know the standard error of
[06:32] if we want to know the standard error of the mean value from the original data
[06:34] the mean value from the original data set,
[06:36] set, we only need to calculate the standard
[06:38] we only need to calculate the standard deviation of this distribution.
[06:41] deviation of this distribution. And a 95% confidence interval is just an
[06:44] And a 95% confidence interval is just an interval that covers 95% of the
[06:46] interval that covers 95% of the bootstrap means.
[06:49] bootstrap means. Double bam.
[06:51] Double bam. In this case, we see that the 95%
[06:54] In this case, we see that the 95% confidence interval covers zero, so we
[06:57] confidence interval covers zero, so we cannot reject the hypothesis that the
[06:59] cannot reject the hypothesis that the drug is not doing anything.
[07:02] drug is not doing anything. Note, what we just did with the
[07:04] Note, what we just did with the confidence interval was a type of
[07:06] confidence interval was a type of hypothesis testing. If you want to learn
[07:08] hypothesis testing. If you want to learn more about hypothesis testing, check out
[07:11] more about hypothesis testing, check out the quest.
[07:12] the quest. Also note, just so you know, there are
[07:15] Also note, just so you know, there are other fancier ways to use bootstrapping
[07:18] other fancier ways to use bootstrapping to calculate confidence intervals.
[07:21] to calculate confidence intervals. While these fancy methods can result in
[07:23] While these fancy methods can result in better confidence intervals, we'll save
[07:25] better confidence intervals, we'll save them for another day, since the purpose
[07:27] them for another day, since the purpose of this video is to explain the main
[07:29] of this video is to explain the main ideas behind bootstrapping.
[07:32] ideas behind bootstrapping. Small bam.
[07:35] Small bam. Now, so far we have used bootstrapping
[07:37] Now, so far we have used bootstrapping to calculate the standard error and a
[07:39] to calculate the standard error and a confidence interval for the mean.
[07:42] confidence interval for the mean. However, both the standard error and the
[07:45] However, both the standard error and the confidence interval can be calculated
[07:47] confidence interval can be calculated directly with a formula without having
[07:49] directly with a formula without having to create bootstrapped data sets.
[07:52] to create bootstrapped data sets. So, what is it that makes bootstrapping
[07:54] So, what is it that makes bootstrapping so awesome?
[07:57] so awesome? The awesome thing about bootstrapping is
[07:59] The awesome thing about bootstrapping is that we can apply it to any statistic to
[08:01] that we can apply it to any statistic to create a histogram of what might happen
[08:04] create a histogram of what might happen if we repeated the experiment a bunch of
[08:06] if we repeated the experiment a bunch of times.
[08:07] times. And we can use that histogram to
[08:09] And we can use that histogram to calculate stuff like standard errors and
[08:11] calculate stuff like standard errors and confidence intervals without having to
[08:13] confidence intervals without having to worry about whether or not there is a
[08:15] worry about whether or not there is a nice formula.
[08:17] nice formula. For example, if we started out by
[08:19] For example, if we started out by calculating the median of the original
[08:21] calculating the median of the original data,
[08:23] data, then we can use bootstrapping to create
[08:25] then we can use bootstrapping to create a distribution
[08:26] a distribution and use that distribution to create the
[08:29] and use that distribution to create the confidence interval.
[08:31] confidence interval. So, regardless of the statistic we
[08:33] So, regardless of the statistic we calculate, bootstrapping allows us to
[08:36] calculate, bootstrapping allows us to see it in the context of a distribution.
[08:39] see it in the context of a distribution. And we can use that distribution to help
[08:41] And we can use that distribution to help us interpret the initial results.
[08:44] us interpret the initial results. Triple bam!
[08:47] Triple bam! Now it's time for some shameless
[08:50] Now it's time for some shameless self-promotion.
[08:51] self-promotion. If you want to review statistics and
[08:53] If you want to review statistics and machine learning offline, check out the
[08:56] machine learning offline, check out the StatQuest Study Guides at statquest.org.
[08:59] StatQuest Study Guides at statquest.org. There's something for everyone.
[09:01] There's something for everyone. Hooray! We've made it to the end of
[09:04] Hooray! We've made it to the end of another exciting StatQuest. If you like
[09:06] another exciting StatQuest. If you like this StatQuest and want to see more,
[09:08] this StatQuest and want to see more, please subscribe. And if you want to
[09:10] please subscribe. And if you want to support StatQuest, consider contributing
[09:12] support StatQuest, consider contributing to my Patreon campaign, becoming a
[09:15] to my Patreon campaign, becoming a channel member, buying one or two of my
[09:17] channel member, buying one or two of my original songs or a t-shirt or a hoodie,
[09:20] original songs or a t-shirt or a hoodie, or just donate. The links are in the
[09:21] or just donate. The links are in the description below. All right, until next
[09:24] description below. All right, until next time. Quest on!
