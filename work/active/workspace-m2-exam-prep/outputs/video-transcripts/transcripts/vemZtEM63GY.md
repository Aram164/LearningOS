---
video_id: vemZtEM63GY
url: https://www.youtube.com/watch?v=vemZtEM63GY
title: p-values: What they are and how to interpret them
channel: StatQuest with Josh Starmer
duration: 11:21
language: en
unit: L10
status: OK
---

[00:00] Going to talk about P-values,
[00:03] Going to talk about P-values, yeah. StatQuest.
[00:08] Hello, I'm Josh Starmer, and welcome to StatQuest. Today, we're going to talk
[00:12] StatQuest. Today, we're going to talk about what P-values are and how to
[00:15] about what P-values are and how to interpret them.
[00:17] interpret them. Imagine I have two drugs, drug A
[00:21] Imagine I have two drugs, drug A and drug B.
[00:24] and drug B. And I want to know if drug A is
[00:26] And I want to know if drug A is different from drug B.
[00:29] different from drug B. So, I give one person drug A
[00:32] So, I give one person drug A and I give one other person drug B.
[00:36] and I give one other person drug B. The one person using drug A is cured.
[00:40] The one person using drug A is cured. Hooray!
[00:43] Hooray! The one person using drug B is not
[00:46] The one person using drug B is not cured.
[00:47] cured. Bummer.
[00:49] Bummer. Can we conclude that drug A is better
[00:51] Can we conclude that drug A is better than drug B?
[00:54] than drug B? Nope.
[00:55] Nope. Drug B may have failed for a lot of
[00:58] Drug B may have failed for a lot of different reasons.
[01:00] different reasons. Maybe this guy is taking a medication
[01:02] Maybe this guy is taking a medication that has a bad interaction with drug B.
[01:06] that has a bad interaction with drug B. Or maybe this guy has a rare allergy to
[01:08] Or maybe this guy has a rare allergy to drug B.
[01:10] drug B. Or maybe this guy didn't take drug B
[01:12] Or maybe this guy didn't take drug B properly and missed a dose.
[01:15] properly and missed a dose. Or maybe drug A doesn't actually work
[01:18] Or maybe drug A doesn't actually work and placebo effect deserves all of the
[01:21] and placebo effect deserves all of the credit.
[01:23] credit. There are a lot of weird, random things
[01:26] There are a lot of weird, random things that can happen when doing a test.
[01:29] that can happen when doing a test. And this means that we need to try each
[01:31] And this means that we need to try each drug on more than just one person each.
[01:35] drug on more than just one person each. So, we redo the experiment, but this
[01:37] So, we redo the experiment, but this time we give each drug to two different
[01:40] time we give each drug to two different people.
[01:42] people. This time, both people taking drug A are
[01:45] This time, both people taking drug A are cured.
[01:47] cured. Hooray!
[01:49] Hooray! And one person taking drug B is cured,
[01:52] And one person taking drug B is cured, and one person is not cured.
[01:55] and one person is not cured. Hooray and bummer.
[01:58] Hooray and bummer. Is drug A better?
[02:01] Is drug A better? Are both drugs the same?
[02:04] Are both drugs the same? We can't answer either of those
[02:06] We can't answer either of those questions because maybe something weird
[02:08] questions because maybe something weird happened to this guy that caused drug B
[02:10] happened to this guy that caused drug B to fail.
[02:12] to fail. Or maybe something weird happened to
[02:14] Or maybe something weird happened to this guy. Like maybe the drug was
[02:16] this guy. Like maybe the drug was mislabeled and he actually took drug A
[02:19] mislabeled and he actually took drug A and that's why he was cured.
[02:22] and that's why he was cured. So now we test the drugs on a lot of
[02:25] So now we test the drugs on a lot of different people.
[02:27] different people. And these are the results.
[02:30] And these are the results. Drug A cured a whole lot of people,
[02:32] Drug A cured a whole lot of people, 1,043.
[02:35] 1,043. Compared to the number of people it
[02:37] Compared to the number of people it didn't cure, three.
[02:40] didn't cure, three. In other words, 99.7%
[02:44] In other words, 99.7% of the 1,046 people using drug A were
[02:47] of the 1,046 people using drug A were cured.
[02:49] cured. In contrast, drug B only cured a few
[02:52] In contrast, drug B only cured a few people, two.
[02:55] people, two. Compared to the number of people it
[02:57] Compared to the number of people it didn't cure, 1,432.
[03:01] In other words, only 0.1%
[03:05] In other words, only 0.1% of the 1,434
[03:07] of the 1,434 people using drug B were cured.
[03:11] people using drug B were cured. If these were the results, then it would
[03:13] If these were the results, then it would be pretty obvious that drug A was better
[03:16] be pretty obvious that drug A was better than drug B.
[03:19] than drug B. In other words, it would seem
[03:21] In other words, it would seem unrealistic to suppose that these
[03:23] unrealistic to suppose that these results were just random chance and that
[03:26] results were just random chance and that there is no real difference between drug
[03:28] there is no real difference between drug A and drug B.
[03:31] A and drug B. It's possible that some of these people
[03:33] It's possible that some of these people were cured by placebo.
[03:36] were cured by placebo. And some of these people were not cured
[03:39] And some of these people were not cured because of some rare allergy.
[03:42] because of some rare allergy. But there are just too many people cured
[03:44] But there are just too many people cured by drug A and too few cured by drug B
[03:48] by drug A and too few cured by drug B for us to seriously think that these
[03:50] for us to seriously think that these results are just random and that drug A
[03:53] results are just random and that drug A is no better or worse than drug B.
[03:57] is no better or worse than drug B. In contrast, what if these were the
[04:00] In contrast, what if these were the results?
[04:02] results? Now, only 37% of the people that took
[04:05] Now, only 37% of the people that took drug A were cured
[04:08] drug A were cured compared to 31% that took drug B.
[04:13] compared to 31% that took drug B. So, drug A cured a larger percentage of
[04:15] So, drug A cured a larger percentage of people.
[04:17] people. But, given that no study is perfect, and
[04:20] But, given that no study is perfect, and there are always a few random things
[04:21] there are always a few random things that happen, how confident can we be
[04:24] that happen, how confident can we be that drug A is superior?
[04:27] that drug A is superior? That's where the P value comes in.
[04:31] That's where the P value comes in. P values are numbers between 0 and 1
[04:34] P values are numbers between 0 and 1 that, in this example, quantify how
[04:37] that, in this example, quantify how confident we should be that drug A is
[04:40] confident we should be that drug A is different from drug B.
[04:43] different from drug B. The closer a P value is to 0, the more
[04:46] The closer a P value is to 0, the more confidence we have that drug A and drug
[04:48] confidence we have that drug A and drug B are different.
[04:51] B are different. So, the question is, how small does a P
[04:54] So, the question is, how small does a P value have to be before we are
[04:56] value have to be before we are sufficiently confident that drug A is
[04:59] sufficiently confident that drug A is different from drug B?
[05:02] different from drug B? In other words, what threshold can we
[05:04] In other words, what threshold can we use to make a good decision?
[05:07] use to make a good decision? In practice, a commonly used threshold
[05:10] In practice, a commonly used threshold is 0.05.
[05:13] is 0.05. It means that if there is no difference
[05:15] It means that if there is no difference between drug A and drug B,
[05:18] between drug A and drug B, and if we did this exact same experiment
[05:20] and if we did this exact same experiment a bunch of times,
[05:22] a bunch of times, then only 5% of those experiments would
[05:24] then only 5% of those experiments would result in the wrong decision.
[05:28] result in the wrong decision. Yes, this is an awkward sentence.
[05:32] Yes, this is an awkward sentence. So, let's go through an example and work
[05:35] So, let's go through an example and work this out one step at a time.
[05:39] this out one step at a time. Imagine I gave the same drug, drug A, to
[05:42] Imagine I gave the same drug, drug A, to two different groups.
[05:45] two different groups. Now, any differences in the results are
[05:48] Now, any differences in the results are 100% attributable to weird random
[05:51] 100% attributable to weird random things, like a rare allergy in one
[05:54] things, like a rare allergy in one person, or a strong placebo effect in
[05:57] person, or a strong placebo effect in another.
[05:58] another. In this case, the P value would be 0.9,
[06:02] In this case, the P value would be 0.9, which is way larger than 0.05.
[06:07] which is way larger than 0.05. Thus, we would say that we failed to see
[06:09] Thus, we would say that we failed to see a difference between the two groups.
[06:13] a difference between the two groups. If we repeated this same experiment a
[06:15] If we repeated this same experiment a lot of times, most of the time we would
[06:18] lot of times, most of the time we would get similarly large P values.
[06:22] get similarly large P values. However, every once in a while, all of
[06:25] However, every once in a while, all of the people with rare allergies might end
[06:27] the people with rare allergies might end up in the group on the left.
[06:30] up in the group on the left. And all of the people with the strong
[06:32] And all of the people with the strong placebo reactions might end up in the
[06:34] placebo reactions might end up in the group on the right.
[06:37] group on the right. As a result, the P value for this
[06:39] As a result, the P value for this specific run of the experiment is 0.01,
[06:43] specific run of the experiment is 0.01, since the results are pretty different.
[06:47] since the results are pretty different. Thus, in this case, we would say that
[06:50] Thus, in this case, we would say that the two groups are different, even
[06:52] the two groups are different, even though they both took the same drug.
[06:55] though they both took the same drug. Oh, no! It's the dreaded terminology
[06:57] Oh, no! It's the dreaded terminology alert.
[06:59] alert. Getting a small P value when there is no
[07:01] Getting a small P value when there is no difference is called a false positive.
[07:06] difference is called a false positive. A 0.05
[07:08] A 0.05 threshold for P values means that 5% of
[07:11] threshold for P values means that 5% of the experiments, where the only
[07:13] the experiments, where the only differences come from weird random
[07:15] differences come from weird random things, will generate a P value smaller
[07:18] things, will generate a P value smaller than 0.05.
[07:22] In other words, if there's no difference
[07:25] In other words, if there's no difference between drug A and drug B, 5% of the
[07:28] between drug A and drug B, 5% of the time we do the experiment, we will get a
[07:31] time we do the experiment, we will get a P value less than 0.05,
[07:34] P value less than 0.05, aka a false positive.
[07:37] aka a false positive. Note, if it is extremely important that
[07:40] Note, if it is extremely important that we are correct when we say the drugs are
[07:42] we are correct when we say the drugs are different, then we can use a smaller
[07:45] different, then we can use a smaller threshold like 0.00001.
[07:51] Using a threshold of 0.00001
[07:56] means we would only get a false positive
[07:59] means we would only get a false positive once every 100,000 experiments.
[08:03] once every 100,000 experiments. Likewise, if it's not that important,
[08:06] Likewise, if it's not that important, for example, if we're trying to decide
[08:08] for example, if we're trying to decide if the ice cream truck will arrive on
[08:10] if the ice cream truck will arrive on time,
[08:11] time, then we can use a larger threshold like
[08:13] then we can use a larger threshold like 0.2.
[08:16] 0.2. Using a threshold of 0.2
[08:19] Using a threshold of 0.2 means we are willing to get a false
[08:20] means we are willing to get a false positive two times out of 10.
[08:24] positive two times out of 10. That said, the most common threshold is
[08:27] That said, the most common threshold is 0.05
[08:29] 0.05 because trying to reduce the number of
[08:31] because trying to reduce the number of false positives below 5% often costs
[08:35] false positives below 5% often costs more than it's worth.
[08:37] more than it's worth. So, if we calculate a P value for this
[08:40] So, if we calculate a P value for this experiment,
[08:42] experiment, and the P value is less than 0.05,
[08:46] and the P value is less than 0.05, then we will decide that drug A is
[08:48] then we will decide that drug A is different from drug B.
[08:51] different from drug B. That said, the P value is actually 0.24,
[08:56] That said, the P value is actually 0.24, so we are not confident that drug A is
[08:58] so we are not confident that drug A is different from drug B.
[09:01] different from drug B. Bam!
[09:03] Bam! Okay, before we're done, let me say two
[09:06] Okay, before we're done, let me say two more things about P values.
[09:09] more things about P values. Unfortunately, the first thing I want to
[09:11] Unfortunately, the first thing I want to say is just more terminology.
[09:14] say is just more terminology. In fancy statistical lingo, the idea of
[09:18] In fancy statistical lingo, the idea of trying to determine if these drugs are
[09:20] trying to determine if these drugs are the same or not is called hypothesis
[09:22] the same or not is called hypothesis testing.
[09:24] testing. The null hypothesis is that the drugs
[09:27] The null hypothesis is that the drugs are the same.
[09:29] are the same. And the P value helps us decide if we
[09:31] And the P value helps us decide if we should reject the null hypothesis or
[09:33] should reject the null hypothesis or not.
[09:35] not. Small bam.
[09:37] Small bam. Okay,
[09:39] Okay, now that we have that fancy terminology
[09:41] now that we have that fancy terminology out of the way, the second thing I want
[09:43] out of the way, the second thing I want to say is way more interesting.
[09:46] to say is way more interesting. While a small p-value helps us decide if
[09:49] While a small p-value helps us decide if drug A is different from drug B, it does
[09:52] drug A is different from drug B, it does not tell us how different they are.
[09:56] not tell us how different they are. In other words, you can have a small
[09:58] In other words, you can have a small p-value regardless of the size of
[10:01] p-value regardless of the size of difference between drug A and drug B.
[10:04] difference between drug A and drug B. The difference can be tiny or huge.
[10:08] The difference can be tiny or huge. For example, this experiment gives us a
[10:10] For example, this experiment gives us a relatively large p-value, 0.24,
[10:14] relatively large p-value, 0.24, even though there is a six-point
[10:16] even though there is a six-point difference between drug A and drug B.
[10:20] difference between drug A and drug B. In contrast, this experiment, which
[10:23] In contrast, this experiment, which involves a lot more people, gives us a
[10:26] involves a lot more people, gives us a smaller p-value, 0.04.
[10:30] smaller p-value, 0.04. Even though, given the new data, there
[10:33] Even though, given the new data, there is a one-point difference between drug A
[10:36] is a one-point difference between drug A and drug B.
[10:39] and drug B. In summary, a small p-value does not
[10:42] In summary, a small p-value does not imply that the effect size or difference
[10:45] imply that the effect size or difference between drug A and drug B is large.
[10:49] between drug A and drug B is large. Double bam.
[10:53] Double bam. Hooray!
[10:54] Hooray! We've made it to the end of another
[10:56] We've made it to the end of another exciting StatQuest. If you liked this
[10:59] exciting StatQuest. If you liked this StatQuest and want to see more, please
[11:01] StatQuest and want to see more, please subscribe. And if you want to support
[11:03] subscribe. And if you want to support StatQuest, consider contributing to my
[11:05] StatQuest, consider contributing to my Patreon campaign, becoming a channel
[11:08] Patreon campaign, becoming a channel member, buying one or two of my original
[11:11] member, buying one or two of my original songs or a t-shirt or a hoodie, or just
[11:13] songs or a t-shirt or a hoodie, or just donate. The links are in the description
[11:16] donate. The links are in the description below. All right, until next time, quest
[11:19] below. All right, until next time, quest on.
