---
video_id: XLCWeSVzHUU
url: https://www.youtube.com/watch?v=XLCWeSVzHUU
title: Sampling from a Distribution, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 3:48
language: en
unit: L07
status: OK
---

[00:03] StatQuest
[00:06] StatQuest Hello and welcome to StatQuest.
[00:08] Hello and welcome to StatQuest. StatQuest is brought to you by the
[00:10] StatQuest is brought to you by the friendly folks in the genetics
[00:12] friendly folks in the genetics department in the University of North
[00:14] department in the University of North Carolina at Chapel Hill.
[00:16] Carolina at Chapel Hill. Today we're going to be talking about
[00:17] Today we're going to be talking about sampling a distribution or getting
[00:20] sampling a distribution or getting samples from a distribution.
[00:23] samples from a distribution. This is something that we do all the
[00:25] This is something that we do all the time in StatQuest, so I wanted to make a
[00:27] time in StatQuest, so I wanted to make a video that we could reference rather
[00:29] video that we could reference rather than covering the same material over and
[00:31] than covering the same material over and over and over again.
[00:33] over and over again. So let's get down to it.
[00:36] So let's get down to it. Here we have a histogram of height
[00:38] Here we have a histogram of height measurements. Each red dot represents a
[00:41] measurements. Each red dot represents a different person that we measured.
[00:44] different person that we measured. The tallest part of the histogram shows
[00:46] The tallest part of the histogram shows the region where measurements are most
[00:48] the region where measurements are most likely.
[00:49] likely. In this case, most of the people we
[00:52] In this case, most of the people we measured were between 5 ft 7 in and 6 ft
[00:55] measured were between 5 ft 7 in and 6 ft tall.
[00:57] tall. The low parts of the histogram show
[00:59] The low parts of the histogram show where measurements are less likely. In
[01:01] where measurements are less likely. In this case, we didn't measure many people
[01:04] this case, we didn't measure many people that were shorter than 4 and 1/2 ft or
[01:06] that were shorter than 4 and 1/2 ft or taller than 6 and 1/2 ft.
[01:10] taller than 6 and 1/2 ft. We can approximate the histogram with a
[01:12] We can approximate the histogram with a smooth curve.
[01:14] smooth curve. You guys already know all this from the
[01:16] You guys already know all this from the StatQuest on statistical distributions.
[01:20] StatQuest on statistical distributions. What we want to know today is what it
[01:23] What we want to know today is what it means to take a sample from a
[01:25] means to take a sample from a distribution.
[01:28] distribution. All that means is that we use a computer
[01:31] All that means is that we use a computer to pick a random number based on the
[01:33] to pick a random number based on the probabilities described by the histogram
[01:36] probabilities described by the histogram or the curve.
[01:38] or the curve. For example, if we wanted to take one
[01:41] For example, if we wanted to take one sample from this distribution, there's a
[01:43] sample from this distribution, there's a good chance the computer will pick a
[01:45] good chance the computer will pick a value near the middle where the
[01:47] value near the middle where the histogram and curve are tallest.
[01:51] histogram and curve are tallest. However, every now and then the computer
[01:54] However, every now and then the computer will return a value from the edges where
[01:57] will return a value from the edges where the histogram and curve are the
[01:59] the histogram and curve are the shortest.
[02:01] shortest. Why would you want to take a sample from
[02:04] Why would you want to take a sample from a distribution?
[02:05] a distribution? We do this to explore statistics.
[02:10] We do this to explore statistics. The computer can generate lots of
[02:12] The computer can generate lots of samples and we can plug them into
[02:14] samples and we can plug them into statistical tests to see what happens.
[02:18] statistical tests to see what happens. Since we know what the original
[02:20] Since we know what the original distribution is, we can compare our
[02:23] distribution is, we can compare our expectations of what will happen to
[02:26] expectations of what will happen to reality.
[02:28] reality. For example, I could take two samples
[02:31] For example, I could take two samples where n equals three
[02:33] where n equals three from a single distribution and do
[02:35] from a single distribution and do t-tests on the samples. In this case, n
[02:38] t-tests on the samples. In this case, n equals the number of measurements we
[02:40] equals the number of measurements we take within each sample.
[02:43] take within each sample. Since the distribution is the same, the
[02:45] Since the distribution is the same, the t-test should give me a large p-value.
[02:50] t-test should give me a large p-value. Doing lots of tests will give me a sense
[02:53] Doing lots of tests will give me a sense of how frequently the t-test
[02:55] of how frequently the t-test successfully gives me a large p-value.
[02:59] successfully gives me a large p-value. If I had two separate distributions, a
[03:02] If I had two separate distributions, a t-test is supposed to give me a small
[03:04] t-test is supposed to give me a small p-value.
[03:06] p-value. If I took lots of samples, I could do
[03:08] If I took lots of samples, I could do lots of t-tests and see how frequently
[03:11] lots of t-tests and see how frequently the t-test worked and gave me a small
[03:14] the t-test worked and gave me a small p-value.
[03:15] p-value. This would tell me if I needed to
[03:17] This would tell me if I needed to increase my sample size or not.
[03:22] increase my sample size or not. Taking samples from a distribution or
[03:24] Taking samples from a distribution or multiple distributions, i.e. getting a
[03:27] multiple distributions, i.e. getting a computer to generate a bunch of random
[03:30] computer to generate a bunch of random numbers that reflect the probabilities
[03:32] numbers that reflect the probabilities of a distribution,
[03:34] of a distribution, lets us determine what a statistical
[03:36] lets us determine what a statistical test is capable of doing without doing
[03:39] test is capable of doing without doing much real work.
[03:42] much real work. Hooray! We've made it to the end. Tune
[03:44] Hooray! We've made it to the end. Tune in next time for another exciting stat
[03:46] in next time for another exciting stat quest.
