---
video_id: bsZGt-caXO4
url: https://www.youtube.com/watch?v=bsZGt-caXO4
title: StatQuest:  One or Two Tailed P-Values
channel: StatQuest with Josh Starmer
duration: 7:05
language: en
unit: L10
status: OK
---

[00:01] StatQuest StatQuest
[00:05] StatQuest StatQuest
[00:10] StatQuest Hello and welcome to StatQuest.
[00:13] Hello and welcome to StatQuest. StatQuest is brought to you by the
[00:14] StatQuest is brought to you by the friendly folks in the genetics
[00:16] friendly folks in the genetics department at the University of North
[00:18] department at the University of North Carolina at Chapel Hill.
[00:20] Carolina at Chapel Hill. Today we're going to be talking about
[00:22] Today we're going to be talking about one versus two-tailed tests.
[00:25] one versus two-tailed tests. People frequently ask me which one they
[00:27] People frequently ask me which one they should use. So, I'm going to settle the
[00:29] should use. So, I'm going to settle the matter once and for all right here with
[00:31] matter once and for all right here with this StatQuest.
[00:33] this StatQuest. Imagine you've got a new cancer
[00:35] Imagine you've got a new cancer treatment.
[00:37] treatment. You hope that people do better with your
[00:39] You hope that people do better with your new treatment than the standard
[00:40] new treatment than the standard treatment.
[00:42] treatment. You do a small clinical trial on six
[00:44] You do a small clinical trial on six patients.
[00:46] patients. And here's your data.
[00:48] And here's your data. The red dots represent people that took
[00:51] The red dots represent people that took your new treatment
[00:53] your new treatment and the black dots represent people that
[00:56] and the black dots represent people that took the standard treatment.
[00:58] took the standard treatment. The values range from better
[01:00] The values range from better to worse.
[01:03] to worse. The data suggests that people who use
[01:05] The data suggests that people who use your new treatment do better than people
[01:07] your new treatment do better than people on the standard treatment.
[01:10] on the standard treatment. However, there is a little bit of
[01:12] However, there is a little bit of ambiguity in the results.
[01:15] ambiguity in the results. So, you run the stats.
[01:18] So, you run the stats. A one-tailed or one-sided test gives you
[01:21] A one-tailed or one-sided test gives you a P value of 0.03.
[01:25] a P value of 0.03. Awesome.
[01:26] Awesome. 0.03
[01:28] 0.03 is smaller than that pesky 0.05 cutoff
[01:32] is smaller than that pesky 0.05 cutoff that we usually use to determine
[01:34] that we usually use to determine significance.
[01:36] significance. A two-tailed or two-sided test gives you
[01:40] A two-tailed or two-sided test gives you a P value of 0.06.
[01:44] a P value of 0.06. Dag.
[01:46] Dag. Not so awesome.
[01:48] Not so awesome. Which P value should you use?
[01:52] Which P value should you use? The one-tailed P value tests the
[01:54] The one-tailed P value tests the hypothesis that your treatment is better
[01:57] hypothesis that your treatment is better than the standard treatment.
[02:00] than the standard treatment. Great. That's what we wanted, right?
[02:04] Great. That's what we wanted, right? It's certainly tempting, but let's not
[02:06] It's certainly tempting, but let's not jump to conclusions before learning
[02:08] jump to conclusions before learning about the two-tailed P value.
[02:12] about the two-tailed P value. The two-tailed P value test whether the
[02:15] The two-tailed P value test whether the new treatment is better, worse, or not
[02:18] new treatment is better, worse, or not significantly different.
[02:21] significantly different. The one-tailed P value is smaller
[02:23] The one-tailed P value is smaller because it doesn't distinguish between
[02:25] because it doesn't distinguish between worse and not significantly different.
[02:29] worse and not significantly different. Since we'd want to know if our new
[02:31] Since we'd want to know if our new treatment was worse than the standard
[02:33] treatment was worse than the standard treatment, we should use the two-tailed
[02:36] treatment, we should use the two-tailed P value.
[02:38] P value. But wait.
[02:39] But wait. Doesn't the data being skewed towards
[02:42] Doesn't the data being skewed towards the new method being better suggest we
[02:44] the new method being better suggest we don't need to test if it is worse?
[02:49] No. Good statistical practice means we need
[02:53] Good statistical practice means we need to decide what test and what P value we
[02:56] to decide what test and what P value we want to use before we do the experiment.
[03:00] want to use before we do the experiment. Otherwise, we're P hacking.
[03:03] Otherwise, we're P hacking. This increases the probability that we
[03:05] This increases the probability that we will report bogus results.
[03:09] will report bogus results. Let's see why this is.
[03:12] Let's see why this is. I started with a standard normal
[03:14] I started with a standard normal distribution.
[03:16] distribution. The X axis represents measurements from
[03:19] The X axis represents measurements from small to large.
[03:20] small to large. The Y axis represents the probability
[03:23] The Y axis represents the probability that I'll get certain measurements.
[03:26] that I'll get certain measurements. Most of the time, I should get
[03:28] Most of the time, I should get measurements in the middle.
[03:31] measurements in the middle. But every now and then, I'll get a
[03:32] But every now and then, I'll get a really small measurement or a really big
[03:35] really small measurement or a really big one.
[03:36] one. Then I took a sample from this
[03:38] Then I took a sample from this distribution.
[03:40] distribution. That means a computer picked three
[03:42] That means a computer picked three numbers that had a high likelihood of
[03:45] numbers that had a high likelihood of being from the center of the
[03:46] being from the center of the distribution, but every now and then,
[03:49] distribution, but every now and then, one of them might be really small or
[03:51] one of them might be really small or really big.
[03:53] really big. I then took another sample from the
[03:55] I then took another sample from the exact same distribution.
[03:58] exact same distribution. In most cases, a two-tailed t-test on
[04:02] In most cases, a two-tailed t-test on these two samples should give me a
[04:04] these two samples should give me a p-value greater than 0.05.
[04:08] p-value greater than 0.05. This is because most of the time the
[04:10] This is because most of the time the samples will overlap.
[04:13] samples will overlap. But every now and then, the samples will
[04:15] But every now and then, the samples will not overlap and the t-test will give me
[04:18] not overlap and the t-test will give me a p-value less than 0.05.
[04:22] This is called a false positive. It
[04:25] This is called a false positive. It happens 5% of the time.
[04:29] happens 5% of the time. I did 10,000 two-tailed t-tests on data
[04:32] I did 10,000 two-tailed t-tests on data like this.
[04:35] 5% of 10,000 equals 500. So, I was
[04:40] 5% of 10,000 equals 500. So, I was expecting 500 false positives.
[04:44] expecting 500 false positives. Here's a histogram of the p-values.
[04:48] Here's a histogram of the p-values. The blue line shows that each bin
[04:51] The blue line shows that each bin contains about 500 tests.
[04:54] contains about 500 tests. These are the false positives.
[04:56] These are the false positives. The tests with p-values less than 0.05.
[05:02] We pretty much got what we expected.
[05:05] We pretty much got what we expected. There were close to 500 false positives.
[05:08] There were close to 500 false positives. Then I changed things to mimic switching
[05:11] Then I changed things to mimic switching to a one-tailed test when things looked
[05:14] to a one-tailed test when things looked good.
[05:16] good. If sample number one had two or more
[05:19] If sample number one had two or more values that were less than all of the
[05:21] values that were less than all of the values in sample number two,
[05:24] values in sample number two, then I used a one-tailed t-test.
[05:28] then I used a one-tailed t-test. Since these two values are less than all
[05:30] Since these two values are less than all of the values in sample number two,
[05:33] of the values in sample number two, I used a one-tailed t-test on this data
[05:35] I used a one-tailed t-test on this data set.
[05:38] Here's a histogram of the new p-values.
[05:42] Here's a histogram of the new p-values. The blue line shows the expected number
[05:44] The blue line shows the expected number of p-values per bin.
[05:47] of p-values per bin. There are now close to 800 false
[05:50] There are now close to 800 false positives.
[05:52] positives. The chance of reporting a false positive
[05:54] The chance of reporting a false positive went from 5% to 8% even though we're
[05:58] went from 5% to 8% even though we're using 0.05 as the threshold for
[06:01] using 0.05 as the threshold for significance.
[06:02] significance. Thus, you can't wait till you see the
[06:05] Thus, you can't wait till you see the data to decide you want to use a
[06:07] data to decide you want to use a one-tailed P value.
[06:10] one-tailed P value. So, let's take a step back to before we
[06:12] So, let's take a step back to before we did the experiment.
[06:15] did the experiment. What do we want to learn from it?
[06:18] What do we want to learn from it? With a cancer treatment, it's obvious we
[06:20] With a cancer treatment, it's obvious we must learn if it improves things or
[06:23] must learn if it improves things or makes them worse.
[06:25] makes them worse. But really, it's the same for all data
[06:28] But really, it's the same for all data that has the option for a one or
[06:30] that has the option for a one or two-tailed P value.
[06:33] two-tailed P value. We always want to know both sides of the
[06:35] We always want to know both sides of the story, not just one.
[06:39] story, not just one. So, when you have a choice, always go
[06:42] So, when you have a choice, always go with a two-tailed P value. Note, not all
[06:45] with a two-tailed P value. Note, not all statistical tests have a choice. In that
[06:48] statistical tests have a choice. In that case, don't worry about it.
[06:51] case, don't worry about it. Hooray! We've made it to the end. We now
[06:54] Hooray! We've made it to the end. We now know that when we have a choice, we
[06:57] know that when we have a choice, we should always select a two-tailed test.
[07:01] should always select a two-tailed test. Tune in next time for another exciting
[07:03] Tune in next time for another exciting stat quest.
